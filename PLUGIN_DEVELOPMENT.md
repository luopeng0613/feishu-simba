# 📘 插件开发指南

本指南将教你如何为飞书Simba机器人开发插件。

## 🎯 核心概念

### 插件是什么？

插件是机器人功能的独立模块，每个插件负责一个特定的功能领域。插件系统的设计目标是：

- **独立性** - 插件之间互不干扰
- **可插拔** - 随时添加或移除插件
- **简单性** - 开发新插件只需几步

### 插件架构

```
plugins/
├── base_plugin.py          # 所有插件的基类
├── your_plugin/            # 你的插件目录
│   ├── __init__.py        # Python包标识
│   └── plugin.py          # 插件实现
```

## 🚀 快速开始

### 步骤 1: 创建插件目录

```bash
cd plugins
mkdir my_plugin
cd my_plugin
touch __init__.py plugin.py
```

### 步骤 2: 编写插件代码

编辑 `plugin.py`:

```python
from plugins.base_plugin import BasePlugin
from typing import Dict, Any, List, Optional


class MyPlugin(BasePlugin):
    """我的第一个插件"""

    @property
    def name(self) -> str:
        """插件名称"""
        return "我的插件"

    @property
    def description(self) -> str:
        """插件描述"""
        return "这是我的第一个插件"

    @property
    def version(self) -> str:
        """插件版本"""
        return "1.0.0"

    @property
    def author(self) -> str:
        """插件作者"""
        return "Your Name"

    @property
    def commands(self) -> List[Dict[str, str]]:
        """插件命令列表"""
        return [
            {
                "command": "/hello",
                "description": "打招呼",
                "usage": "/hello [名字]"
            }
        ]

    def handle_command(self, command: str, args: List[str],
                      event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理命令"""
        if command == "hello":
            # 获取参数
            name = args[0] if args else "世界"

            # 返回文本响应
            return self.create_text_response(f"你好，{name}！")

        return None
```

### 步骤 3: 重启机器人

```bash
python app.py
```

插件会自动加载！在群里输入 `/hello` 测试。

## 📚 BasePlugin API

### 必须实现的属性

```python
@property
def name(self) -> str:
    """插件名称，显示给用户"""
    return "插件名称"

@property
def description(self) -> str:
    """插件描述，说明插件功能"""
    return "插件描述"

@property
def version(self) -> str:
    """插件版本号"""
    return "1.0.0"

@property
def author(self) -> str:
    """插件作者"""
    return "作者名称"
```

### 可选属性

```python
@property
def commands(self) -> List[Dict[str, str]]:
    """
    插件支持的命令列表
    显示在帮助信息中
    """
    return [
        {
            "command": "/cmd",
            "description": "命令描述",
            "usage": "/cmd <参数>"
        }
    ]

@property
def enabled(self) -> bool:
    """
    插件是否启用
    返回False将不加载插件
    """
    return True
```

### 核心方法

#### 1. 处理命令

```python
def handle_command(self, command: str, args: List[str],
                  event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    处理命令

    Args:
        command: 命令名称（不含前缀）
        args: 命令参数列表
        event: 完整的事件数据

    Returns:
        处理结果，或None表示不处理
    """
    if command == "mycommand":
        # 处理逻辑
        return self.create_text_response("处理成功")

    return None
```

#### 2. 处理消息事件

```python
async def on_message(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    处理消息事件（异步）

    Args:
        event: 消息事件数据

    Returns:
        处理结果，或None表示不处理
    """
    text = self.get_message_text(event)

    if "关键词" in text:
        return self.create_text_response("检测到关键词")

    return None
```

#### 3. 处理卡片交互

```python
async def on_card_action(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    处理卡片交互事件

    Args:
        event: 卡片交互事件数据

    Returns:
        处理结果
    """
    action = event.get("action", {})
    value = action.get("value", {})

    if value.get("action") == "my_action":
        # 处理交互
        return self.create_text_response("已处理")

    return None
```

### 生命周期钩子

```python
def on_load(self):
    """
    插件加载时调用
    可以在这里初始化资源
    """
    self.logger.info("插件已加载")
    # 初始化数据库连接等

def on_unload(self):
    """
    插件卸载时调用
    可以在这里清理资源
    """
    self.logger.info("插件已卸载")
    # 关闭数据库连接等
```

## 🛠️ 工具方法

BasePlugin提供了很多实用方法：

