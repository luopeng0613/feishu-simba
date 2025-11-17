"""
值日抽签插件
支持随机抽取值日人员，可以设置值日周期
"""
import json
import random
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from plugins.base_plugin import BasePlugin


class DutyLotteryPlugin(BasePlugin):
    """值日抽签插件"""

    def __init__(self, bot):
        super().__init__(bot)
        self.data_file = os.path.join(bot.config.DATA_DIR, 'duty_lottery.json')
        self.duty_data = self._load_data()

    @property
    def name(self) -> str:
        return "值日抽签"

    @property
    def description(self) -> str:
        return "随机抽取值日人员，支持值日历史记录和公平性保证"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def author(self) -> str:
        return "Feishu Team"

    @property
    def commands(self) -> List[Dict[str, str]]:
        return [
            {
                "command": "/duty draw",
                "description": "抽取今日值日人员",
                "usage": "/duty draw"
            },
            {
                "command": "/duty list",
                "description": "查看值日历史记录",
                "usage": "/duty list [数量]"
            },
            {
                "command": "/duty today",
                "description": "查看今日值日人员",
                "usage": "/duty today"
            },
            {
                "command": "/duty stats",
                "description": "查看值日统计",
                "usage": "/duty stats"
            }
        ]

    def _load_data(self) -> Dict:
        """加载数据"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"加载数据失败: {e}")
                return {"history": [], "stats": {}}
        return {"history": [], "stats": {}}

    def _save_data(self):
        """保存数据"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.duty_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存数据失败: {e}")

    async def on_message(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理消息"""
        text = self.get_message_text(event)

        # 检查是否是值日相关消息
        if "值日" in text or "打扫" in text:
            # 如果被@了，提供帮助信息
            if self.extract_mentions(event):
                return self.create_text_response(
                    "📋 值日抽签功能\n\n"
                    "使用 /duty draw 进行抽签\n"
                    "使用 /duty today 查看今日值日人员\n"
                    "使用 /duty list 查看历史记录\n"
                    "使用 /duty stats 查看统计信息"
                )

        return None

    def handle_command(self, command: str, args: List[str],
                      event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理命令"""
        if command != "duty":
            return None

        if not args:
            return self.create_text_response(
                "请指定子命令: draw/today/list/stats"
            )

        sub_command = args[0].lower()

        if sub_command == "draw":
            return self._draw_duty(event)
        elif sub_command == "today":
            return self._show_today_duty(event)
        elif sub_command == "list":
            limit = int(args[1]) if len(args) > 1 else 10
            return self._show_history(event, limit)
        elif sub_command == "stats":
            return self._show_stats(event)
        else:
            return self.create_text_response(f"未知子命令: {sub_command}")

    def _draw_duty(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """抽取值日人员"""
        chat_id = self.get_chat_id(event)

        # 检查今天是否已经抽过签
        today = datetime.now().strftime("%Y-%m-%d")
        history = self.duty_data.get("history", [])

        for record in history:
            if record.get("date") == today and record.get("chat_id") == chat_id:
                user_name = record.get("user_name", "未知")
                return self.create_text_response(
                    f"⚠️ 今天已经抽过签了！\n今日值日: {user_name}"
                )

        # 获取群成员
        members = self.bot.feishu_client.get_chat_members(chat_id)

        if not members:
            return self.create_text_response("❌ 无法获取群成员列表")

        # 过滤掉机器人
        valid_members = [m for m in members if m.get("member_id_type") == "open_id"]

        if not valid_members:
            return self.create_text_response("❌ 群里没有可用成员")

        # 计算权重（值日次数少的权重高）
        stats = self.duty_data.get("stats", {})
        weighted_members = []

        for member in valid_members:
            open_id = member.get("member_id", "")
            count = stats.get(open_id, {}).get("count", 0)
            # 权重 = 最大次数 - 当前次数 + 1
            weight = max(stats.values(), key=lambda x: x.get("count", 0), default={"count": 0}).get("count", 0) - count + 1
            weighted_members.extend([member] * max(weight, 1))

        # 随机抽取
        selected = random.choice(weighted_members)
        open_id = selected.get("member_id", "")
        user_name = selected.get("name", "未知用户")

        # 记录历史
        record = {
            "date": today,
            "chat_id": chat_id,
            "open_id": open_id,
            "user_name": user_name,
            "timestamp": datetime.now().isoformat()
        }
        self.duty_data.setdefault("history", []).append(record)

        # 更新统计
        if open_id not in self.duty_data.setdefault("stats", {}):
            self.duty_data["stats"][open_id] = {
                "name": user_name,
                "count": 0,
                "last_date": None
            }

        self.duty_data["stats"][open_id]["count"] += 1
        self.duty_data["stats"][open_id]["last_date"] = today

        self._save_data()

        # 创建卡片消息
        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "template": "blue",
                "title": {
                    "content": "🎲 值日抽签结果",
                    "tag": "plain_text"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": f"**今日值日人员:** {user_name}\n**日期:** {today}",
                        "tag": "lark_md"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"这是第 {self.duty_data['stats'][open_id]['count']} 次值日"
                        }
                    ]
                }
            ]
        }

        return self.create_card_response(card)

    def _show_today_duty(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """查看今日值日"""
        chat_id = self.get_chat_id(event)
        today = datetime.now().strftime("%Y-%m-%d")

        history = self.duty_data.get("history", [])
        for record in reversed(history):
            if record.get("date") == today and record.get("chat_id") == chat_id:
                user_name = record.get("user_name", "未知")
                return self.create_text_response(
                    f"📅 今日值日人员: {user_name}"
                )

        return self.create_text_response("❌ 今天还没有进行值日抽签")

    def _show_history(self, event: Dict[str, Any], limit: int) -> Dict[str, Any]:
        """查看历史记录"""
        chat_id = self.get_chat_id(event)
        history = self.duty_data.get("history", [])

        # 过滤当前群的记录
        chat_history = [r for r in history if r.get("chat_id") == chat_id]

        if not chat_history:
            return self.create_text_response("📋 暂无值日历史记录")

        # 取最近的记录
        recent = chat_history[-limit:]

        text = f"📋 **值日历史记录** (最近{len(recent)}条)\n\n"
        for record in reversed(recent):
            date = record.get("date", "")
            user_name = record.get("user_name", "未知")
            text += f"• {date}: {user_name}\n"

        return self.create_text_response(text)

    def _show_stats(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """查看统计信息"""
        stats = self.duty_data.get("stats", {})

        if not stats:
            return self.create_text_response("📊 暂无统计数据")

        # 按次数排序
        sorted_stats = sorted(
            stats.items(),
            key=lambda x: x[1].get("count", 0),
            reverse=True
        )

        text = "📊 **值日统计**\n\n"
        for i, (open_id, data) in enumerate(sorted_stats[:10], 1):
            name = data.get("name", "未知")
            count = data.get("count", 0)
            last_date = data.get("last_date", "从未")
            text += f"{i}. {name}: {count}次 (最后: {last_date})\n"

        return self.create_text_response(text)

    async def on_card_action(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理卡片交互"""
        # 可以添加卡片交互功能，比如"重新抽签"按钮
        action = event.get("action", {})
        value = action.get("value", {})

        if value.get("action") == "redraw":
            return self._draw_duty(event)

        return None
