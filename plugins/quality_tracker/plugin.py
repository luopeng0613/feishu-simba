"""
项目质量跟踪插件
记录代码质量指标、Bug统计、代码审查等
"""
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from plugins.base_plugin import BasePlugin


class QualityTrackerPlugin(BasePlugin):
    """项目质量跟踪插件"""

    def __init__(self, bot):
        super().__init__(bot)
        self.data_file = os.path.join(bot.config.DATA_DIR, 'quality_tracker.json')
        self.quality_data = self._load_data()

    @property
    def name(self) -> str:
        return "项目质量跟踪"

    @property
    def description(self) -> str:
        return "跟踪项目质量指标，包括Bug统计、代码审查、测试覆盖率等"

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
                "command": "/quality bug",
                "description": "记录Bug",
                "usage": "/quality bug add <严重程度> <描述>"
            },
            {
                "command": "/quality bug list",
                "description": "查看Bug列表",
                "usage": "/quality bug list [状态]"
            },
            {
                "command": "/quality bug close",
                "description": "关闭Bug",
                "usage": "/quality bug close <Bug ID>"
            },
            {
                "command": "/quality report",
                "description": "生成质量报告",
                "usage": "/quality report [week/month]"
            },
            {
                "command": "/quality metrics",
                "description": "查看质量指标",
                "usage": "/quality metrics"
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
                return {"bugs": [], "reviews": [], "metrics": {}}
        return {"bugs": [], "reviews": [], "metrics": {}}

    def _save_data(self):
        """保存数据"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.quality_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存数据失败: {e}")

    async def on_message(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理消息"""
        text = self.get_message_text(event)

        if "质量" in text or "bug" in text.lower() or "代码审查" in text:
            if self.extract_mentions(event):
                return self.create_text_response(
                    "📊 项目质量跟踪功能\n\n"
                    "使用 /quality bug add <级别> <描述> 记录Bug\n"
                    "使用 /quality bug list 查看Bug列表\n"
                    "使用 /quality report 生成质量报告\n"
                    "使用 /quality metrics 查看质量指标"
                )

        return None

    def handle_command(self, command: str, args: List[str],
                      event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理命令"""
        if command != "quality":
            return None

        if not args:
            return self.create_text_response(
                "请指定子命令: bug/report/metrics"
            )

        sub_command = args[0].lower()

        if sub_command == "bug":
            return self._handle_bug_command(event, args[1:])
        elif sub_command == "report":
            period = args[1] if len(args) > 1 else "week"
            return self._generate_report(event, period)
        elif sub_command == "metrics":
            return self._show_metrics(event)
        else:
            return self.create_text_response(f"未知子命令: {sub_command}")

    def _handle_bug_command(self, event: Dict[str, Any], args: List[str]) -> Dict[str, Any]:
        """处理Bug相关命令"""
        if not args:
            return self.create_text_response(
                "请指定操作: add/list/close"
            )

        action = args[0].lower()

        if action == "add":
            if len(args) < 3:
                return self.create_text_response(
                    "用法: /quality bug add <严重程度:critical/high/medium/low> <描述>"
                )
            severity = args[1].lower()
            description = " ".join(args[2:])
            return self._add_bug(event, severity, description)

        elif action == "list":
            status = args[1] if len(args) > 1 else "open"
            return self._list_bugs(event, status)

        elif action == "close":
            if len(args) < 2:
                return self.create_text_response("用法: /quality bug close <Bug ID>")
            bug_id = args[1]
            return self._close_bug(event, bug_id)

        else:
            return self.create_text_response(f"未知操作: {action}")

    def _add_bug(self, event: Dict[str, Any], severity: str, description: str) -> Dict[str, Any]:
        """添加Bug记录"""
        valid_severities = ["critical", "high", "medium", "low"]
        if severity not in valid_severities:
            return self.create_text_response(
                f"❌ 无效的严重程度，请使用: {', '.join(valid_severities)}"
            )

        sender = self.get_sender_info(event)
        chat_id = self.get_chat_id(event)

        # 生成Bug ID
        bug_id = f"BUG-{len(self.quality_data.get('bugs', [])) + 1:04d}"

        bug_info = {
            "id": bug_id,
            "severity": severity,
            "description": description,
            "reporter": sender["sender_id"],
            "chat_id": chat_id,
            "status": "open",
            "created_at": datetime.now().isoformat(),
            "closed_at": None
        }

        self.quality_data.setdefault("bugs", []).append(bug_info)
        self._save_data()

        # 根据严重程度选择颜色
        severity_colors = {
            "critical": "red",
            "high": "orange",
            "medium": "yellow",
            "low": "blue"
        }

        severity_labels = {
            "critical": "🔴 严重",
            "high": "🟠 高",
            "medium": "🟡 中",
            "low": "🔵 低"
        }

        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "template": severity_colors.get(severity, "blue"),
                "title": {
                    "content": f"🐛 新Bug记录",
                    "tag": "plain_text"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": f"**Bug ID:** `{bug_id}`\n**严重程度:** {severity_labels.get(severity, severity)}\n**描述:** {description}",
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
                            "content": f"状态: 待修复 | 创建时间: {bug_info['created_at'][:19]}"
                        }
                    ]
                }
            ]
        }

        return self.create_card_response(card)

    def _list_bugs(self, event: Dict[str, Any], status: str) -> Dict[str, Any]:
        """查看Bug列表"""
        chat_id = self.get_chat_id(event)
        bugs = self.quality_data.get("bugs", [])

        # 过滤当前群的Bug
        chat_bugs = [b for b in bugs if b.get("chat_id") == chat_id]

        if status != "all":
            chat_bugs = [b for b in chat_bugs if b.get("status") == status]

        if not chat_bugs:
            return self.create_text_response(f"📋 暂无{status}状态的Bug")

        # 按严重程度分组
        severity_order = ["critical", "high", "medium", "low"]
        grouped = {s: [] for s in severity_order}

        for bug in chat_bugs:
            severity = bug.get("severity", "low")
            if severity in grouped:
                grouped[severity].append(bug)

        text = f"🐛 **Bug列表** (状态: {status})\n\n"

        severity_labels = {
            "critical": "🔴 严重",
            "high": "🟠 高",
            "medium": "🟡 中",
            "low": "🔵 低"
        }

        for severity in severity_order:
            bugs_in_severity = grouped[severity]
            if bugs_in_severity:
                text += f"\n**{severity_labels[severity]}** ({len(bugs_in_severity)}个)\n"
                for bug in bugs_in_severity[:5]:  # 只显示前5个
                    text += f"• `{bug['id']}` - {bug['description'][:30]}...\n"

                if len(bugs_in_severity) > 5:
                    text += f"  ... 还有 {len(bugs_in_severity) - 5} 个\n"

        return self.create_text_response(text)

    def _close_bug(self, event: Dict[str, Any], bug_id: str) -> Dict[str, Any]:
        """关闭Bug"""
        bugs = self.quality_data.get("bugs", [])

        for bug in bugs:
            if bug.get("id") == bug_id:
                if bug.get("status") == "closed":
                    return self.create_text_response("⚠️ 该Bug已经关闭")

                bug["status"] = "closed"
                bug["closed_at"] = datetime.now().isoformat()
                self._save_data()

                return self.create_text_response(
                    f"✅ Bug {bug_id} 已关闭\n描述: {bug['description']}"
                )

        return self.create_text_response(f"❌ Bug不存在: {bug_id}")

    def _generate_report(self, event: Dict[str, Any], period: str) -> Dict[str, Any]:
        """生成质量报告"""
        chat_id = self.get_chat_id(event)
        bugs = self.quality_data.get("bugs", [])

        # 计算时间范围
        now = datetime.now()
        if period == "week":
            start_date = now - timedelta(days=7)
            period_label = "本周"
        elif period == "month":
            start_date = now - timedelta(days=30)
            period_label = "本月"
        else:
            start_date = now - timedelta(days=7)
            period_label = "本周"

        # 过滤时间范围内的Bug
        chat_bugs = [
            b for b in bugs
            if b.get("chat_id") == chat_id
            and datetime.fromisoformat(b.get("created_at", "")) >= start_date
        ]

        total_bugs = len(chat_bugs)
        open_bugs = len([b for b in chat_bugs if b.get("status") == "open"])
        closed_bugs = len([b for b in chat_bugs if b.get("status") == "closed"])

        # 按严重程度统计
        severity_stats = {}
        for bug in chat_bugs:
            severity = bug.get("severity", "low")
            severity_stats[severity] = severity_stats.get(severity, 0) + 1

        # 计算解决率
        fix_rate = (closed_bugs / total_bugs * 100) if total_bugs > 0 else 0

        text = f"📊 **{period_label}质量报告**\n\n"
        text += f"**Bug统计:**\n"
        text += f"• 总数: {total_bugs}\n"
        text += f"• 待修复: {open_bugs}\n"
        text += f"• 已修复: {closed_bugs}\n"
        text += f"• 修复率: {fix_rate:.1f}%\n\n"

        if severity_stats:
            text += f"**严重程度分布:**\n"
            severity_labels = {
                "critical": "🔴 严重",
                "high": "🟠 高",
                "medium": "🟡 中",
                "low": "🔵 低"
            }
            for severity, count in severity_stats.items():
                text += f"• {severity_labels.get(severity, severity)}: {count}\n"

        # 质量评分（简单算法）
        if total_bugs == 0:
            score = 100
        else:
            # 基础分100，每个open bug扣分
            critical_count = len([b for b in chat_bugs if b.get("severity") == "critical" and b.get("status") == "open"])
            high_count = len([b for b in chat_bugs if b.get("severity") == "high" and b.get("status") == "open"])
            medium_count = len([b for b in chat_bugs if b.get("severity") == "medium" and b.get("status") == "open"])
            low_count = len([b for b in chat_bugs if b.get("severity") == "low" and b.get("status") == "open"])

            score = max(0, 100 - critical_count * 20 - high_count * 10 - medium_count * 5 - low_count * 2)

        text += f"\n**质量评分:** {score}/100"

        if score >= 90:
            text += " 🌟 优秀"
        elif score >= 70:
            text += " 👍 良好"
        elif score >= 50:
            text += " ⚠️ 需改进"
        else:
            text += " 🚨 较差"

        return self.create_text_response(text)

    def _show_metrics(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """显示质量指标"""
        chat_id = self.get_chat_id(event)
        bugs = self.quality_data.get("bugs", [])

        # 过滤当前群的Bug
        chat_bugs = [b for b in bugs if b.get("chat_id") == chat_id]

        total_bugs = len(chat_bugs)
        open_bugs = len([b for b in chat_bugs if b.get("status") == "open"])
        closed_bugs = len([b for b in chat_bugs if b.get("status") == "closed"])

        # 计算平均修复时间
        fix_times = []
        for bug in chat_bugs:
            if bug.get("status") == "closed" and bug.get("closed_at"):
                created = datetime.fromisoformat(bug.get("created_at"))
                closed = datetime.fromisoformat(bug.get("closed_at"))
                fix_time = (closed - created).total_seconds() / 3600  # 转为小时
                fix_times.append(fix_time)

        avg_fix_time = sum(fix_times) / len(fix_times) if fix_times else 0

        text = "📈 **质量指标总览**\n\n"
        text += f"**Bug总数:** {total_bugs}\n"
        text += f"**待修复:** {open_bugs}\n"
        text += f"**已修复:** {closed_bugs}\n"
        text += f"**平均修复时间:** {avg_fix_time:.1f} 小时\n"

        return self.create_text_response(text)

    async def on_card_action(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理卡片交互"""
        action = event.get("action", {})
        value = action.get("value", {})

        if value.get("action") == "close_bug":
            bug_id = value.get("bug_id")
            return self._close_bug(event, bug_id)

        return None
