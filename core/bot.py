"""
飞书机器人核心类
"""
import logging
from typing import Dict, Any
from core.feishu_client import FeishuClient
from core.plugin_manager import PluginManager
from core.message_handler import MessageHandler

logger = logging.getLogger(__name__)


class FeishuBot:
    """飞书机器人核心类"""

    def __init__(self, config):
        """
        初始化机器人

        Args:
            config: 配置对象
        """
        self.config = config
        self.bot_open_id = None

        # 初始化飞书客户端
        self.feishu_client = FeishuClient(
            app_id=config.APP_ID,
            app_secret=config.APP_SECRET
        )

        # 初始化插件管理器
        self.plugin_manager = PluginManager(
            bot=self,
            plugins_dir=config.PLUGINS_DIR
        )

        # 初始化消息处理器
        self.message_handler = MessageHandler(bot=self)

        logger.info("飞书机器人初始化完成")

    def start(self):
        """启动机器人"""
        logger.info("正在启动飞书机器人...")

        # 验证配置
        try:
            self.config.validate()
        except ValueError as e:
            logger.error(f"配置验证失败: {e}")
            raise

        # 获取access token（验证凭证是否有效）
        try:
            self.feishu_client._get_tenant_access_token()
            logger.info("飞书凭证验证成功")
        except Exception as e:
            logger.error(f"飞书凭证验证失败: {e}")
            raise

        # 加载所有插件
        self.plugin_manager.load_all_plugins()

        logger.info("飞书机器人启动成功！")

    def stop(self):
        """停止机器人"""
        logger.info("正在停止飞书机器人...")

        # 卸载所有插件
        for plugin_name in list(self.plugin_manager.plugins.keys()):
            self.plugin_manager.unload_plugin(plugin_name)

        logger.info("飞书机器人已停止")

    async def handle_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理飞书事件

        Args:
            event: 事件数据

        Returns:
            处理结果
        """
        event_type = event.get("header", {}).get("event_type", "")

        logger.info(f"收到事件: {event_type}")

        # 消息事件
        if event_type == "im.message.receive_v1":
            await self.message_handler.handle_message(event.get("event", {}))

        # 卡片交互事件
        elif event_type == "card.action.trigger":
            await self.message_handler.handle_card_action(event.get("event", {}))

        # 其他事件可以在这里添加处理

        return {"code": 0}

    def verify_request(self, token: str, timestamp: str, nonce: str,
                       encrypt_key: str, body: str) -> bool:
        """
        验证请求签名

        Args:
            token: 验证token
            timestamp: 时间戳
            nonce: 随机数
            encrypt_key: 加密key
            body: 请求体

        Returns:
            是否验证通过
        """
        # 这里应该实现签名验证逻辑
        # 飞书的签名验证方法可以参考官方文档
        # https://open.feishu.cn/document/ukTMukTMukTM/uYDNxYjL2QTM24iN0EjN/event-subscription-configure-/encrypt-key-encryption-configuration-case
        return True

    def get_bot_info(self) -> Dict[str, Any]:
        """
        获取机器人信息

        Returns:
            机器人信息
        """
        return {
            "app_id": self.config.APP_ID,
            "plugins_count": len(self.plugin_manager.plugins),
            "plugins": self.plugin_manager.get_plugin_info()
        }
