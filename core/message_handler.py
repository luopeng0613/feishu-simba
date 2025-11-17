"""
消息处理器
"""
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class MessageHandler:
    """消息处理器"""

    def __init__(self, bot):
        """
        初始化消息处理器

        Args:
            bot: 机器人实例
        """
        self.bot = bot
        self.feishu_client = bot.feishu_client
        self.plugin_manager = bot.plugin_manager
        self.command_prefix = bot.config.COMMAND_PREFIX

    async def handle_message(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理消息事件

        Args:
            event: 消息事件数据

        Returns:
            处理结果
        """
        try:
            # 提取消息内容
            message = event.get("message", {})
            message_type = message.get("message_type", "")
            chat_type = message.get("chat_type", "")

            logger.info(f"收到消息: type={message_type}, chat_type={chat_type}")

            # 只处理文本消息
            if message_type != "text":
                logger.debug(f"忽略非文本消息: {message_type}")
                return None

            # 获取消息内容
            content = json.loads(message.get("content", "{}"))
            text = content.get("text", "").strip()

            if not text:
                return None

            logger.info(f"消息内容: {text}")

            # 检查是否是命令
            if text.startswith(self.command_prefix):
                return await self._handle_command(text, event)

            # 检查是否@了机器人
            if self._is_mentioned(event):
                # 移除@内容，获取纯文本
                text = self._remove_mentions(text)
                logger.info(f"机器人被@，处理内容: {text}")

                # 分发给插件处理
                handled = await self.plugin_manager.dispatch_message(event)

                if not handled:
                    # 如果没有插件处理，返回默认帮助信息
                    return await self._send_help(event)

            return None

        except Exception as e:
            logger.error(f"处理消息时发生错误: {e}", exc_info=True)
            return None

    async def _handle_command(self, text: str, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理命令

        Args:
            text: 命令文本
            event: 事件数据

        Returns:
            处理结果
        """
        # 移除命令前缀
        command_text = text[len(self.command_prefix):].strip()

        # 分割命令和参数
        parts = command_text.split()
        if not parts:
            return None

        command = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []

        logger.info(f"执行命令: {command}, 参数: {args}")

        # 内置命令处理
        if command == "help":
            return await self._send_help(event, args)
        elif command == "plugins":
            return await self._send_plugins_list(event)
        elif command == "reload":
            return await self._reload_plugin(event, args)

        # 分发给插件处理
        for plugin in self.plugin_manager.get_all_plugins():
            try:
                result = plugin.handle_command(command, args, event)
                if result and result.get("handled"):
                    await self._send_response(event, result)
                    return result
            except Exception as e:
                logger.error(f"插件 {plugin.name} 处理命令失败: {e}", exc_info=True)

        # 命令未找到
        message_id = event.get("message", {}).get("message_id", "")
        self.feishu_client.reply_message(
            message_id,
            "text",
            {"text": f"❌ 未知命令: {command}\n使用 /help 查看可用命令"}
        )

        return None

    async def _send_help(self, event: Dict[str, Any], args: list = None) -> Dict[str, Any]:
        """
        发送帮助信息

        Args:
            event: 事件数据
            args: 参数列表（可选，用于查询特定插件帮助）

        Returns:
            处理结果
        """
        message_id = event.get("message", {}).get("message_id", "")

        # 如果指定了插件名称，显示该插件的帮助
        if args and len(args) > 0:
            plugin_name = args[0]
            plugin = self.plugin_manager.get_plugin(plugin_name)

            if plugin:
                help_text = plugin.get_help_text()
            else:
                help_text = f"❌ 插件不存在: {plugin_name}"
        else:
            # 显示总体帮助信息
            help_text = "🤖 **飞书团队机器人使用指南**\n\n"
            help_text += "**内置命令:**\n"
            help_text += f"• `{self.command_prefix}help` - 显示帮助信息\n"
            help_text += f"• `{self.command_prefix}help <插件名>` - 显示特定插件帮助\n"
            help_text += f"• `{self.command_prefix}plugins` - 列出所有插件\n\n"

            help_text += "**已加载的插件:**\n"
            for plugin in self.plugin_manager.get_all_plugins():
                help_text += f"• **{plugin.name}** - {plugin.description}\n"

            help_text += f"\n💡 使用 `{self.command_prefix}help <插件名>` 查看插件详细用法"

        self.feishu_client.reply_message(
            message_id,
            "text",
            {"text": help_text}
        )

        return {"handled": True}

    async def _send_plugins_list(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送插件列表

        Args:
            event: 事件数据

        Returns:
            处理结果
        """
        message_id = event.get("message", {}).get("message_id", "")

        plugins_info = self.plugin_manager.get_plugin_info()

        if not plugins_info:
            text = "📦 当前没有加载任何插件"
        else:
            text = f"📦 **已加载的插件** (共 {len(plugins_info)} 个)\n\n"
            for info in plugins_info:
                text += f"• **{info['name']}** v{info['version']}\n"
                text += f"  {info['description']}\n"
                text += f"  作者: {info['author']}\n\n"

        self.feishu_client.reply_message(
            message_id,
            "text",
            {"text": text}
        )

        return {"handled": True}

    async def _reload_plugin(self, event: Dict[str, Any], args: list) -> Dict[str, Any]:
        """
        重新加载插件

        Args:
            event: 事件数据
            args: 参数列表

        Returns:
            处理结果
        """
        message_id = event.get("message", {}).get("message_id", "")

        if not args or len(args) == 0:
            text = "❌ 请指定要重新加载的插件名称"
        else:
            plugin_name = args[0]
            success = self.plugin_manager.reload_plugin(plugin_name)

            if success:
                text = f"✅ 插件 {plugin_name} 重新加载成功"
            else:
                text = f"❌ 插件 {plugin_name} 重新加载失败"

        self.feishu_client.reply_message(
            message_id,
            "text",
            {"text": text}
        )

        return {"handled": True}

    async def _send_response(self, event: Dict[str, Any], result: Dict[str, Any]):
        """
        发送响应

        Args:
            event: 事件数据
            result: 处理结果
        """
        if not result.get("response"):
            return

        message_id = event.get("message", {}).get("message_id", "")
        reply_type = result.get("reply_type", "text")
        response = result.get("response")

        if reply_type == "text":
            self.feishu_client.reply_message(
                message_id,
                "text",
                {"text": response}
            )
        elif reply_type == "card":
            self.feishu_client.reply_message(
                message_id,
                "interactive",
                response
            )

    def _is_mentioned(self, event: Dict[str, Any]) -> bool:
        """
        检查机器人是否被@

        Args:
            event: 事件数据

        Returns:
            是否被@
        """
        message = event.get("message", {})
        mentions = message.get("mentions", [])

        # 检查是否有@当前机器人
        for mention in mentions:
            # 飞书机器人的mention会包含机器人的信息
            if mention.get("id", {}).get("open_id") == self.bot.bot_open_id:
                return True

        return len(mentions) > 0

    def _remove_mentions(self, text: str) -> str:
        """
        移除文本中的@标记

        Args:
            text: 原始文本

        Returns:
            清理后的文本
        """
        # 移除@xxx格式的文本
        import re
        text = re.sub(r'@\w+\s*', '', text)
        return text.strip()

    async def handle_card_action(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理卡片交互事件

        Args:
            event: 卡片交互事件数据

        Returns:
            处理结果
        """
        try:
            action = event.get("action", {})
            value = action.get("value", {})

            logger.info(f"收到卡片交互: {value}")

            # 分发给插件处理
            handled = await self.plugin_manager.dispatch_card_action(event)

            if handled:
                logger.info("卡片交互已处理")
            else:
                logger.warning("没有插件处理该卡片交互")

            return None

        except Exception as e:
            logger.error(f"处理卡片交互时发生错误: {e}", exc_info=True)
            return None
