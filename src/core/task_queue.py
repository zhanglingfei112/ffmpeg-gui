"""
任务队列与资源调度模块
管理并发任务数、线程限制、优先级队列。
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional
import inspect


class TaskStatus(Enum):
    WAITING = "等待中"
    RUNNING = "进行中"
    COMPLETED = "已完成"
    FAILED = "失败"
    CANCELLED = "已取消"


class Priority(Enum):
    HIGH = 3
    NORMAL = 2
    LOW = 1


@dataclass
class Task:
    """单个处理任务"""
    id: str
    name: str                          # 显示名称
    func: Callable                     # 实际要执行的函数
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: Priority = Priority.NORMAL
    status: TaskStatus = TaskStatus.WAITING
    progress: float = 0.0              # 0-100
    thread_count: int = 0              # FFmpeg 线程数（0=不限制）
    user_progress_callback: Optional[Callable] = None  # 用户传入的进度回调
    error: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None

    @property
    def duration(self) -> float:
        """任务已耗时（秒）"""
        if self.started_at:
            end = self.finished_at or time.time()
            return end - self.started_at
        return 0.0

    @property
    def duration_str(self) -> str:
        d = self.duration
        if d < 60:
            return f"{d:.0f}秒"
        return f"{d // 60:.0f}分{d % 60:.0f}秒"


class TaskQueue:
    """
    任务队列，支持：
    - 优先级排序
    - 最大并发数控制
    - 线程数限制
    - 取消/重试
    """

    def __init__(self, max_concurrent: int = 1, default_threads: int = 2):
        self._lock = threading.Lock()
        self._max_concurrent = max(1, max_concurrent)
        self._default_threads = max(1, min(default_threads, 4))  # 上限4线程，避免过载
        self._queue: list[Task] = []
        self._running: list[Task] = []
        self._completed: list[Task] = []
        self._task_id_counter = 0
        self._on_status_change = None  # Callable[[Task], None]

    # ---- 配置 ----

    @property
    def max_concurrent(self) -> int:
        return self._max_concurrent

    @max_concurrent.setter
    def max_concurrent(self, value: int):
        self._max_concurrent = max(1, value)

    @property
    def default_threads(self) -> int:
        return self._default_threads

    @default_threads.setter
    def default_threads(self, value: int):
        self._default_threads = max(1, value)

    def set_on_status_change(self, callback: Callable[[Task], None]):
        """状态变更回调"""
        self._on_status_change = callback

    # ---- 任务管理 ----

    def add_task(self, name: str, func: Callable, *args,
                 priority: Priority = Priority.NORMAL, **kwargs) -> str:
        """添加任务到队列，返回任务 ID"""
        with self._lock:
            self._task_id_counter += 1
            task_id = f"task_{self._task_id_counter:04d}"

            # 提取内部参数，不从 kwargs 传给用户函数
            user_progress = kwargs.pop("progress_callback", None)
            task_threads = kwargs.pop("thread_count", self._default_threads)
            kwargs.pop("log_callback", None)

            task = Task(
                id=task_id,
                name=name,
                func=func,
                args=args,
                kwargs=kwargs,
                priority=priority,
                thread_count=task_threads,
                user_progress_callback=user_progress,
            )
            self._queue.append(task)
            self._notify(task)
        # 在锁外派发，避免 _notify 回调死锁
        self._try_dispatch()
        return task_id

    def cancel_task(self, task_id: str) -> bool:
        """取消等待中的任务"""
        task_to_cancel = None
        with self._lock:
            for task in self._queue:
                if task.id == task_id and task.status == TaskStatus.WAITING:
                    task.status = TaskStatus.CANCELLED
                    self._queue.remove(task)
                    self._completed.append(task)
                    task_to_cancel = task
                    break
        if task_to_cancel:
            self._notify(task_to_cancel)
            return True
        return False

    def cancel_all(self):
        """取消所有等待中的任务"""
        cancelled = []
        with self._lock:
            for task in self._queue[:]:
                if task.status == TaskStatus.WAITING:
                    task.status = TaskStatus.CANCELLED
                    self._queue.remove(task)
                    self._completed.append(task)
                    cancelled.append(task)
        for task in cancelled:
            self._notify(task)
        return cancelled

    def clear_completed(self):
        """清空已完成的任务列表"""
        with self._lock:
            self._completed.clear()

    def get_task(self, task_id: str) -> Optional[Task]:
        """按 ID 查找任务"""
        with self._lock:
            for task in self._queue:
                if task.id == task_id:
                    return task
            for task in self._running:
                if task.id == task_id:
                    return task
            for task in self._completed:
                if task.id == task_id:
                    return task
        return None

    # ---- 队列状态 ----

    @property
    def waiting_count(self) -> int:
        with self._lock:
            return len(self._queue)

    @property
    def running_count(self) -> int:
        with self._lock:
            return len(self._running)

    @property
    def completed_count(self) -> int:
        with self._lock:
            return len(self._completed)

    @property
    def is_busy(self) -> bool:
        """是否有任务正在运行或等待"""
        with self._lock:
            return len(self._running) > 0 or len(self._queue) > 0

    def get_all_tasks(self) -> list[Task]:
        """获取所有任务（排队中 + 运行中 + 已完成）"""
        with self._lock:
            return list(self._queue + self._running + self._completed)

    def get_active_tasks(self) -> list[Task]:
        """获取活跃任务（排队中 + 运行中）"""
        with self._lock:
            return list(self._queue + self._running)

    # ---- 内部 ----

    def _try_dispatch(self):
        """尝试派发排队中的任务"""
        task = None
        with self._lock:
            if len(self._running) < self._max_concurrent and self._queue:
                # 按优先级排序
                self._queue.sort(key=lambda t: t.priority.value, reverse=True)
                task = self._queue.pop(0)
                self._running.append(task)
                task.status = TaskStatus.RUNNING
                task.started_at = time.time()
        if task:
            self._notify(task)
            # 在线程中执行，不阻塞 UI
            t = threading.Thread(target=self._execute_task, args=(task,), daemon=True)
            t.start()

    def _execute_task(self, task: Task):
        """实际执行任务（同步，会阻塞调用线程）"""
        try:
            # 构建传给函数的参数（只传函数接受的参数）
            try:
                sig = inspect.signature(task.func)
            except (ValueError, TypeError):
                sig = inspect.Signature()
            call_kwargs = dict(task.kwargs)

            # 内部参数：只在函数签名接受时才传递
            internal_params = {
                "thread_count": task.thread_count,
                "progress_callback": None,  # 下面包装
                "log_callback": None,
            }

            # 包装 progress_callback 以自动更新 task.progress
            def progress_wrapper(pct):
                task.progress = pct
                self._notify(task)
                # 如果用户传了回调也调用
                if task.user_progress_callback:
                    task.user_progress_callback(pct)

            internal_params["progress_callback"] = progress_wrapper

            # 只传递函数签名的参数
            for param_name, param_value in internal_params.items():
                if param_name in sig.parameters or param_name in call_kwargs:
                    call_kwargs[param_name] = param_value

            result = task.func(*task.args, **call_kwargs)
            with self._lock:
                task.status = TaskStatus.COMPLETED
                task.progress = 100.0
                task.finished_at = time.time()
                self._running.remove(task)
                self._completed.append(task)
            self._notify(task)
        except Exception as e:
            with self._lock:
                task.status = TaskStatus.FAILED
                task.error = str(e)
                task.finished_at = time.time()
                try:
                    self._running.remove(task)
                except ValueError:
                    pass
                self._completed.append(task)
            self._notify(task)

        # 继续派发下一个任务
        self._try_dispatch()

    def _notify(self, task: Task):
        """通知状态变更"""
        if self._on_status_change:
            try:
                self._on_status_change(task)
            except Exception:
                pass


def format_duration(seconds: float) -> str:
    """格式化时长"""
    if seconds < 1:
        return f"{seconds * 1000:.0f} 毫秒"
    if seconds < 60:
        return f"{seconds:.1f} 秒"
    m, s = divmod(int(seconds), 60)
    if m < 60:
        return f"{m} 分 {s} 秒"
    h, m = divmod(m, 60)
    return f"{h} 时 {m} 分 {s} 秒"