### 响应创建

```python
# 文本响应
self.create_text_response("文本内容")

# 卡片响应
card = {
    "config": {"wide_screen_mode": True},
    "header": {
        "template": "blue",
        "title": {"content": "标题", "tag": "plain_text"}
    },
    "elements": [...]
}
self.create_card_response(card)
```

### 数据提取

```python
# 获取消息文本
text = self.get_message_text(event)

# 获取发送者信息
sender = self.get_sender_info(event)
# 返回: {"sender_id": "xxx", "sender_type": "user", "tenant_key": "xxx"}

# 获取群聊ID
chat_id = self.get_chat_id(event)

# 获取消息ID
message_id = self.get_message_id(event)

# 获取@用户列表
mentions = self.extract_mentions(event)
```

### 日志记录

```python
# 插件自带logger
self.logger.info("信息日志")
self.logger.warning("警告日志")
self.logger.error("错误日志")
self.logger.debug("调试日志")
```

### 访问机器人功能

```python
# 飞书客户端
self.bot.feishu_client.send_text_message(chat_id, "消息")
self.bot.feishu_client.get_chat_members(chat_id)

# 配置
data_dir = self.bot.config.DATA_DIR
```

## 💾 数据持久化

### 使用JSON文件

```python
import json
import os

class MyPlugin(BasePlugin):
    def __init__(self, bot):
        super().__init__(bot)
        self.data_file = os.path.join(
            bot.config.DATA_DIR,
            'my_plugin.json'
        )
        self.data = self._load_data()

    def _load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _save_data(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
```

## 🎨 发送卡片消息

### 基础卡片

```python
card = {
    "config": {
        "wide_screen_mode": True
    },
    "header": {
        "template": "blue",  # 颜色: blue/red/yellow/green/orange/purple
        "title": {
            "content": "卡片标题",
            "tag": "plain_text"
        }
    },
    "elements": [
        {
            "tag": "div",
            "text": {
                "content": "**粗体文本**\n普通文本",
                "tag": "lark_md"
            }
        },
        {
            "tag": "hr"  # 分割线
        },
        {
            "tag": "note",
            "elements": [
                {
                    "tag": "plain_text",
                    "content": "备注信息"
                }
            ]
        }
    ]
}

return self.create_card_response(card)
```

### 带按钮的卡片

```python
card = {
    "config": {"wide_screen_mode": True},
    "header": {
        "template": "blue",
        "title": {"content": "请选择", "tag": "plain_text"}
    },
    "elements": [
        {
            "tag": "action",
            "actions": [
                {
                    "tag": "button",
                    "text": {
                        "tag": "plain_text",
                        "content": "确认"
                    },
                    "type": "primary",
                    "value": {
                        "action": "confirm",
                        "data": "some_data"
                    }
                },
                {
                    "tag": "button",
                    "text": {
                        "tag": "plain_text",
                        "content": "取消"
                    },
                    "type": "default",
                    "value": {
                        "action": "cancel"
                    }
                }
            ]
        }
    ]
}
```

然后在 `on_card_action` 中处理按钮点击：

```python
async def on_card_action(self, event: Dict[str, Any]):
    action = event.get("action", {})
    value = action.get("value", {})

    if value.get("action") == "confirm":
        # 处理确认
        return self.create_text_response("已确认")
    elif value.get("action") == "cancel":
        # 处理取消
        return self.create_text_response("已取消")

    return None
```

## 📝 完整示例

### 示例：待办事项插件

