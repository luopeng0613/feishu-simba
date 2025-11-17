"""
生日提醒插件
记录团队成员生日，自动提醒即将到来的生日
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from plugins.base_plugin import BasePlugin
import threading
import time


class BirthdayReminderPlugin(BasePlugin):
    """生日提醒插件"""

    def __init__(self, bot):
        super().__init__(bot)
        self.data_file = os.path.join(bot.config.DATA_DIR, 'birthdays.json')
        self.birthday_data = self._load_data()
        self.check_timer = None

    @property
    def name(self) -> str:
        return "生日提醒"

    @property
    def description(self) -> str:
        return "记录团队成员生日，自动提醒即将到来的生日"

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
                "command": "/birthday add",
                "description": "添加生日记录",
                "usage": "/birthday add <姓名> <MM-DD>"
            },
            {
                "command": "/birthday list",
                "description": "查看生日列表",
                "usage": "/birthday list [月份]"
            },
            {
                "command": "/birthday today",
                "description": "查看今天的生日",
                "usage": "/birthday today"
            },
            {
                "command": "/birthday upcoming",
                "description": "查看即将到来的生日",
                "usage": "/birthday upcoming [天数]"
            },
            {
                "command": "/birthday remove",
                "description": "删除生日记录",
                "usage": "/birthday remove <姓名>"
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
                return {"birthdays": {}, "notified": []}
        return {"birthdays": {}, "notified": []}

    def _save_data(self):
        """保存数据"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.birthday_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存数据失败: {e}")

    def on_load(self):
        """插件加载时启动定时检查"""
        super().on_load()
        # 启动每日生日检查（每24小时检查一次）
        self._start_birthday_check()

    def on_unload(self):
        """插件卸载时停止定时器"""
        super().on_unload()
        if self.check_timer:
            self.check_timer.cancel()

    def _start_birthday_check(self):
        """启动定时检查"""
        # 每天早上9点检查生日
        self._check_birthdays()

        # 设置下次检查时间（24小时后）
        self.check_timer = threading.Timer(86400, self._start_birthday_check)
        self.check_timer.daemon = True
        self.check_timer.start()

    def _check_birthdays(self):
        """检查今天和即将到来的生日"""
        today = datetime.now()
        today_str = today.strftime("%m-%d")

        # 检查今天的生日
        for chat_id, birthdays in self.birthday_data.get("birthdays", {}).items():
            today_birthdays = [
                name for name, date in birthdays.items()
                if date == today_str
            ]

            if today_birthdays:
                # 发送今日生日提醒
                self._send_birthday_notification(chat_id, today_birthdays, 0)

        # 检查明天的生日（提前一天提醒）
        tomorrow = today + timedelta(days=1)
        tomorrow_str = tomorrow.strftime("%m-%d")

        for chat_id, birthdays in self.birthday_data.get("birthdays", {}).items():
            tomorrow_birthdays = [
                name for name, date in birthdays.items()
                if date == tomorrow_str
            ]

            if tomorrow_birthdays:
                self._send_birthday_notification(chat_id, tomorrow_birthdays, 1)

    def _send_birthday_notification(self, chat_id: str, names: List[str], days: int):
        """发送生日通知"""
        try:
            if days == 0:
                title = "🎂 今日生日提醒"
                content = f"今天是 **{', '.join(names)}** 的生日！\n让我们一起送上祝福吧！🎉"
                color = "red"
            else:
                title = "🎈 明日生日提醒"
                content = f"明天是 **{', '.join(names)}** 的生日！\n记得准备祝福哦！"
                color = "orange"

            card = {
                "config": {"wide_screen_mode": True},
                "header": {
                    "template": color,
                    "title": {"content": title, "tag": "plain_text"}
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {"content": content, "tag": "lark_md"}
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "note",
                        "elements": [
                            {
                                "tag": "plain_text",
                                "content": f"发送时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                            }
                        ]
                    }
                ]
            }

            self.bot.feishu_client.send_card_message(chat_id, card)
            self.logger.info(f"已发送生日提醒到群 {chat_id}: {names}")

        except Exception as e:
            self.logger.error(f"发送生日提醒失败: {e}", exc_info=True)

    async def on_message(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理消息"""
        text = self.get_message_text(event)

        if "生日" in text and self.extract_mentions(event):
            return self.create_text_response(
                "🎂 生日提醒功能\n\n"
                "使用 /birthday add <姓名> <MM-DD> 添加生日\n"
                "使用 /birthday list 查看生日列表\n"
                "使用 /birthday today 查看今日生日\n"
                "使用 /birthday upcoming 查看即将到来的生日"
            )

        return None

    def handle_command(self, command: str, args: List[str],
                      event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理命令"""
        if command != "birthday":
            return None

        if not args:
            return self.create_text_response(
                "请指定子命令: add/list/today/upcoming/remove"
            )

        sub_command = args[0].lower()

        if sub_command == "add":
            if len(args) < 3:
                return self.create_text_response(
                    "用法: /birthday add <姓名> <MM-DD>\n例如: /birthday add 张三 03-15"
                )
            name = args[1]
            date = args[2]
            return self._add_birthday(event, name, date)

        elif sub_command == "list":
            month = args[1] if len(args) > 1 else None
            return self._list_birthdays(event, month)

        elif sub_command == "today":
            return self._show_today_birthdays(event)

        elif sub_command == "upcoming":
            days = int(args[1]) if len(args) > 1 else 7
            return self._show_upcoming_birthdays(event, days)

        elif sub_command == "remove":
            if len(args) < 2:
                return self.create_text_response("用法: /birthday remove <姓名>")
            name = args[1]
            return self._remove_birthday(event, name)

        else:
            return self.create_text_response(f"未知子命令: {sub_command}")

    def _add_birthday(self, event: Dict[str, Any], name: str, date: str) -> Dict[str, Any]:
        """添加生日记录"""
        # 验证日期格式
        try:
            datetime.strptime(date, "%m-%d")
        except ValueError:
            return self.create_text_response(
                "❌ 日期格式错误，请使用 MM-DD 格式\n例如: 03-15"
            )

        chat_id = self.get_chat_id(event)

        # 初始化群组数据
        if chat_id not in self.birthday_data.setdefault("birthdays", {}):
            self.birthday_data["birthdays"][chat_id] = {}

        # 添加生日
        self.birthday_data["birthdays"][chat_id][name] = date
        self._save_data()

        return self.create_text_response(
            f"✅ 已添加生日记录\n姓名: {name}\n日期: {date}"
        )

    def _list_birthdays(self, event: Dict[str, Any], month: Optional[str] = None) -> Dict[str, Any]:
        """查看生日列表"""
        chat_id = self.get_chat_id(event)
        birthdays = self.birthday_data.get("birthdays", {}).get(chat_id, {})

        if not birthdays:
            return self.create_text_response("📋 暂无生日记录")

        # 过滤月份
        if month:
            try:
                month_num = int(month)
                if month_num < 1 or month_num > 12:
                    return self.create_text_response("❌ 月份必须在1-12之间")

                month_str = f"{month_num:02d}"
                birthdays = {
                    name: date for name, date in birthdays.items()
                    if date.startswith(month_str)
                }
            except ValueError:
                return self.create_text_response("❌ 月份必须是数字")

        if not birthdays:
            return self.create_text_response(f"📋 {month}月没有生日记录")

        # 按日期排序
        sorted_birthdays = sorted(birthdays.items(), key=lambda x: x[1])

        text = f"📋 **生日列表**"
        if month:
            text += f" ({month}月)"
        text += f" (共 {len(sorted_birthdays)} 人)\n\n"

        for name, date in sorted_birthdays:
            # 计算距离生日的天数
            today = datetime.now()
            birthday_this_year = datetime.strptime(f"{today.year}-{date}", "%Y-%m-%d")

            if birthday_this_year < today:
                birthday_this_year = datetime.strptime(f"{today.year + 1}-{date}", "%Y-%m-%d")

            days_left = (birthday_this_year - today).days

            if days_left == 0:
                days_text = "🎂 今天"
            elif days_left == 1:
                days_text = "🎈 明天"
            else:
                days_text = f"还有 {days_left} 天"

            text += f"• {name}: {date} ({days_text})\n"

        return self.create_text_response(text)

    def _show_today_birthdays(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """查看今日生日"""
        chat_id = self.get_chat_id(event)
        birthdays = self.birthday_data.get("birthdays", {}).get(chat_id, {})

        today = datetime.now().strftime("%m-%d")
        today_birthdays = [name for name, date in birthdays.items() if date == today]

        if not today_birthdays:
            return self.create_text_response("🎂 今天没有人过生日")

        text = "🎂 **今日寿星**\n\n"
        for name in today_birthdays:
            text += f"🎉 {name}\n"

        text += "\n祝生日快乐！Happy Birthday! 🎊"

        return self.create_text_response(text)

    def _show_upcoming_birthdays(self, event: Dict[str, Any], days: int) -> Dict[str, Any]:
        """查看即将到来的生日"""
        chat_id = self.get_chat_id(event)
        birthdays = self.birthday_data.get("birthdays", {}).get(chat_id, {})

        if not birthdays:
            return self.create_text_response("📋 暂无生日记录")

        today = datetime.now()
        upcoming = []

        for name, date in birthdays.items():
            birthday_this_year = datetime.strptime(f"{today.year}-{date}", "%Y-%m-%d")

            if birthday_this_year < today:
                birthday_this_year = datetime.strptime(f"{today.year + 1}-{date}", "%Y-%m-%d")

            days_left = (birthday_this_year - today).days

            if 0 <= days_left <= days:
                upcoming.append((name, date, days_left))

        if not upcoming:
            return self.create_text_response(f"📅 未来{days}天内没有生日")

        # 按天数排序
        upcoming.sort(key=lambda x: x[2])

        text = f"📅 **未来{days}天的生日** (共 {len(upcoming)} 人)\n\n"
        for name, date, days_left in upcoming:
            if days_left == 0:
                text += f"🎂 {name}: {date} (今天)\n"
            elif days_left == 1:
                text += f"🎈 {name}: {date} (明天)\n"
            else:
                text += f"• {name}: {date} (还有{days_left}天)\n"

        return self.create_text_response(text)

    def _remove_birthday(self, event: Dict[str, Any], name: str) -> Dict[str, Any]:
        """删除生日记录"""
        chat_id = self.get_chat_id(event)
        birthdays = self.birthday_data.get("birthdays", {}).get(chat_id, {})

        if name not in birthdays:
            return self.create_text_response(f"❌ 未找到 {name} 的生日记录")

        date = birthdays[name]
        del birthdays[name]
        self._save_data()

        return self.create_text_response(
            f"✅ 已删除生日记录\n姓名: {name}\n日期: {date}"
        )
