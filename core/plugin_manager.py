"""
插件管理器
负责插件的加载、卸载和管理
"""
import os
import sys
import importlib
import inspect
import logging
from typing import Dict, List, Optional
from plugins.base_plugin import BasePlugin

logger = logging.getLogger(__name__)


class PluginManager:
    """插件管理器"""

    def __init__(self, bot, plugins_dir: str):
        """
        初始化插件管理器

        Args:
            bot: 机器人实例
            plugins_dir: 插件目录路径
        """
        self.bot = bot
        self.plugins_dir = plugins_dir
        self.plugins: Dict[str, BasePlugin] = {}

        # 将插件目录添加到Python路径
        if plugins_dir not in sys.path:
            sys.path.insert(0, os.path.dirname(plugins_dir))

    def load_all_plugins(self):
        """加载所有插件"""
        logger.info(f"开始加载插件，目录: {self.plugins_dir}")

        if not os.path.exists(self.plugins_dir):
            logger.warning(f"插件目录不存在: {self.plugins_dir}")
            return

        # 遍历插件目录
        for item in os.listdir(self.plugins_dir):
            plugin_path = os.path.join(self.plugins_dir, item)

            # 跳过非目录和特殊目录
            if not os.path.isdir(plugin_path):
                continue
            if item.startswith('__') or item.startswith('.'):
                continue

            # 尝试加载插件
            try:
                self._load_plugin(item)
            except Exception as e:
                logger.error(f"加载插件 {item} 失败: {e}", exc_info=True)

        logger.info(f"插件加载完成，共加载 {len(self.plugins)} 个插件")

    def _load_plugin(self, plugin_name: str):
        """
        加载单个插件

        Args:
            plugin_name: 插件名称（目录名）
        """
        try:
            # 导入插件模块
            module_name = f"plugins.{plugin_name}.plugin"
            module = importlib.import_module(module_name)

            # 查找插件类（继承自BasePlugin的类）
            plugin_class = None
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, BasePlugin) and obj != BasePlugin:
                    plugin_class = obj
                    break

            if not plugin_class:
                logger.warning(f"插件 {plugin_name} 中未找到有效的插件类")
                return

            # 实例化插件
            plugin_instance = plugin_class(self.bot)

            # 检查插件是否启用
            if not plugin_instance.enabled:
                logger.info(f"插件 {plugin_instance.name} 已禁用，跳过加载")
                return

            # 注册插件
            self.plugins[plugin_instance.name] = plugin_instance

            # 调用插件的加载钩子
            plugin_instance.on_load()

            logger.info(f"插件加载成功: {plugin_instance.name} v{plugin_instance.version}")

        except ImportError as e:
            logger.error(f"导入插件 {plugin_name} 失败: {e}")
        except Exception as e:
            logger.error(f"加载插件 {plugin_name} 时发生错误: {e}", exc_info=True)

    def unload_plugin(self, plugin_name: str) -> bool:
        """
        卸载插件

        Args:
            plugin_name: 插件名称

        Returns:
            是否成功卸载
        """
        if plugin_name not in self.plugins:
            logger.warning(f"插件 {plugin_name} 不存在")
            return False

        try:
            plugin = self.plugins[plugin_name]
            plugin.on_unload()
            del self.plugins[plugin_name]
            logger.info(f"插件卸载成功: {plugin_name}")
            return True
        except Exception as e:
            logger.error(f"卸载插件 {plugin_name} 失败: {e}", exc_info=True)
            return False

    def reload_plugin(self, plugin_name: str) -> bool:
        """
        重新加载插件

        Args:
            plugin_name: 插件名称

        Returns:
            是否成功重新加载
        """
        # 先卸载
        if plugin_name in self.plugins:
            self.unload_plugin(plugin_name)

        # 重新加载模块
        try:
            module_name = f"plugins.{plugin_name}.plugin"
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])

            # 重新加载插件
            self._load_plugin(plugin_name)
            return True
        except Exception as e:
            logger.error(f"重新加载插件 {plugin_name} 失败: {e}", exc_info=True)
            return False

    def get_plugin(self, plugin_name: str) -> Optional[BasePlugin]:
        """
        获取插件实例

        Args:
            plugin_name: 插件名称

        Returns:
            插件实例，如果不存在则返回None
        """
        return self.plugins.get(plugin_name)

    def get_all_plugins(self) -> List[BasePlugin]:
        """
        获取所有已加载的插件

        Returns:
            插件列表
        """
        return list(self.plugins.values())

    def get_plugin_info(self) -> List[Dict[str, str]]:
        """
        获取所有插件的信息

        Returns:
            插件信息列表
        """
        info_list = []
        for plugin in self.plugins.values():
            info_list.append({
                "name": plugin.name,
                "description": plugin.description,
                "version": plugin.version,
                "author": plugin.author,
                "enabled": str(plugin.enabled)
            })
        return info_list

    async def dispatch_message(self, event: Dict) -> bool:
        """
        将消息分发给所有插件处理

        Args:
            event: 消息事件

        Returns:
            是否有插件处理了该消息
        """
        for plugin in self.plugins.values():
            try:
                result = await plugin.on_message(event)
                if result and result.get("handled"):
                    logger.info(f"消息已被插件 {plugin.name} 处理")
                    return True
            except Exception as e:
                logger.error(f"插件 {plugin.name} 处理消息时发生错误: {e}", exc_info=True)

        return False

    async def dispatch_card_action(self, event: Dict) -> bool:
        """
        将卡片交互事件分发给所有插件处理

        Args:
            event: 卡片交互事件

        Returns:
            是否有插件处理了该事件
        """
        for plugin in self.plugins.values():
            try:
                result = await plugin.on_card_action(event)
                if result and result.get("handled"):
                    logger.info(f"卡片交互已被插件 {plugin.name} 处理")
                    return True
            except Exception as e:
                logger.error(f"插件 {plugin.name} 处理卡片交互时发生错误: {e}", exc_info=True)

        return False

    def get_all_commands(self) -> Dict[str, List[Dict[str, str]]]:
        """
        获取所有插件的命令列表

        Returns:
            命令字典，格式：{plugin_name: [commands]}
        """
        all_commands = {}
        for plugin in self.plugins.values():
            if plugin.commands:
                all_commands[plugin.name] = plugin.commands
        return all_commands
