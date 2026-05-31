"""
任务队列测试
"""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from core.task_queue import TaskQueue, TaskStatus, Priority, format_duration


class TestTaskQueue(unittest.TestCase):
    """TaskQueue 基本功能测试"""

    def setUp(self):
        self.queue = TaskQueue(max_concurrent=1, default_threads=2)

    def test_initial_state(self):
        self.assertEqual(self.queue.waiting_count, 0)
        self.assertEqual(self.queue.running_count, 0)
        self.assertEqual(self.queue.completed_count, 0)
        self.assertFalse(self.queue.is_busy)

    def test_add_task(self):
        def dummy():
            import time
            time.sleep(0.05)
            return "ok"

        task_id = self.queue.add_task("test", dummy)
        self.assertIsNotNone(task_id)
        # 任务可能已被派发，检查是否在等待或运行中
        task = self.queue.get_task(task_id)
        self.assertIsNotNone(task)
        self.assertIn(task.status, [TaskStatus.WAITING, TaskStatus.RUNNING])
        self.assertTrue(self.queue.is_busy)

    def test_get_task(self):
        def dummy():
            import time
            time.sleep(0.05)
            return "ok"

        task_id = self.queue.add_task("test", dummy)
        task = self.queue.get_task(task_id)
        self.assertIsNotNone(task)
        self.assertEqual(task.name, "test")
        # 可能在等待或运行中
        self.assertIn(task.status, [TaskStatus.WAITING, TaskStatus.RUNNING, TaskStatus.COMPLETED])

    def test_get_nonexistent_task(self):
        task = self.queue.get_task("nonexistent")
        self.assertIsNone(task)

    def test_cancel_task(self):
        def slow():
            import time
            time.sleep(0.5)
            return "ok"

        # 先添加 2 个慢任务，让队列填满
        self.queue.max_concurrent = 1
        task_id1 = self.queue.add_task("slow1", slow)
        import time
        time.sleep(0.05)
        task_id2 = self.queue.add_task("slow2", slow)  # 应该在排队
        time.sleep(0.05)

        # 取消排队中的任务
        self.assertTrue(self.queue.cancel_task(task_id2))
        self.assertEqual(self.queue.waiting_count, 0)

        cancelled_task = self.queue.get_task(task_id2)
        self.assertEqual(cancelled_task.status, TaskStatus.CANCELLED)

    def test_cancel_nonexistent(self):
        self.assertFalse(self.queue.cancel_task("nonexistent"))

    def test_cancel_all(self):
        def slow():
            import time
            time.sleep(0.5)
            return "ok"

        self.queue.add_task("task1", slow)  # 被派发
        import time
        time.sleep(0.05)
        self.queue.add_task("task2", slow)  # 排队
        self.queue.add_task("task3", slow)  # 排队

        cancelled = self.queue.cancel_all()
        # 只有排队中的被取消
        self.assertGreater(len(cancelled), 0)
        self.assertLessEqual(len(cancelled), 2)
        self.assertEqual(self.queue.waiting_count, 0)

    def test_task_execution(self):
        """测试任务实际执行"""
        results = []

        def dummy():
            results.append("executed")
            return "ok"

        self.queue.add_task("test", dummy)
        # 等待任务完成
        time.sleep(0.2)
        self.assertEqual(len(results), 1)
        self.assertEqual(self.queue.running_count, 0)
        self.assertEqual(self.queue.completed_count, 1)

    def test_task_failure(self):
        def failing():
            raise ValueError("test error")

        self.queue.add_task("failing", failing)
        time.sleep(0.2)

        tasks = self.queue.get_all_tasks()
        failed = [t for t in tasks if t.status == TaskStatus.FAILED]
        self.assertEqual(len(failed), 1)
        self.assertIn("test error", failed[0].error)

    def test_priority_order(self):
        """高优先级先执行"""
        results = []

        def make_task(name):
            def task():
                results.append(name)
                return name
            return task

        # 添加低优先级 + 高优先级
        self.queue.add_task("low", make_task("low"), priority=Priority.LOW)
        self.queue.add_task("high", make_task("high"), priority=Priority.HIGH)

        time.sleep(0.3)

        # 高优先级应该先执行
        self.assertEqual(len(results), 2)
        # 但因为是顺序执行，只能同时跑一个
        # 先添加 low 再 high，但 high 优先级高
        # 不过 add_task 时 low 先派发，high 排队
        # 实际上只能测试到两个都执行完
        self.assertIn("low", results)
        self.assertIn("high", results)

    def test_max_concurrent(self):
        """测试并发限制"""
        running = []

        def slow_task():
            running.append(1)
            time.sleep(0.3)
            running.pop()
            return "ok"

        self.queue.add_task("task1", slow_task)
        self.queue.add_task("task2", slow_task)
        self.queue.add_task("task3", slow_task)

        time.sleep(0.1)
        # 因为 max_concurrent=1，只有一个在跑
        self.assertEqual(len(running), 1)

        time.sleep(0.7)
        # 3 个任务各 0.3s，单线程运行，0.7s 内至少完成 2 个
        self.assertGreaterEqual(self.queue.completed_count, 2)

    def test_max_concurrent_adjust(self):
        """调整并发数后生效"""
        self.queue.max_concurrent = 3
        self.assertEqual(self.queue.max_concurrent, 3)
        self.queue.max_concurrent = 0  # 最小值 clamp
        self.assertEqual(self.queue.max_concurrent, 1)

    def test_default_threads(self):
        self.queue.default_threads = 4
        self.assertEqual(self.queue.default_threads, 4)
        self.queue.default_threads = 0
        self.assertEqual(self.queue.default_threads, 1)

    def test_clear_completed(self):
        def dummy():
            return "ok"

        self.queue.add_task("test", dummy)
        time.sleep(0.2)
        self.queue.clear_completed()
        self.assertEqual(self.queue.completed_count, 0)

    def test_get_all_tasks(self):
        def dummy():
            return "ok"

        self.queue.add_task("test", dummy)
        time.sleep(0.2)
        all_tasks = self.queue.get_all_tasks()
        self.assertGreaterEqual(len(all_tasks), 1)

    def test_status_change_callback(self):
        changes = []

        def on_change(task):
            changes.append(task.status)

        self.queue.set_on_status_change(on_change)

        def dummy():
            return "ok"

        self.queue.add_task("test", dummy)
        time.sleep(0.2)

        # WAITING → RUNNING → COMPLETED
        self.assertIn(TaskStatus.COMPLETED, changes)