```python
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from plugins.base_plugin import BasePlugin


class TodoPlugin(BasePlugin):
    """待办事项管理插件"""

    def __init__(self, bot):
        super().__init__(bot)
        self.data_file = os.path.join(bot.config.DATA_DIR, 'todo.json')
        self.todos = self._load_data()

    @property
    def name(self) -> str:
        return "待办事项"

    @property
    def description(self) -> str:
        return "管理团队待办事项"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def author(self) -> str:
        return "Your Name"

    @property
    def commands(self) -> List[Dict[str, str]]:
        return [
            {
                "command": "/todo add",
                "description": "添加待办",
                "usage": "/todo add <内容>"
            },
            {
                "command": "/todo list",
                "description": "查看待办列表",
                "usage": "/todo list"
            },
            {
                "command": "/todo done",
                "description": "完成待办",
                "usage": "/todo done <ID>"
            }
        ]

    def _load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"items": []}

    def _save_data(self):
        os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.todos, f, ensure_ascii=False, indent=2)

    def handle_command(self, command: str, args: List[str],
                      event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if command != "todo":
            return None

        if not args:
            return self.create_text_response("请指定操作: add/list/done")

        action = args[0]

        if action == "add":
            content = " ".join(args[1:])
            if not content:
                return self.create_text_response("请输入待办内容")

            todo_id = len(self.todos["items"]) + 1
            self.todos["items"].append({
                "id": todo_id,
                "content": content,
                "done": False,
                "created_at": datetime.now().isoformat()
            })
            self._save_data()

            return self.create_text_response(f"✅ 已添加待办 #{todo_id}")

        elif action == "list":
            items = [t for t in self.todos["items"] if not t["done"]]
            if not items:
                return self.create_text_response("📋 暂无待办事项")

            text = "📋 待办列表\n\n"
            for item in items:
                text += f"#{item['id']} {item['content']}\n"

            return self.create_text_response(text)

        elif action == "done":
            if len(args) < 2:
                return self.create_text_response("请指定待办ID")

            try:
                todo_id = int(args[1])
            except ValueError:
                return self.create_text_response("ID必须是数字")

            for item in self.todos["items"]:
                if item["id"] == todo_id:
                    item["done"] = True
                    self._save_data()
                    return self.create_text_response(
                        f"✅ 已完成: {item['content']}"
                    )

            return self.create_text_response("未找到该待办")

        return None
```

## 🔍 调试技巧

### 1. 启用调试日志

在 `.env` 中设置：
```
DEBUG=True
LOG_LEVEL=DEBUG
```

### 2. 使用日志

```python
self.logger.debug(f"收到参数: {args}")
self.logger.info(f"处理命令: {command}")
self.logger.warning(f"无效的参数")
self.logger.error(f"发生错误: {e}", exc_info=True)
```

### 3. 查看事件数据

```python
async def on_message(self, event: Dict[str, Any]):
    # 打印完整事件数据
    import json
    self.logger.debug(f"事件数据: {json.dumps(event, ensure_ascii=False)}")

    return None
```

## ⚠️ 最佳实践

### 1. 错误处理

```python
def handle_command(self, command, args, event):
    try:
        # 你的逻辑
        return self.create_text_response("成功")
    except Exception as e:
        self.logger.error(f"处理失败: {e}", exc_info=True)
        return self.create_text_response(f"❌ 发生错误: {str(e)}")
```

### 2. 参数验证

```python
if len(args) < 2:
    return self.create_text_response("用法: /cmd <参数1> <参数2>")

try:
    count = int(args[0])
except ValueError:
    return self.create_text_response("第一个参数必须是数字")
```

### 3. 权限检查

```python
sender = self.get_sender_info(event)
if sender["sender_id"] not in self.admins:
    return self.create_text_response("❌ 权限不足")
```

### 4. 性能优化

```python
# 避免耗时操作阻塞
import asyncio

async def on_message(self, event):
    # 异步处理耗时任务
    await asyncio.sleep(1)
    return self.create_text_response("完成")
```

## 🎓 进阶话题

### 定时任务

```python
import threading

class MyPlugin(BasePlugin):
    def on_load(self):
        # 启动定时任务
        self.timer = threading.Timer(60, self._periodic_task)
        self.timer.start()

    def _periodic_task(self):
        # 执行定时任务
        self.logger.info("执行定时任务")

        # 重新设置定时器
        self.timer = threading.Timer(60, self._periodic_task)
        self.timer.start()

    def on_unload(self):
        # 停止定时器
        if hasattr(self, 'timer'):
            self.timer.cancel()
```

### 外部API调用

```python
import requests

def handle_command(self, command, args, event):
    if command == "weather":
        city = args[0] if args else "北京"

        # 调用天气API
        response = requests.get(
            f"https://api.weather.com/city/{city}",
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            return self.create_text_response(
                f"🌤️ {city}天气：{data['weather']}"
            )
        else:
            return self.create_text_response("❌ 获取天气失败")
```

## 📦 发布插件

1. 确保插件目录结构正确
2. 编写详细的README
3. 测试所有功能
4. 提交到Git仓库

## 🆘 获取帮助

- 查看已有插件源码学习
- 阅读飞书开放平台文档
- 提交Issue获取帮助

---

**祝你开发愉快！** 🎉
