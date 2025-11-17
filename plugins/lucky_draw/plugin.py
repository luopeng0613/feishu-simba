"""
随机抽奖插件
支持创建抽奖活动，参与抽奖，开奖等功能
"""
import json
import random
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from plugins.base_plugin import BasePlugin


class LuckyDrawPlugin(BasePlugin):
    """随机抽奖插件"""

    def __init__(self, bot):
        super().__init__(bot)
        self.data_file = os.path.join(bot.config.DATA_DIR, 'lucky_draw.json')
        self.draws_data = self._load_data()

    @property
    def name(self) -> str:
        return "随机抽奖"

    @property
    def description(self) -> str:
        return "创建抽奖活动，群成员可参与抽奖"

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
                "command": "/lottery create",
                "description": "创建抽奖活动",
                "usage": "/lottery create <奖品名称> <中奖人数>"
            },
            {
                "command": "/lottery join",
                "description": "参与当前抽奖",
                "usage": "/lottery join [抽奖ID]"
            },
            {
                "command": "/lottery draw",
                "description": "开始抽奖",
                "usage": "/lottery draw [抽奖ID]"
            },
            {
                "command": "/lottery list",
                "description": "查看进行中的抽奖",
                "usage": "/lottery list"
            },
            {
                "command": "/lottery info",
                "description": "查看抽奖详情",
                "usage": "/lottery info <抽奖ID>"
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
                return {"draws": {}}
        return {"draws": {}}

    def _save_data(self):
        """保存数据"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.draws_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存数据失败: {e}")

    async def on_message(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理消息"""
        text = self.get_message_text(event)

        if "抽奖" in text or "lottery" in text.lower():
            if self.extract_mentions(event):
                return self.create_text_response(
                    "🎁 抽奖功能\n\n"
                    "使用 /lottery create <奖品> <人数> 创建抽奖\n"
                    "使用 /lottery join 参与抽奖\n"
                    "使用 /lottery draw 开奖\n"
                    "使用 /lottery list 查看进行中的抽奖"
                )

        return None

    def handle_command(self, command: str, args: List[str],
                      event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理命令"""
        if command != "lottery":
            return None

        if not args:
            return self.create_text_response(
                "请指定子命令: create/join/draw/list/info"
            )

        sub_command = args[0].lower()

        if sub_command == "create":
            if len(args) < 3:
                return self.create_text_response(
                    "用法: /lottery create <奖品名称> <中奖人数>"
                )
            prize_name = args[1]
            try:
                winner_count = int(args[2])
            except ValueError:
                return self.create_text_response("中奖人数必须是数字")
            return self._create_lottery(event, prize_name, winner_count)

        elif sub_command == "join":
            draw_id = args[1] if len(args) > 1 else None
            return self._join_lottery(event, draw_id)

        elif sub_command == "draw":
            draw_id = args[1] if len(args) > 1 else None
            return self._do_lottery(event, draw_id)

        elif sub_command == "list":
            return self._list_lotteries(event)

        elif sub_command == "info":
            if len(args) < 2:
                return self.create_text_response("用法: /lottery info <抽奖ID>")
            return self._show_lottery_info(event, args[1])

        else:
            return self.create_text_response(f"未知子命令: {sub_command}")

    def _create_lottery(self, event: Dict[str, Any], prize_name: str,
                       winner_count: int) -> Dict[str, Any]:
        """创建抽奖"""
        chat_id = self.get_chat_id(event)
        sender = self.get_sender_info(event)

        # 生成抽奖ID
        draw_id = str(uuid.uuid4())[:8]

        # 创建抽奖记录
        draw_info = {
            "id": draw_id,
            "chat_id": chat_id,
            "prize_name": prize_name,
            "winner_count": winner_count,
            "creator": sender["sender_id"],
            "participants": [],
            "winners": [],
            "status": "active",  # active/finished
            "created_at": datetime.now().isoformat(),
            "finished_at": None
        }

        self.draws_data.setdefault("draws", {})[draw_id] = draw_info
        self._save_data()

        # 创建卡片消息
        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "template": "red",
                "title": {
                    "content": "🎁 新抽奖活动",
                    "tag": "plain_text"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": f"**奖品:** {prize_name}\n**中奖人数:** {winner_count}\n**抽奖ID:** `{draw_id}`",
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
                            "content": f"使用 /lottery join {draw_id} 参与抽奖"
                        }
                    ]
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "🎲 参与抽奖"
                            },
                            "type": "primary",
                            "value": {
                                "action": "join_lottery",
                                "draw_id": draw_id
                            }
                        }
                    ]
                }
            ]
        }

        return self.create_card_response(card)

    def _join_lottery(self, event: Dict[str, Any], draw_id: Optional[str] = None) -> Dict[str, Any]:
        """参与抽奖"""
        chat_id = self.get_chat_id(event)
        sender = self.get_sender_info(event)
        sender_id = sender["sender_id"]

        # 如果没有指定抽奖ID，查找当前群最新的活动
        if not draw_id:
            active_draws = [
                d for d in self.draws_data.get("draws", {}).values()
                if d["chat_id"] == chat_id and d["status"] == "active"
            ]

            if not active_draws:
                return self.create_text_response("❌ 当前没有进行中的抽奖活动")

            # 使用最新的抽奖
            draw_info = sorted(active_draws, key=lambda x: x["created_at"])[-1]
            draw_id = draw_info["id"]
        else:
            draw_info = self.draws_data.get("draws", {}).get(draw_id)

        if not draw_info:
            return self.create_text_response(f"❌ 抽奖活动不存在: {draw_id}")

        if draw_info["status"] != "active":
            return self.create_text_response("❌ 该抽奖活动已结束")

        # 检查是否已经参与
        if sender_id in draw_info["participants"]:
            return self.create_text_response("⚠️ 您已经参与过这个抽奖了")

        # 添加参与者
        draw_info["participants"].append(sender_id)
        self._save_data()

        participant_count = len(draw_info["participants"])
        return self.create_text_response(
            f"✅ 参与成功！\n当前已有 {participant_count} 人参与抽奖"
        )

    def _do_lottery(self, event: Dict[str, Any], draw_id: Optional[str] = None) -> Dict[str, Any]:
        """开奖"""
        chat_id = self.get_chat_id(event)
        sender = self.get_sender_info(event)

        # 如果没有指定抽奖ID，查找当前群最新的活动
        if not draw_id:
            active_draws = [
                d for d in self.draws_data.get("draws", {}).values()
                if d["chat_id"] == chat_id and d["status"] == "active"
            ]

            if not active_draws:
                return self.create_text_response("❌ 当前没有进行中的抽奖活动")

            draw_info = sorted(active_draws, key=lambda x: x["created_at"])[-1]
            draw_id = draw_info["id"]
        else:
            draw_info = self.draws_data.get("draws", {}).get(draw_id)

        if not draw_info:
            return self.create_text_response(f"❌ 抽奖活动不存在: {draw_id}")

        # 检查权限（只有创建者可以开奖）
        if draw_info["creator"] != sender["sender_id"]:
            return self.create_text_response("❌ 只有创建者可以开奖")

        if draw_info["status"] != "active":
            return self.create_text_response("❌ 该抽奖活动已结束")

        participants = draw_info["participants"]
        if not participants:
            return self.create_text_response("❌ 还没有人参与抽奖")

        winner_count = min(draw_info["winner_count"], len(participants))

        # 随机抽取中奖者
        winners = random.sample(participants, winner_count)
        draw_info["winners"] = winners
        draw_info["status"] = "finished"
        draw_info["finished_at"] = datetime.now().isoformat()

        self._save_data()

        # 创建开奖结果卡片
        winner_names = []
        for winner_id in winners:
            # 尝试获取用户信息
            user_info = self.bot.feishu_client.get_user_info(winner_id)
            if user_info:
                winner_names.append(user_info.get("name", winner_id))
            else:
                winner_names.append(winner_id)

        winners_text = "\n".join([f"{i+1}. {name}" for i, name in enumerate(winner_names)])

        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "template": "yellow",
                "title": {
                    "content": "🎊 抽奖结果",
                    "tag": "plain_text"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": f"**奖品:** {draw_info['prize_name']}\n**参与人数:** {len(participants)}",
                        "tag": "lark_md"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {
                        "content": f"**🏆 中奖名单:**\n{winners_text}",
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
                            "content": "恭喜以上中奖者！"
                        }
                    ]
                }
            ]
        }

        return self.create_card_response(card)

    def _list_lotteries(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """列出进行中的抽奖"""
        chat_id = self.get_chat_id(event)

        active_draws = [
            d for d in self.draws_data.get("draws", {}).values()
            if d["chat_id"] == chat_id and d["status"] == "active"
        ]

        if not active_draws:
            return self.create_text_response("📋 当前没有进行中的抽奖活动")

        text = f"📋 **进行中的抽奖** (共 {len(active_draws)} 个)\n\n"
        for draw in active_draws:
            text += f"• **{draw['prize_name']}**\n"
            text += f"  ID: `{draw['id']}`\n"
            text += f"  中奖人数: {draw['winner_count']}\n"
            text += f"  已参与: {len(draw['participants'])} 人\n\n"

        return self.create_text_response(text)

    def _show_lottery_info(self, event: Dict[str, Any], draw_id: str) -> Dict[str, Any]:
        """查看抽奖详情"""
        draw_info = self.draws_data.get("draws", {}).get(draw_id)

        if not draw_info:
            return self.create_text_response(f"❌ 抽奖活动不存在: {draw_id}")

        text = f"🎁 **抽奖详情**\n\n"
        text += f"**ID:** `{draw_info['id']}`\n"
        text += f"**奖品:** {draw_info['prize_name']}\n"
        text += f"**中奖人数:** {draw_info['winner_count']}\n"
        text += f"**参与人数:** {len(draw_info['participants'])}\n"
        text += f"**状态:** {'进行中' if draw_info['status'] == 'active' else '已结束'}\n"
        text += f"**创建时间:** {draw_info['created_at'][:19]}\n"

        if draw_info["status"] == "finished":
            text += f"**开奖时间:** {draw_info['finished_at'][:19]}\n"
            text += f"\n**中奖名单:**\n"
            for i, winner_id in enumerate(draw_info["winners"], 1):
                text += f"{i}. {winner_id}\n"

        return self.create_text_response(text)

    async def on_card_action(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理卡片交互"""
        action = event.get("action", {})
        value = action.get("value", {})

        if value.get("action") == "join_lottery":
            draw_id = value.get("draw_id")
            return self._join_lottery(event, draw_id)

        return None