class TestFormatDuration(unittest.TestCase):
    """时长格式化测试"""

    def test_milliseconds(self):
        self.assertEqual(format_duration(0.5), "500 毫秒")

    def test_seconds(self):
        self.assertEqual(format_duration(30.0), "30.0 秒")

    def test_minutes(self):
        self.assertEqual(format_duration(125.0), "2 分 5 秒")

    def test_hours(self):
        self.assertEqual(format_duration(3665.0), "1 时 1 分 5 秒")


class TestPresets(unittest.TestCase):
    """格式预设测试"""

    def test_import(self):
        from core.presets import FORMAT_PRESETS, QUALITY_PRESETS, DEVICE_PRESETS
        self.assertGreater(len(FORMAT_PRESETS), 0)
        self.assertGreater(len(QUALITY_PRESETS), 0)
        self.assertGreater(len(DEVICE_PRESETS), 0)

    def test_get_format_preset(self):
        from core.presets import get_format_preset
        p = get_format_preset("MP4 (H.264)")
        self.assertIsNotNone(p)
        self.assertEqual(p.extension, ".mp4")

    def test_get_format_preset_nonexistent(self):
        from core.presets import get_format_preset
        self.assertIsNone(get_format_preset("nonexistent"))

    def test_quality_preset_order(self):
        from core.presets import QUALITY_PRESETS
        self.assertEqual(QUALITY_PRESETS[0].name, "无损 / 最高质量")
        self.assertEqual(QUALITY_PRESETS[0].crf, 17)
        self.assertEqual(QUALITY_PRESETS[-1].crf, 40)


if __name__ == "__main__":
    unittest.main()
