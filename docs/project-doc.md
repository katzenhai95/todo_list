# 待办清单 — 项目文档

---

## 一、功能库

| 编号 | 功能名称 | 功能描述 | 验收方式 |
|------|----------|----------|----------|
| F-001 | 添加待办事项 | 在界面底部输入文本并选择优先级，点击"添加"或按回车键，将新条目加入列表 | 输入文字 → 选择优先级 → 点击添加/回车 → 列表中新增一条目，且按优先级排列 |
| F-002 | 快速添加（快捷键） | 按下全局快捷键（默认 `Ctrl+T`），弹出快速添加窗口，输入文本和优先级后回车即添加 | 在任意应用前台按下 `Ctrl+T` → 弹出快速添加窗口 → 输入内容回车 → 主窗口列表新增条目 |
| F-003 | 优先级排序 | 列表按优先级降序排列（危急 > 高 > 中 > 低 > 琐碎），已完成条目自动沉底 | 添加不同优先级条目 → 观察列表顺序是否严格按优先级降序 + 已完成在末尾 |
| F-004 | 标记完成 | 点击条目左侧复选框，条目文字变为灰色并添加删除线，自动移至列表末尾 | 勾选复选框 → 文字变灰加删除线 → 条目移至底部 |
| F-005 | 删除条目 | 点击条目的 "✕" 按钮，条目从列表移除 | 点击删除按钮 → 条目消失，列表重新排序，文件保存 |
| F-006 | 数据持久化 | 所有条目自动保存至 `todos.json`，每次增删改后即时写入。下次启动自动加载 | 添加条目 → 关闭应用 → 重新启动 → 条目仍在 |
| F-007 | 导出到文件 | 点击"导出"按钮，选择保存路径，将当前所有条目以 JSON 格式导出 | 点击导出 → 选择路径 → 确认文件生成且内容为合法 JSON |
| F-008 | 从文件导入 | 点击"导入"按钮，选择 JSON 文件，可选择替换当前列表或合并 | 点击导入 → 选择文件 → 选择替换/合并 → 列表更新 |
| F-009 | 屏幕边缘自动隐藏 | 将窗口拖至屏幕左/右/上/下边缘 → 鼠标离开窗口后，窗口自动滑出屏幕（留 3px 把手） | 拖窗口到屏幕左边缘 → 鼠标移开 → 0.4 秒后窗口滑出 → 仅剩 3px 边缘可见 |
| F-010 | 边缘弹出恢复 | 当窗口处于隐藏状态时，鼠标移到对应屏幕边缘的把手位置 → 窗口自动滑回原位 | 窗口隐藏后 → 鼠标移向屏幕边缘把手 → 窗口滑出完整显示 |
| F-011 | 快捷键自定义 | 在设置中点击"录制新快捷键"，按下组合键（必须包含至少一个修饰键），保存后生效 | 设置 → 录制 → 按下 `Ctrl+Shift+N` → 保存 → 按 `Ctrl+Shift+N` 弹出快速添加 |
| F-012 | 快捷键持久化 | 自定义快捷键保存至 `hotkey_config.json`，下次启动自动加载 | 自定义快捷键 → 关闭应用 → 重启 → 快捷键保持自定义值 |

---

## 二、项目架构

### 2.1 模块依赖图

```
main.py
  └── app.py (TodoApp)
        ├── models.py    ← TodoItem, Priority
        ├── storage.py   ← TodoStorage
        ├── edge.py      ← EdgeManager
        └── hotkey.py    ← HotkeyManager
```

### 2.2 模块职责

| 模块 | 职责 | 依赖 |
|------|------|------|
| `main.py` | 入口，实例化并启动 TodoApp | `app.py` |
| `app.py` | 主窗口 UI 布局、条目增删改、导入/导出触发、设置弹窗、快速添加弹窗 | 全部 |
| `models.py` | `TodoItem` 数据类、`Priority` 枚举（含标签/颜色映射） | 无 |
| `storage.py` | JSON 序列化/反序列化，文件读写，导入/导出 | `models.py` |
| `edge.py` | 窗口边缘检测、动画滑出/滑入、鼠标位置轮询 | 无（依赖 `tkinter` + `ctypes`） |
| `hotkey.py` | 全局快捷键注册/监听、快捷键配置持久化 | `pynput` |

