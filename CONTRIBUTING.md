# 贡献指南

感谢你愿意对这个项目做出贡献！

## 🐛 报告 Bug

请使用 [Bug Report 模板](.github/ISSUE_TEMPLATE/bug_report.md) 提交 Issue，尽可能详细地描述问题和复现步骤。

## 💡 功能建议

欢迎新想法！请使用 [Feature Request 模板](.github/ISSUE_TEMPLATE/feature_request.md) 提交 Issue，描述清楚使用场景和期望效果。

## 🔧 Pull Request

1. Fork 本仓库
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 提交改动：`git commit -m "feat: add xxx"`
4. 推送分支：`git push origin feature/your-feature`
5. 打开 Pull Request（请使用提供的 PR 模板）

### 开发环境

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -r requirements.txt

# 运行测试
cd src && python -m pytest ../tests -v
```

### 代码风格

- 遵循 PEP 8
- 类型标注优先（Python 类型注解）
- 核心功能需附带单元测试
- 提交信息遵循 [Conventional Commits](https://www.conventionalcommits.org/)

## 📄 许可证

提交代码即表示你同意你的贡献将以 MIT 许可证授权。
