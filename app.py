"""
飞书机器人主应用
使用Flask接收飞书Webhook事件
"""
import json
import logging
import asyncio
from flask import Flask, request, jsonify
from config import Config
from core.bot import FeishuBot

# 配置日志
logging.basicConfig(
    level=Config.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{Config.LOG_DIR}/bot.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 创建机器人实例
bot = FeishuBot(Config)


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        "status": "ok",
        "bot_info": bot.get_bot_info()
    })


@app.route('/webhook/event', methods=['POST'])
def handle_event():
    """
    处理飞书事件回调
    """
    try:
        # 获取请求数据
        data = request.json

        logger.debug(f"收到事件: {json.dumps(data, ensure_ascii=False)}")

        # URL验证
        if data.get("type") == "url_verification":
            challenge = data.get("challenge", "")
            logger.info("URL验证请求")
            return jsonify({"challenge": challenge})

        # 事件回调
        if data.get("header", {}).get("event_type"):
            # 在异步环境中处理事件
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(bot.handle_event(data))
            loop.close()

            return jsonify(result)

        return jsonify({"code": 0})

    except Exception as e:
        logger.error(f"处理事件失败: {e}", exc_info=True)
        return jsonify({"code": 1, "msg": str(e)})


@app.route('/webhook/card', methods=['POST'])
def handle_card_action():
    """
    处理卡片交互回调
    """
    try:
        data = request.json
        logger.debug(f"收到卡片交互: {json.dumps(data, ensure_ascii=False)}")

        # 在异步环境中处理事件
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(bot.handle_event(data))
        loop.close()

        return jsonify(result)

    except Exception as e:
        logger.error(f"处理卡片交互失败: {e}", exc_info=True)
        return jsonify({"code": 1, "msg": str(e)})


@app.route('/api/plugins', methods=['GET'])
def list_plugins():
    """
    查看已加载的插件列表
    """
    try:
        plugins_info = bot.plugin_manager.get_plugin_info()
        return jsonify({
            "code": 0,
            "data": {
                "count": len(plugins_info),
                "plugins": plugins_info
            }
        })
    except Exception as e:
        logger.error(f"获取插件列表失败: {e}", exc_info=True)
        return jsonify({"code": 1, "msg": str(e)})


@app.route('/api/plugins/<plugin_name>/reload', methods=['POST'])
def reload_plugin(plugin_name):
    """
    重新加载指定插件
    """
    try:
        success = bot.plugin_manager.reload_plugin(plugin_name)
        if success:
            return jsonify({
                "code": 0,
                "msg": f"插件 {plugin_name} 重新加载成功"
            })
        else:
            return jsonify({
                "code": 1,
                "msg": f"插件 {plugin_name} 重新加载失败"
            })
    except Exception as e:
        logger.error(f"重新加载插件失败: {e}", exc_info=True)
        return jsonify({"code": 1, "msg": str(e)})


def main():
    """主函数"""
    try:
        # 启动机器人
        logger.info("=" * 50)
        logger.info("飞书团队机器人启动中...")
        logger.info("=" * 50)

        bot.start()

        # 启动Flask服务
        logger.info(f"Web服务启动在 {Config.HOST}:{Config.PORT}")
        app.run(
            host=Config.HOST,
            port=Config.PORT,
            debug=Config.DEBUG
        )

    except KeyboardInterrupt:
        logger.info("收到停止信号，正在关闭...")
        bot.stop()
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        bot.stop()


if __name__ == '__main__':
    main()