### 2.3 数据流

```
用户操作 → app.py (UI 事件处理)
              ├── 增删改 → models.TodoItem (内存) → storage.TodoStorage.save() → todos.json
              ├── 导入   → storage.TodoStorage.import_from() → models.TodoItem[] → 列表刷新
              ├── 导出   → models.TodoItem[] → storage.TodoStorage.export_to() → 用户指定文件
              └── 快捷键 → hotkey.HotkeyManager (pynput 线程) → app.quick_add() → QuickAddPopup
```

---

## 三、项目详细实现方式

以下按功能点 (F-001 ~ F-012) 逐一说明实现细节，标注涉及的关键模块和方法。

---

### 3.1 F-001 添加待办事项

| 层次 | 位置 | 实现要点 |
|------|------|----------|
| 数据模型 | `models.py` — `TodoItem` | `@dataclass` 定义，字段：`text`、`priority`(Priority 枚举)、`completed`(bool)、`item_id`(UUID 前 8 位)、`created_at`(ISO 时间戳)。`to_dict()`/`from_dict()` 支持 JSON 序列化。 |
| 优先级枚举 | `models.py` — `Priority(IntEnum)` | 继承 `IntEnum`，值域 1–5（高值=高优先级）。提供 `label`（中文标签："危急"/"高"/"中"/"低"/"琐碎"）和 `color`（六位十六进制色值）。 |
| 界面添加 | `app.py` — `TodoApp._add_item()` | 从底部输入栏获取文本和优先级 → 构造 `TodoItem` 实例 → 追加到 `_items` 列表 → 调用 `_sort_items()` → `_rebuild_list()` 刷新 UI → `_save_data()` 持久化。回车键绑定 `<Return>` 事件，行为与点击"添加"一致。 |
| 空文本拒绝 | `app.py` — `_add_item()` | `text.strip()` 为空时直接 `return`，不创建条目也不写盘。 |
| 条目 UI | `app.py` — `TodoItemWidget` | 继承 `CTkFrame`，深色背景+圆角。布局从左到右：优先级色条(6px 宽，颜色取自 `Priority.color`) → 优先级中文标签 → 复选框 → 条目文本 → 删除按钮"✕"。 |

---

### 3.2 F-002 快速添加（快捷键触发）

| 层次 | 位置 | 实现要点 |
|------|------|----------|
| 全局监听 | `hotkey.py` — `HotkeyManager` | 封装 `pynput.keyboard.Listener`，后台线程持续监听。维护 `_pressed` 集合追踪当前按下的键，当 `_pressed == 期望组合` 时触发回调。 |
| 线程调度 | `app.py` — `TodoApp.quick_add()` | `HotkeyManager` 的回调在 pynput 线程中执行；通过 `self.after(0, _show)` 将实际 UI 操作安全调度到 tkinter 主线程。 |
| 弹窗 UI | `app.py` — `QuickAddPopup` | 继承 `CTkToplevel`，360×160 居中显示，`-topmost` 置顶。包含优先级下拉菜单、文本输入框（自动聚焦）、"添加"按钮。回车触发添加，Esc 关闭弹窗。 |
| 添加回调 | `app.py` — `TodoApp._on_quick_add()` | 弹窗关闭时通过回调将文本和优先级传回主窗口，调用 `_add_item()` 完成添加。 |

---

### 3.3 F-003 优先级排序

