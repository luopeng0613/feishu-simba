"""
代码统计插件
统计Git代码提交情况，生成代码贡献报告
"""
import json
import os
import subprocess
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from plugins.base_plugin import BasePlugin
from collections import defaultdict


class CodeStatsPlugin(BasePlugin):
    """代码统计插件"""

    def __init__(self, bot):
        super().__init__(bot)
        self.data_file = os.path.join(bot.config.DATA_DIR, 'code_stats.json')
        self.stats_data = self._load_data()

    @property
    def name(self) -> str:
        return "代码统计"

    @property
    def description(self) -> str:
        return "统计Git代码提交情况，生成代码贡献报告"

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
                "command": "/code repo",
                "description": "设置Git仓库路径",
                "usage": "/code repo <路径>"
            },
            {
                "command": "/code stats",
                "description": "查看代码统计",
                "usage": "/code stats [week/month/all]"
            },
            {
                "command": "/code ranking",
                "description": "查看提交排行榜",
                "usage": "/code ranking [week/month/all]"
            },
            {
                "command": "/code user",
                "description": "查看指定用户的统计",
                "usage": "/code user <用户名>"
            },
            {
                "command": "/code report",
                "description": "生成代码周报/月报",
                "usage": "/code report [week/month]"
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
                return {"repos": {}}
        return {"repos": {}}

    def _save_data(self):
        """保存数据"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存数据失败: {e}")

    async def on_message(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理消息"""
        text = self.get_message_text(event)

        if "代码统计" in text or "代码贡献" in text:
            if self.extract_mentions(event):
                return self.create_text_response(
                    "📊 代码统计功能\n\n"
                    "使用 /code repo <路径> 设置仓库路径\n"
                    "使用 /code stats 查看代码统计\n"
                    "使用 /code ranking 查看提交排行榜\n"
                    "使用 /code report 生成周报/月报"
                )

        return None

    def handle_command(self, command: str, args: List[str],
                      event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理命令"""
        if command != "code":
            return None

        if not args:
            return self.create_text_response(
                "请指定子命令: repo/stats/ranking/user/report"
            )

        sub_command = args[0].lower()

        if sub_command == "repo":
            if len(args) < 2:
                return self.create_text_response("用法: /code repo <仓库路径>")
            repo_path = args[1]
            return self._set_repo(event, repo_path)

        elif sub_command == "stats":
            period = args[1] if len(args) > 1 else "week"
            return self._show_stats(event, period)

        elif sub_command == "ranking":
            period = args[1] if len(args) > 1 else "week"
            return self._show_ranking(event, period)

        elif sub_command == "user":
            if len(args) < 2:
                return self.create_text_response("用法: /code user <用户名>")
            username = args[1]
            return self._show_user_stats(event, username)

        elif sub_command == "report":
            period = args[1] if len(args) > 1 else "week"
            return self._generate_report(event, period)

        else:
            return self.create_text_response(f"未知子命令: {sub_command}")

    def _set_repo(self, event: Dict[str, Any], repo_path: str) -> Dict[str, Any]:
        """设置Git仓库路径"""
        # 检查路径是否存在
        if not os.path.exists(repo_path):
            return self.create_text_response(f"❌ 路径不存在: {repo_path}")

        # 检查是否是Git仓库
        git_dir = os.path.join(repo_path, '.git')
        if not os.path.exists(git_dir):
            return self.create_text_response(f"❌ 不是有效的Git仓库: {repo_path}")

        chat_id = self.get_chat_id(event)
        self.stats_data.setdefault("repos", {})[chat_id] = repo_path
        self._save_data()

        return self.create_text_response(
            f"✅ 已设置Git仓库路径\n路径: {repo_path}"
        )

    def _get_git_log(self, repo_path: str, since: str = None, author: str = None) -> List[Dict]:
        """获取Git提交日志"""
        try:
            cmd = ['git', '-C', repo_path, 'log', '--pretty=format:%H|%an|%ae|%ad|%s', '--date=iso']

            if since:
                cmd.append(f'--since={since}')

            if author:
                cmd.append(f'--author={author}')

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                self.logger.error(f"Git命令执行失败: {result.stderr}")
                return []

            commits = []
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue

                parts = line.split('|')
                if len(parts) >= 5:
                    commits.append({
                        'hash': parts[0],
                        'author': parts[1],
                        'email': parts[2],
                        'date': parts[3],
                        'message': '|'.join(parts[4:])
                    })

            return commits

        except subprocess.TimeoutExpired:
            self.logger.error("Git命令超时")
            return []
        except Exception as e:
            self.logger.error(f"获取Git日志失败: {e}", exc_info=True)
            return []

    def _get_git_stats(self, repo_path: str, since: str = None) -> Dict:
        """获取Git统计数据"""
        try:
            cmd = ['git', '-C', repo_path, 'log', '--shortstat', '--pretty=format:%an']

            if since:
                cmd.append(f'--since={since}')

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode != 0:
                return {}

            stats = defaultdict(lambda: {'commits': 0, 'insertions': 0, 'deletions': 0})
            current_author = None

            for line in result.stdout.strip().split('\n'):
                line = line.strip()
                if not line:
                    continue

                # 作者行
                if 'files changed' not in line:
                    current_author = line
                    stats[current_author]['commits'] += 1
                # 统计行
                else:
                    if current_author:
                        # 解析统计数据
                        if 'insertion' in line:
                            insertions = int(line.split('insertion')[0].split(',')[-1].strip().split()[-1])
                            stats[current_author]['insertions'] += insertions

                        if 'deletion' in line:
                            deletions = int(line.split('deletion')[0].split(',')[-1].strip().split()[-1])
                            stats[current_author]['deletions'] += deletions

            return dict(stats)

        except Exception as e:
            self.logger.error(f"获取Git统计失败: {e}", exc_info=True)
            return {}

    def _show_stats(self, event: Dict[str, Any], period: str) -> Dict[str, Any]:
        """显示代码统计"""
        chat_id = self.get_chat_id(event)
        repo_path = self.stats_data.get("repos", {}).get(chat_id)

        if not repo_path:
            return self.create_text_response(
                "❌ 未设置Git仓库路径\n请使用 /code repo <路径> 设置"
            )

        # 计算时间范围
        since = self._get_time_range(period)

        # 获取统计数据
        stats = self._get_git_stats(repo_path, since)

        if not stats:
            return self.create_text_response(f"📊 {period}期间暂无提交记录")

        # 计算总计
        total_commits = sum(s['commits'] for s in stats.values())
        total_insertions = sum(s['insertions'] for s in stats.values())
        total_deletions = sum(s['deletions'] for s in stats.values())
        total_contributors = len(stats)

        period_labels = {
            'week': '本周',
            'month': '本月',
            'all': '全部'
        }

        text = f"📊 **代码统计** ({period_labels.get(period, period)})\n\n"
        text += f"**总体数据:**\n"
        text += f"• 提交次数: {total_commits}\n"
        text += f"• 新增代码: +{total_insertions} 行\n"
        text += f"• 删除代码: -{total_deletions} 行\n"
        text += f"• 贡献者: {total_contributors} 人\n\n"

        text += f"**活跃贡献者 TOP5:**\n"
        sorted_stats = sorted(stats.items(), key=lambda x: x[1]['commits'], reverse=True)
        for i, (author, data) in enumerate(sorted_stats[:5], 1):
            text += f"{i}. {author}: {data['commits']} 次提交\n"

        return self.create_text_response(text)

    def _show_ranking(self, event: Dict[str, Any], period: str) -> Dict[str, Any]:
        """显示提交排行榜"""
        chat_id = self.get_chat_id(event)
        repo_path = self.stats_data.get("repos", {}).get(chat_id)

        if not repo_path:
            return self.create_text_response(
                "❌ 未设置Git仓库路径\n请使用 /code repo <路径> 设置"
            )

        since = self._get_time_range(period)
        stats = self._get_git_stats(repo_path, since)

        if not stats:
            return self.create_text_response(f"📊 {period}期间暂无提交记录")

        period_labels = {
            'week': '本周',
            'month': '本月',
            'all': '全部时间'
        }

        # 按提交次数排序
        sorted_by_commits = sorted(stats.items(), key=lambda x: x[1]['commits'], reverse=True)

        text = f"🏆 **提交排行榜** ({period_labels.get(period, period)})\n\n"

        for i, (author, data) in enumerate(sorted_by_commits[:10], 1):
            medal = ""
            if i == 1:
                medal = "🥇 "
            elif i == 2:
                medal = "🥈 "
            elif i == 3:
                medal = "🥉 "

            text += f"{medal}{i}. **{author}**\n"
            text += f"   提交: {data['commits']} 次"
            text += f" | +{data['insertions']} / -{data['deletions']} 行\n"

        return self.create_text_response(text)

    def _show_user_stats(self, event: Dict[str, Any], username: str) -> Dict[str, Any]:
        """显示指定用户的统计"""
        chat_id = self.get_chat_id(event)
        repo_path = self.stats_data.get("repos", {}).get(chat_id)

        if not repo_path:
            return self.create_text_response(
                "❌ 未设置Git仓库路径\n请使用 /code repo <路径> 设置"
            )

        # 获取用户的所有提交
        commits = self._get_git_log(repo_path, author=username)

        if not commits:
            return self.create_text_response(f"❌ 未找到用户 {username} 的提交记录")

        # 获取用户统计
        stats = self._get_git_stats(repo_path)
        user_stats = stats.get(username, {})

        text = f"👤 **{username} 的代码统计**\n\n"
        text += f"**总体数据:**\n"
        text += f"• 总提交: {user_stats.get('commits', 0)} 次\n"
        text += f"• 新增代码: +{user_stats.get('insertions', 0)} 行\n"
        text += f"• 删除代码: -{user_stats.get('deletions', 0)} 行\n\n"

        text += f"**最近提交** (最多显示5条):\n"
        for commit in commits[:5]:
            date = commit['date'][:10]
            message = commit['message'][:40]
            text += f"• {date}: {message}...\n"

        return self.create_text_response(text)

    def _generate_report(self, event: Dict[str, Any], period: str) -> Dict[str, Any]:
        """生成代码报告"""
        chat_id = self.get_chat_id(event)
        repo_path = self.stats_data.get("repos", {}).get(chat_id)

        if not repo_path:
            return self.create_text_response(
                "❌ 未设置Git仓库路径\n请使用 /code repo <路径> 设置"
            )

        since = self._get_time_range(period)
        stats = self._get_git_stats(repo_path, since)
        commits = self._get_git_log(repo_path, since)

        if not stats:
            return self.create_text_response(f"📊 {period}期间暂无提交记录")

        period_labels = {
            'week': '周报',
            'month': '月报'
        }

        # 计算总计
        total_commits = sum(s['commits'] for s in stats.values())
        total_insertions = sum(s['insertions'] for s in stats.values())
        total_deletions = sum(s['deletions'] for s in stats.values())

        # 创建卡片
        card = {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "blue",
                "title": {
                    "content": f"📊 代码{period_labels.get(period, '报告')}",
                    "tag": "plain_text"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": f"**统计周期:** {self._get_period_text(period)}\n"
                                   f"**总提交数:** {total_commits}\n"
                                   f"**代码变更:** +{total_insertions} / -{total_deletions} 行\n"
                                   f"**贡献者:** {len(stats)} 人",
                        "tag": "lark_md"
                    }
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {
                        "content": "**🏆 贡献排行:**",
                        "tag": "lark_md"
                    }
                }
            ]
        }

        # 添加排行榜
        sorted_stats = sorted(stats.items(), key=lambda x: x[1]['commits'], reverse=True)
        ranking_text = ""
        for i, (author, data) in enumerate(sorted_stats[:5], 1):
            medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i - 1]
            ranking_text += f"{medal} {author}: {data['commits']}次提交\n"

        card["elements"].append({
            "tag": "div",
            "text": {
                "content": ranking_text,
                "tag": "lark_md"
            }
        })

        # 添加备注
        card["elements"].extend([
            {
                "tag": "hr"
            },
            {
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                    }
                ]
            }
        ])

        return self.create_card_response(card)

    def _get_time_range(self, period: str) -> Optional[str]:
        """获取时间范围"""
        now = datetime.now()

        if period == "week":
            since = now - timedelta(days=7)
            return since.strftime("%Y-%m-%d")
        elif period == "month":
            since = now - timedelta(days=30)
            return since.strftime("%Y-%m-%d")
        elif period == "all":
            return None
        else:
            return None

    def _get_period_text(self, period: str) -> str:
        """获取周期文本"""
        now = datetime.now()

        if period == "week":
            since = now - timedelta(days=7)
            return f"{since.strftime('%Y-%m-%d')} ~ {now.strftime('%Y-%m-%d')}"
        elif period == "month":
            since = now - timedelta(days=30)
            return f"{since.strftime('%Y-%m-%d')} ~ {now.strftime('%Y-%m-%d')}"
        else:
            return "全部时间"
