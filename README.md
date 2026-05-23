# 待办清单 (Todo List)

轻量化桌面待办清单应用。Python + CustomTkinter 构建，启动快、界面简洁、支持边缘自动隐藏。

## 技术栈

- **Python 3.10+**
- **CustomTkinter** — 现代化 Tkinter 主题
- **pynput** — 全局快捷键监听

## 构建与启动

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动应用

```bash
python main.py
```

> 推荐使用 `pythonw main.py`（Windows）以避免控制台窗口。

## 功能概览

| 功能 | 说明 |
|---|---|
| 优先级排序 | 5 级优先级（危急→琐碎），自动降序排列 |
| 边缘隐藏 | 拖至屏幕边缘自动滑出，鼠标靠近弹出 |
| 全局快捷键 | 默认 `Ctrl+T` 快速添加，支持自定义组合键 |
| 导入/导出 | JSON 格式，支持替换或合并 |
| 数据持久化 | 自动保存至 `todos.json` |

## 运行测试

```bash
python -m pytest tests -v
```

## 项目结构

```
├── main.py            # 入口
├── app.py             # 主窗口 UI 与业务逻辑
├── models.py          # TodoItem 数据模型 / Priority 枚举
├── storage.py         # JSON 持久化与导入/导出
├── edge.py            # 屏幕边缘自动隐藏/弹出管理
├── hotkey.py          # 全局快捷键管理
├── requirements.txt
├── tests/             # 自动化测试 (pytest)
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_storage.py
│   ├── test_hotkey.py
│   └── test_sorting.py
└── docs/
    └── project-doc.md # 详细项目文档
```

## 许可证

MIT