| 层次 | 位置 | 实现要点 |
|------|------|----------|
| 排序键 | `app.py` — `TodoApp._sort_items()` | `items.sort(key=lambda i: (i.completed, -int(i.priority), i.created_at))` — 三级排序：(1) 未完成在前 → (2) 优先级值降序（高在前）→ (3) 创建时间升序（先创建在前）。 |
| 触发时机 | `app.py` | 每次 `_add_item()`、`_delete_item()`、`_import()` 完成后均调用 `_sort_items()`，保证列表始终有序。 |
| UI 刷新 | `app.py` — `_rebuild_list()` | 销毁列表区全部 `TodoItemWidget`，按 `_items` 当前顺序重新创建并 `pack()`，确保显示与数据一致。 |

---

### 3.4 F-004 标记完成

| 层次 | 位置 | 实现要点 |
|------|------|----------|
| 复选框 | `app.py` — `TodoItemWidget._toggle()` | `CTkCheckBox` 绑定 `_toggle` 回调，设置 `item.completed = self._check_var.get()`。随后调用 `_update_style()` 更新视觉样式。 |
| 视觉反馈 | `app.py` — `TodoItemWidget._update_style()` | 已完成：文本颜色变灰 + `overstrike=True`（删除线）。未完成：恢复默认颜色和字体。 |
| 排序联动 | `app.py` — `TodoItemWidget._on_toggle` | 切换完成后触发排序回调。由于 `_sort_items()` 按 `(completed, -priority, created_at)` 排序，已完成条目自动移至列表末尾。 |
| 数据同步 | `app.py` — `_save_data()` | 切换状态后立即写盘，先遍历 `_item_widgets` 将 widget 的最新 `_check_var` 值同步回 `item.completed`，再调用 `TodoStorage.save()`。 |

---

### 3.5 F-005 删除条目

| 层次 | 位置 | 实现要点 |
|------|------|----------|
| 删除按钮 | `app.py` — `TodoItemWidget._delete()` | "✕" 按钮绑定删除回调，传递自身 widget 引用。 |
| 删除逻辑 | `app.py` — `TodoApp._delete_item()` | 通过列表推导式 `[i for i in self._items if i.item_id != item_id]` 过滤掉指定条目 → 从 `_item_widgets` 字典中移除 → `widget.destroy()` 销毁 UI → `_save_data()` 持久化。 |
| 容错 | 同上 | 删除不存在的 ID 时列表长度和内容不变，无副作用。 |

---

### 3.6 F-006 数据持久化

| 层次 | 位置 | 实现要点 |
|------|------|----------|
| 存储后端 | `storage.py` — `TodoStorage` | 默认路径为脚本同目录的 `todos.json`。`save()` 使用 `json.dump(ensure_ascii=False, indent=2)` 保证中文可读和格式化缩进。`load()` 将 JSON 数组逐项通过 `TodoItem.from_dict()` 还原。 |
| 容错处理 | `storage.py` — `load()` | 文件不存在 → 返回 `[]`；JSON 解析失败 (JSONDecodeError/KeyError/TypeError) → 返回 `[]`。确保首次启动或数据损坏时不崩溃。 |
| 写入时机 | `app.py` | 每次增/删/改/导入操作完成后即时调用 `_save_data()`；关闭窗口时 `_on_close()` 再次调用。先遍历 widget 同步状态再写盘，避免数据丢失。 |
| 加载时机 | `app.py` — `TodoApp.__init__()` | 构造函数末尾调用 `_load_data()`，从磁盘恢复上次会话的数据。 |

---

### 3.7 F-007 导出到文件

| 层次 | 位置 | 实现要点 |
|------|------|----------|
| 文件选择 | `app.py` — `TodoApp._export()` | `tkinter.filedialog.asksaveasfilename` 弹出系统保存对话框，默认扩展名 `.json`，过滤器限定 JSON 文件和所有文件。 |
| 导出逻辑 | `storage.py` — `TodoStorage.export_to()` | 将 `items` 列表转为字典列表，写入用户指定路径。与 `save()` 使用相同的 JSON 格式，可被 `import_from()` 直接读取。 |
| 格式 | JSON 数组 | `[{"id": "...", "text": "...", "priority": 1-5, "completed": bool, "created_at": "ISO..."}, ...]` |

