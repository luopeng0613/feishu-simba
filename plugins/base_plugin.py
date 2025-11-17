"""
插件基类
所有插件必须继承此类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class BasePlugin(ABC):
    """插件基类"""

    def __init__(self, bot):
        """
        初始化插件

        Args:
            bot: 机器人实例
        """
        self.bot = bot
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    @abstractmethod
    def name(self) -> str:
        """插件名称"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """插件描述"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """插件版本"""
        pass

    @property
    @abstractmethod
    def author(self) -> str:
        """插件作者"""
        pass

    @property
    def commands(self) -> List[Dict[str, str]]:
        """
        插件支持的命令列表

        Returns:
            命令列表，格式：[
                {
                    "command": "命令名称",
                    "description": "命令描述",
                    "usage": "使用示例"
                }
            ]
        """
        return []

    @property
    def enabled(self) -> bool:
        """插件是否启用（默认启用）"""
        return True

    def on_load(self):
        """
        插件加载时调用
        可以在这里初始化资源、加载数据等
        """
        self.logger.info(f"插件 {self.name} 已加载")

    def on_unload(self):
        """
        插件卸载时调用
        可以在这里清理资源、保存数据等
        """
        self.logger.info(f"插件 {self.name} 已卸载")

    async def on_message(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理消息事件（对话命令行模式）

        Args:
            event: 消息事件数据

        Returns:
            返回处理结果，如果不处理则返回None
            格式：{
                "handled": True/False,  # 是否处理了该消息
                "response": "响应内容",  # 可选
                "reply_type": "text/card"  # 响应类型，可选
            }
        """
        return None

    async def on_card_action(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理卡片交互事件（URL命令模式）

        Args:
            event: 卡片交互事件数据

        Returns:
            返回处理结果，如果不处理则返回None
        """
        return None

    def handle_command(self, command: str, args: List[str],
                      event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理命令

        Args:
            command: 命令名称
            args: 命令参数列表
            event: 事件数据

        Returns:
            返回处理结果
        """
        return None

    def get_help_text(self) -> str:
        """
        获取插件帮助文本

        Returns:
            帮助文本
        """
        help_text = f"📦 **{self.name}** v{self.version}\n"
        help_text += f"📝 {self.description}\n"
        help_text += f"👤 作者: {self.author}\n\n"

        if self.commands:
            help_text += "**命令列表:**\n"
            for cmd in self.commands:
                help_text += f"• `{cmd['command']}` - {cmd['description']}\n"
                if cmd.get('usage'):
                    help_text += f"  用法: {cmd['usage']}\n"

        return help_text

    def create_text_response(self, text: str) -> Dict[str, Any]:
        """
        创建文本响应

        Args:
            text: 文本内容

        Returns:
            响应数据
        """
        return {
            "handled": True,
            "response": text,
            "reply_type": "text"
        }

    def create_card_response(self, card: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建卡片响应

        Args:
            card: 卡片内容

        Returns:
            响应数据
        """
        return {
            "handled": True,
            "response": card,
            "reply_type": "card"
        }

    def extract_mentions(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        从事件中提取@用户列表

        Args:
            event: 事件数据

        Returns:
            被@的用户列表
        """
        message = event.get("message", {})
        mentions = message.get("mentions", [])
        return mentions

    def get_sender_info(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取消息发送者信息

        Args:
            event: 事件数据

        Returns:
            发送者信息
        """
        sender = event.get("sender", {})
        return {
            "sender_id": sender.get("sender_id", {}).get("open_id", ""),
            "sender_type": sender.get("sender_type", ""),
            "tenant_key": sender.get("tenant_key", "")
        }

    def get_message_text(self, event: Dict[str, Any]) -> str:
        """
        获取消息文本内容

        Args:
            event: 事件数据

        Returns:
            文本内容
        """
        import json

        message = event.get("message", {})
        content = message.get("content", "{}")

        try:
            content_dict = json.loads(content)
            return content_dict.get("text", "").strip()
        except:
            return ""

    def get_chat_id(self, event: Dict[str, Any]) -> str:
        """
        获取群聊ID

        Args:
            event: 事件数据

        Returns:
            群聊ID
        """
        message = event.get("message", {})
        return message.get("chat_id", "")

    def get_message_id(self, event: Dict[str, Any]) -> str:
        """
        获取消息ID

        Args:
            event: 事件数据

        Returns:
            消息ID
        """
        message = event.get("message", {})
        return message.get("message_id", "")
