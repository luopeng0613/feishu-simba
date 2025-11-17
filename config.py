"""
飞书机器人配置管理
"""
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class Config:
    """配置类"""

    # 飞书应用配置
    APP_ID = os.getenv('FEISHU_APP_ID', '')
    APP_SECRET = os.getenv('FEISHU_APP_SECRET', '')
    VERIFICATION_TOKEN = os.getenv('FEISHU_VERIFICATION_TOKEN', '')
    ENCRYPT_KEY = os.getenv('FEISHU_ENCRYPT_KEY', '')

    # 服务器配置
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 8000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

    # 数据存储配置
    DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')

    # 日志配置
    LOG_DIR = os.path.join(os.path.dirname(__file__), 'logs')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # 插件配置
    PLUGINS_DIR = os.path.join(os.path.dirname(__file__), 'plugins')

    # 命令前缀
    COMMAND_PREFIX = os.getenv('COMMAND_PREFIX', '/')

    @classmethod
    def validate(cls):
        """验证必要的配置是否存在"""
        required_fields = ['APP_ID', 'APP_SECRET', 'VERIFICATION_TOKEN']
        missing = [field for field in required_fields if not getattr(cls, field)]

        if missing:
            raise ValueError(f"缺少必要的配置项: {', '.join(missing)}")

        return True