---

### 3.8 F-008 从文件导入

| 层次 | 位置 | 实现要点 |
|------|------|----------|
| 文件选择 | `app.py` — `TodoApp._import()` | `tkinter.filedialog.askopenfilename` 弹出系统打开对话框，限 JSON 文件。 |
| 导入模式 | `app.py` — `_import()` | `messagebox.askyesnocancel` 三选一弹窗：是=替换 (`_items = imported`)，否=合并 (`_items.extend(imported)`)，取消=放弃。选择后调用 `_sort_items()` + `_rebuild_list()` + `_save_data()`。 |
| 导入逻辑 | `storage.py` — `TodoStorage.import_from()` | 文件不存在抛出 `FileNotFoundError`；JSON 格式错误由 `json.load` 抛出 `JSONDecodeError`，均由上层 `_import()` 的 `try/except` 捕获并弹出错误提示。 |

---

### 3.9 F-009 屏幕边缘自动隐藏

| 层次 | 位置 | 实现要点 |
|------|------|----------|
| 轮询机制 | `edge.py` — `EdgeManager._poll()` | 通过 `window.after(150ms, self._poll)` 实现非阻塞轮询，每次 `_tick()` 获取窗口坐标和鼠标位置。 |
| 边缘检测 | `edge.py` — `_detect_edge()` | 窗口坐标距屏幕边缘 ≤15px 判定为"停靠"：`wx ≤ 15` → LEFT，`wx+ww ≥ screen_w-15` → RIGHT，`wy ≤ 15` → TOP，`wy+wh ≥ screen_h-15` → BOTTOM。 |
| 隐藏时机 | `edge.py` — `_tick()` / `_start_hide()` | 条件：窗口已停靠 + 鼠标在窗口内 + 随后鼠标离开 → 启动 400ms 延迟定时器 → 到期后未取消则进入 `_start_hide()`。 |
| 动画 | `edge.py` — `_animate_slide()` | 8 帧，每帧 10ms（共 80ms），线性插值 (`target - start) / steps`）逐帧移动窗口位置。动画期间 `_animating=True` 阻止轮询干扰。 |
| 隐藏状态 | `edge.py` | LEFT 隐藏：`wx = -(ww - 3)`；RIGHT 隐藏：`wx = screen_w - 3`；TOP 隐藏：`wy = -(wh - 3)`；BOTTOM 隐藏：`wy = screen_h - 3`。保留 3px 作为"把手"。 |
| 鼠标获取 | `edge.py` — `_mouse_position()` | 通过 `ctypes.windll.user32.GetCursorPos` (Windows API) 获取全局鼠标坐标，不依赖窗口事件。 |

---

### 3.10 F-010 边缘弹出恢复

| 层次 | 位置 | 实现要点 |
|------|------|----------|
| 隐藏态轮询 | `edge.py` — `_poll_hidden()` | 当 `_hidden=True` 时，每次轮询检查鼠标是否接近把手区域（把手宽度 + 5px 容差）。 |
| 弹出触发 | `edge.py` — `_start_show()` | 鼠标进入把手区域 → 调用 `_animate_slide()` 以 `_visible_x`/`_visible_y`（隐藏前保存的位置）为终点执行滑入动画。 |
| 状态恢复 | `edge.py` | 滑入完成时 `_hidden=False`，回到正常轮询流程。 |

---

### 3.11 F-011 快捷键自定义

| 层次 | 位置 | 实现要点 |
|------|------|----------|
| 设置入口 | `app.py` — `TodoApp._open_settings()` | 工具栏"设置"按钮 → 实例化 `SettingsDialog`。 |
| 录制 UI | `app.py` — `SettingsDialog` | 380×280 弹窗。点击"录制"后通过 `<KeyPress>`/`<KeyRelease>` 事件捕获按键。修饰键 (Ctrl/Alt/Shift/Win) 通过 `keysym` 映射表归一化；普通键取 `keysym.lower()`。 |
| 录制校验 | `SettingsDialog._finish_recording()` | 必须包含 ≥1 个修饰键 + 1 个普通键，否则显示红色提示不完成录制。 |
| 保存生效 | `SettingsDialog._save()` | 调用 `HotkeyManager.set_hotkey(modifiers, key)`，内部更新 `_hotkey` 并写入 `hotkey_config.json` → 通知主窗口重启监听器 (`_restart_hotkey()`)。 |

---

### 3.12 F-012 快捷键持久化

| 层次 | 位置 | 实现要点 |
|------|------|----------|
| 配置格式 | `hotkey.py` — `Hotkey.to_dict()` / `from_dict()` | `{"modifiers": ["alt", "ctrl"], "key": "n"}` — modifiers 按字母排序保证可复现。`display` 属性生成 `"CTRL+ALT+N"` 用于 UI 展示。 |
| 加载时机 | `hotkey.py` — `HotkeyManager.__init__()` | 构造函数检查 `hotkey_config.json` 是否存在且 JSON 合法，是则加载，否则退回默认值 `Ctrl+T`。 |
| 写入时机 | `hotkey.py` — `set_hotkey()` | 每次自定义快捷键时立即写入 `hotkey_config.json`。 |
| 跨会话恢复 | `hotkey.py` — `_load_config()` | 两个独立 `HotkeyManager` 实例读取同一配置文件能得到相同结果。 |

---

## 四、测试用例表

测试用例按功能点 (F-001 ~ F-012) 组织，分为**自动化测试**（`pytest` 一键运行，结果自动判定）和**人工验证**（需用户交互观察，用例中注明判定标准）。

### 4.1 自动化测试（pytest）

运行方式：

```bash
cd F:\Projects\todo_list
python -m pytest tests -v
```

| 用例编号 | 对应功能 | 测试点 | 所在文件 | 验收标准（自动判定） |
|----------|----------|--------|----------|----------------------|
| TC-F001-01 | F-001 添加待办事项 | 创建 TodoItem 实例，验证默认字段 | `tests/test_models.py::TestTodoItem` | `text` 正确、`priority` 默认 MEDIUM、`completed` 为 False、`item_id` 为 8 位字符串 |
| TC-F001-02 | F-001 添加待办事项 | 空文本/空白字符串拒绝添加 | `tests/test_sorting.py::TestEmptyTextRejection` | `""` 和 `"   "` 判定为无效，`is_valid_text()` 返回 False |
| TC-F001-03 | F-001 添加待办事项 | 条目追加到列表 | `tests/test_sorting.py::TestItemListOperations` | `append` 后列表长度 +1，内容匹配 |
| TC-F002-01 | F-002 快速添加快捷键 | Hotkey 默认值验证 | `tests/test_hotkey.py::TestHotkeyDataclass::test_default_hotkey` | 默认修饰键 `{"ctrl"}`、键 `"t"` |
| TC-F003-01 | F-003 优先级排序 | 优先级降序排列 | `tests/test_sorting.py::TestSorting::test_sort_priority_descending` | 乱序输入 → 输出优先级序列 `[5,4,3,2,1]` |
| TC-F003-02 | F-003 优先级排序 | 已完成条目沉底 | `tests/test_sorting.py::TestSorting::test_completed_items_sink_to_bottom` | 所有未完成条目排在已完成条目之前 |
| TC-F003-03 | F-003 优先级排序 | 已完成条目内部也按优先级排序 | `tests/test_sorting.py::TestSorting::test_completed_items_sorted_by_priority_too` | 已完成条目组内优先级降序 |
| TC-F003-04 | F-003 优先级排序 | 排序不丢失条目 | `tests/test_sorting.py::TestSorting::test_sort_preserves_item_count` | 排序前后列表长度不变 |
| TC-F004-01 | F-004 标记完成 | 切换 `completed` 状态 | `tests/test_models.py::TestTodoItem::test_toggle_completed` | `completed` 从 False → True 可切换 |
| TC-F005-01 | F-005 删除条目 | 按 `item_id` 删除条目 | `tests/test_sorting.py::TestItemListOperations::test_delete_item_by_id` | 指定 ID 条目被移除，其他保留 |
| TC-F005-02 | F-005 删除条目 | 删除不存在的 ID 无影响 | `tests/test_sorting.py::TestItemListOperations::test_delete_nonexistent_does_nothing` | 列表长度和内容不变 |
| TC-F006-01 | F-006 数据持久化 | 保存后重新加载，数据完整 | `tests/test_storage.py::TestStorageSaveLoad::test_save_and_load_round_trip` | 加载的条目数量、文本、优先级、完成状态与保存前一致 |
| TC-F006-02 | F-006 数据持久化 | 首次启动（无存储文件） | `tests/test_storage.py::TestStorageSaveLoad::test_load_empty_when_file_missing` | `load()` 返回空列表，不抛异常 |
| TC-F006-03 | F-006 数据持久化 | 损坏的 JSON 文件 | `tests/test_storage.py::TestStorageSaveLoad::test_load_handles_corrupt_json` | `load()` 返回空列表，不崩溃 |
| TC-F006-04 | F-006 数据持久化 | 保存操作创建文件 | `tests/test_storage.py::TestStorageSaveLoad::test_save_creates_file` | `save()` 后文件存在于磁盘 |
| TC-F006-05 | F-006 数据持久化 | 重复保存覆盖而非追加 | `tests/test_storage.py::TestStorageSaveLoad::test_save_overwrites` | 第二次 `save()` 后加载仅得到最新数据 |
| TC-F007-01 | F-007 导出到文件 | 导出生成合法 JSON | `tests/test_storage.py::TestStorageExport::test_export_produces_valid_json` | 文件内容为 JSON 数组，条目字段完整 |
| TC-F007-02 | F-007 导出到文件 | 导出空列表 | `tests/test_storage.py::TestStorageExport::test_export_empty_list` | 生成 `[]` 的合法 JSON |
| TC-F008-01 | F-008 从文件导入 | 导入合法 JSON 文件 | `tests/test_storage.py::TestStorageImport::test_import_replace` | 返回正确条目列表，字段解析无误 |
| TC-F008-02 | F-008 从文件导入 | 导入不存在的文件 | `tests/test_storage.py::TestStorageImport::test_import_invalid_file_raises` | 抛出 `FileNotFoundError` |
| TC-F008-03 | F-008 从文件导入 | 导入非 JSON 格式文件 | `tests/test_storage.py::TestStorageImport::test_import_bad_json_raises` | 抛出 `json.JSONDecodeError` |
| TC-F011-01 | F-011 快捷键自定义 | 设置并读取自定义快捷键 | `tests/test_hotkey.py::TestHotkeyManagerConfig::test_set_and_get_hotkey` | `set_hotkey` 后 `get_hotkey` 返回完全一致的修饰键和键值 |
| TC-F011-02 | F-011 快捷键自定义 | Hotkey 序列化/反序列化 | `tests/test_hotkey.py::TestHotkeyDataclass::test_to_dict_from_dict_round_trip` | `to_dict` → `from_dict` 往返后数据一致 |
| TC-F012-01 | F-012 快捷键持久化 | 配置保存到文件后新建 Manager 可加载 | `tests/test_hotkey.py::TestHotkeyManagerConfig::test_config_persisted_to_disk` | 新 `HotkeyManager` 实例加载的快捷键与之前设置的一致 |
| TC-F012-02 | F-012 快捷键持久化 | 无配置文件时使用默认值 | `tests/test_hotkey.py::TestHotkeyManagerConfig::test_default_when_no_config` | 首次启动快捷键为 `Ctrl+T` |

### 4.2 人工验证用例

以下用例涉及 GUI 渲染、动画、全局系统交互，无法在无头 pytest 环境中自动判定，需人工操作并观察结果。每个用例均注明判定标准。

| 用例编号 | 对应功能 | 测试点 | 操作步骤 | 验收标准（人工判定） |
|----------|----------|--------|----------|----------------------|
| TC-F001-M | F-001 添加待办事项 | 界面添加（按钮 + 回车） | 1. 启动应用 2. 在底部输入"测试条目" 3. 选择优先级"高" 4. 点击"添加"；再输入"条目2"按回车 | 用户自行检查列表是否出现两条新条目，"测试条目"带橙色色条，"条目2"位于中优先级区域。两者按优先级降序排列。 |
| TC-F002-M | F-002 快速添加快捷键 | 弹出窗口 + 添加功能 | 1. 应用最小化或切到其他窗口 2. 按下 `Ctrl+T` 3. 在弹窗中输入"快速条目" 4. 选择优先级 5. 按回车 | 用户自行检查是否弹出"快速添加"窗口，且输入焦点在文本框。回车后弹窗关闭，主窗口列表中新增该条目。 |
| TC-F004-M | F-004 标记完成 | 界面复选框交互 | 1. 添加 3 条未完成条目 2. 勾选中间条目的复选框 | 用户自行检查被勾选条目文字是否变灰并出现删除线，且自动移至列表末尾。 |
| TC-F005-M | F-005 删除条目 | 界面删除按钮 | 1. 添加若干条目 2. 点击某条目的"✕"按钮 | 用户自行检查该条目是否从列表消失，关闭重启后不再出现。 |
| TC-F008-M | F-008 从文件导入 | 导入 UI 交互（替换/合并/无效） | 1. 点击"导出"，将当前列表保存为文件 2. 点击"导入"，选择刚才的文件 3. 选择"是"(替换)，观察列表 4. 再次导入同一文件，选择"否"(合并)，观察列表 5. 导入一个非 JSON 文件，观察提示 | 用户自行检查：(a) 替换后列表与导出时一致；(b) 合并后条目数 = 原列表 + 导入列表；(c) 导入无效文件时弹出错误提示且列表不变。 |
| TC-F009-M | F-009 屏幕边缘自动隐藏 | 左边缘/右边缘/上边缘/下边缘 | 1. 拖动窗口至屏幕左边缘 2. 鼠标移出窗口区域 3. 等待 0.4 秒 | 用户自行检查窗口是否向左侧滑出屏幕，仅留约 3px 的把手可见。依次测试右、上、下边缘行为是否一致。 |
| TC-F010-M | F-010 边缘弹出恢复 | 隐藏后鼠标触发弹出 | 1. 确认窗口已隐藏至左边缘 2. 将鼠标移向屏幕左边缘的 3px 把手区域 | 用户自行检查窗口是否向右滑出并完整显示在原来位置。依次测试右、上、下边缘的恢复行为。 |
| TC-F011-M | F-011 快捷键自定义 | 设置界面录制新快捷键 | 1. 点击"设置" 2. 点击"录制新快捷键" 3. 按下 `Ctrl+Shift+N` 4. 点击"保存" 5. 切换到其他窗口按 `Ctrl+Shift+N` | 用户自行检查：(a) 录制后设置界面显示"新快捷键: CTRL+SHIFT+N"；(b) 保存后按新快捷键能弹出快速添加；(c) 旧快捷键失效。 |
| TC-F011-M2 | F-011 快捷键自定义 | 录制时仅按字母键（无修饰键） | 1. 设置 → 录制 2. 仅按字母键（如"T"） | 用户自行检查是否提示"必须包含至少一个修饰键"，录制不完成。 |
| TC-F022-M | 边界测试 | 窗口在非边缘位置不触发隐藏 | 1. 将窗口放在屏幕中央 2. 鼠标离开窗口 | 用户自行检查窗口不执行隐藏动画。 |

---

*文档版本: 2.0 — 最后更新: 2026-05-23*
