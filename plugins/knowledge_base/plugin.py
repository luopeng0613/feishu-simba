"""
知识库问答插件
团队知识管理，支持添加、搜索、问答知识条目
"""
import json
import os
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
from plugins.base_plugin import BasePlugin


class KnowledgeBasePlugin(BasePlugin):
    """知识库问答插件"""

    def __init__(self, bot):
        super().__init__(bot)
        self.data_file = os.path.join(bot.config.DATA_DIR, 'knowledge_base.json')
        self.kb_data = self._load_data()

    @property
    def name(self) -> str:
        return "知识库问答"

    @property
    def description(self) -> str:
        return "团队知识管理，支持添加、搜索、问答知识条目"

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
                "command": "/kb add",
                "description": "添加知识条目",
                "usage": "/kb add <问题> | <答案>"
            },
            {
                "command": "/kb search",
                "description": "搜索知识库",
                "usage": "/kb search <关键词>"
            },
            {
                "command": "/kb list",
                "description": "查看知识列表",
                "usage": "/kb list [分类]"
            },
            {
                "command": "/kb update",
                "description": "更新知识条目",
                "usage": "/kb update <ID> | <新答案>"
            },
            {
                "command": "/kb delete",
                "description": "删除知识条目",
                "usage": "/kb delete <ID>"
            },
            {
                "command": "/kb category",
                "description": "设置知识分类",
                "usage": "/kb category <ID> <分类>"
            },
            {
                "command": "/kb faq",
                "description": "查看常见问题",
                "usage": "/kb faq"
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
                return {"knowledge": {}, "next_id": 1}
        return {"knowledge": {}, "next_id": 1}

    def _save_data(self):
        """保存数据"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.kb_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存数据失败: {e}")

    async def on_message(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理消息"""
        text = self.get_message_text(event)

        # 如果被@且包含问号，尝试搜索知识库
        if self.extract_mentions(event):
            if "？" in text or "?" in text:
                # 移除@标记
                clean_text = re.sub(r'@\w+\s*', '', text).strip()
                clean_text = clean_text.replace("？", "").replace("?", "").strip()

                if clean_text:
                    # 搜索知识库
                    results = self._search_knowledge(clean_text)

                    if results:
                        # 返回最相关的答案
                        best_match = results[0]
                        response = f"💡 **{best_match['question']}**\n\n{best_match['answer']}"

                        if len(results) > 1:
                            response += f"\n\n_找到 {len(results)} 个相关结果，使用 /kb search {clean_text[:10]} 查看更多_"

                        return self.create_text_response(response)
                    else:
                        return self.create_text_response(
                            f"🤔 抱歉，没有找到关于「{clean_text}」的知识。\n"
                            f"您可以使用 /kb add <问题> | <答案> 添加新知识。"
                        )

            # 帮助信息
            if "知识" in text or "kb" in text.lower():
                return self.create_text_response(
                    "📚 知识库功能\n\n"
                    "使用 /kb add <问题> | <答案> 添加知识\n"
                    "使用 /kb search <关键词> 搜索知识\n"
                    "使用 /kb list 查看知识列表\n"
                    "使用 /kb faq 查看常见问题\n\n"
                    "💡 提示：@我并提问，我会自动搜索知识库"
                )

        return None

    def handle_command(self, command: str, args: List[str],
                      event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理命令"""
        if command != "kb":
            return None

        if not args:
            return self.create_text_response(
                "请指定子命令: add/search/list/update/delete/category/faq"
            )

        sub_command = args[0].lower()

        if sub_command == "add":
            # 获取完整的命令文本
            text = self.get_message_text(event)
            # 提取 /kb add 之后的内容
            content = text[len("/kb add"):].strip()

            if not content or '|' not in content:
                return self.create_text_response(
                    "用法: /kb add <问题> | <答案>\n"
                    "例如: /kb add 如何部署项目? | 使用docker-compose up -d命令部署"
                )

            parts = content.split('|', 1)
            question = parts[0].strip()
            answer = parts[1].strip()

            return self._add_knowledge(event, question, answer)

        elif sub_command == "search":
            if len(args) < 2:
                return self.create_text_response("用法: /kb search <关键词>")
            keyword = " ".join(args[1:])
            return self._search_and_display(event, keyword)

        elif sub_command == "list":
            category = args[1] if len(args) > 1 else None
            return self._list_knowledge(event, category)

        elif sub_command == "update":
            text = self.get_message_text(event)
            content = text[len("/kb update"):].strip()

            if not content or '|' not in content:
                return self.create_text_response(
                    "用法: /kb update <ID> | <新答案>"
                )

            parts = content.split('|', 1)
            try:
                kb_id = int(parts[0].strip())
            except ValueError:
                return self.create_text_response("❌ ID必须是数字")

            new_answer = parts[1].strip()
            return self._update_knowledge(event, kb_id, new_answer)

        elif sub_command == "delete":
            if len(args) < 2:
                return self.create_text_response("用法: /kb delete <ID>")

            try:
                kb_id = int(args[1])
            except ValueError:
                return self.create_text_response("❌ ID必须是数字")

            return self._delete_knowledge(event, kb_id)

        elif sub_command == "category":
            if len(args) < 3:
                return self.create_text_response("用法: /kb category <ID> <分类>")

            try:
                kb_id = int(args[1])
            except ValueError:
                return self.create_text_response("❌ ID必须是数字")

            category = args[2]
            return self._set_category(event, kb_id, category)

        elif sub_command == "faq":
            return self._show_faq(event)

        else:
            return self.create_text_response(f"未知子命令: {sub_command}")

    def _add_knowledge(self, event: Dict[str, Any], question: str, answer: str) -> Dict[str, Any]:
        """添加知识条目"""
        chat_id = self.get_chat_id(event)
        sender = self.get_sender_info(event)

        # 生成ID
        kb_id = self.kb_data.get("next_id", 1)
        self.kb_data["next_id"] = kb_id + 1

        # 创建知识条目
        knowledge_item = {
            "id": kb_id,
            "chat_id": chat_id,
            "question": question,
            "answer": answer,
            "category": "通用",
            "creator": sender["sender_id"],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "view_count": 0
        }

        self.kb_data.setdefault("knowledge", {})[str(kb_id)] = knowledge_item
        self._save_data()

        card = {
            "config": {"wide_screen_mode": True},
            "header": {
                "template": "green",
                "title": {
                    "content": "✅ 知识添加成功",
                    "tag": "plain_text"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "content": f"**ID:** {kb_id}\n**问题:** {question}\n**答案:** {answer[:100]}...",
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
                            "content": f"分类: 通用 | 使用 /kb category {kb_id} <分类> 可以设置分类"
                        }
                    ]
                }
            ]
        }

        return self.create_card_response(card)

    def _search_knowledge(self, keyword: str) -> List[Dict]:
        """搜索知识库"""
        keyword_lower = keyword.lower()
        results = []

        for kb_id, item in self.kb_data.get("knowledge", {}).items():
            question_lower = item["question"].lower()
            answer_lower = item["answer"].lower()

            # 计算匹配度
            score = 0

            # 完全匹配问题
            if keyword_lower == question_lower:
                score += 100

            # 问题包含关键词
            if keyword_lower in question_lower:
                score += 50

            # 答案包含关键词
            if keyword_lower in answer_lower:
                score += 20

            # 分词匹配（简单实现）
            keywords = keyword_lower.split()
            for kw in keywords:
                if kw in question_lower:
                    score += 10
                if kw in answer_lower:
                    score += 5

            if score > 0:
                item_copy = item.copy()
                item_copy["score"] = score
                results.append(item_copy)

        # 按匹配度排序
        results.sort(key=lambda x: x["score"], reverse=True)

        return results

    def _search_and_display(self, event: Dict[str, Any], keyword: str) -> Dict[str, Any]:
        """搜索并显示知识"""
        results = self._search_knowledge(keyword)

        if not results:
            return self.create_text_response(
                f"🔍 未找到关于「{keyword}」的知识\n"
                f"使用 /kb add <问题> | <答案> 添加新知识"
            )

        # 更新浏览次数
        for item in results[:3]:
            kb_id = str(item["id"])
            if kb_id in self.kb_data.get("knowledge", {}):
                self.kb_data["knowledge"][kb_id]["view_count"] += 1
        self._save_data()

        text = f"🔍 **搜索结果** (找到 {len(results)} 条)\n\n"

        for i, item in enumerate(results[:5], 1):
            text += f"**{i}. {item['question']}** (ID: {item['id']})\n"
            answer = item['answer'][:100]
            if len(item['answer']) > 100:
                answer += "..."
            text += f"{answer}\n"
            text += f"_分类: {item['category']} | 浏览: {item['view_count']}次_\n\n"

        if len(results) > 5:
            text += f"_... 还有 {len(results) - 5} 条结果_"

        return self.create_text_response(text)

    def _list_knowledge(self, event: Dict[str, Any], category: Optional[str] = None) -> Dict[str, Any]:
        """查看知识列表"""
        chat_id = self.get_chat_id(event)

        # 过滤当前群的知识
        knowledge_list = [
            item for item in self.kb_data.get("knowledge", {}).values()
            if item.get("chat_id") == chat_id
        ]

        # 过滤分类
        if category:
            knowledge_list = [
                item for item in knowledge_list
                if item.get("category") == category
            ]

        if not knowledge_list:
            if category:
                return self.create_text_response(f"📚 「{category}」分类下暂无知识")
            else:
                return self.create_text_response("📚 知识库为空")

        # 按分类分组
        categories = {}
        for item in knowledge_list:
            cat = item.get("category", "通用")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)

        text = f"📚 **知识库列表** (共 {len(knowledge_list)} 条)\n\n"

        for cat, items in sorted(categories.items()):
            text += f"**📁 {cat}** ({len(items)}条)\n"
            for item in items[:5]:
                text += f"• [{item['id']}] {item['question'][:30]}...\n"

            if len(items) > 5:
                text += f"  _... 还有 {len(items) - 5} 条_\n"
            text += "\n"

        return self.create_text_response(text)

    def _update_knowledge(self, event: Dict[str, Any], kb_id: int, new_answer: str) -> Dict[str, Any]:
        """更新知识条目"""
        kb_id_str = str(kb_id)

        if kb_id_str not in self.kb_data.get("knowledge", {}):
            return self.create_text_response(f"❌ 知识条目不存在: {kb_id}")

        item = self.kb_data["knowledge"][kb_id_str]

        # 检查权限（创建者或管理员可以修改）
        sender = self.get_sender_info(event)
        if item["creator"] != sender["sender_id"]:
            # 这里可以添加管理员检查
            pass

        old_answer = item["answer"]
        item["answer"] = new_answer
        item["updated_at"] = datetime.now().isoformat()

        self._save_data()

        return self.create_text_response(
            f"✅ 已更新知识条目\n"
            f"**ID:** {kb_id}\n"
            f"**问题:** {item['question']}\n"
            f"**旧答案:** {old_answer[:50]}...\n"
            f"**新答案:** {new_answer[:50]}..."
        )

    def _delete_knowledge(self, event: Dict[str, Any], kb_id: int) -> Dict[str, Any]:
        """删除知识条目"""
        kb_id_str = str(kb_id)

        if kb_id_str not in self.kb_data.get("knowledge", {}):
            return self.create_text_response(f"❌ 知识条目不存在: {kb_id}")

        item = self.kb_data["knowledge"][kb_id_str]

        # 检查权限
        sender = self.get_sender_info(event)
        if item["creator"] != sender["sender_id"]:
            # 这里可以添加管理员检查
            pass

        question = item["question"]
        del self.kb_data["knowledge"][kb_id_str]
        self._save_data()

        return self.create_text_response(
            f"✅ 已删除知识条目\n"
            f"**ID:** {kb_id}\n"
            f"**问题:** {question}"
        )

    def _set_category(self, event: Dict[str, Any], kb_id: int, category: str) -> Dict[str, Any]:
        """设置知识分类"""
        kb_id_str = str(kb_id)

        if kb_id_str not in self.kb_data.get("knowledge", {}):
            return self.create_text_response(f"❌ 知识条目不存在: {kb_id}")

        item = self.kb_data["knowledge"][kb_id_str]
        old_category = item.get("category", "通用")

        item["category"] = category
        self._save_data()

        return self.create_text_response(
            f"✅ 已设置分类\n"
            f"**ID:** {kb_id}\n"
            f"**问题:** {item['question']}\n"
            f"**分类:** {old_category} → {category}"
        )

    def _show_faq(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """显示常见问题"""
        chat_id = self.get_chat_id(event)

        # 获取当前群的知识
        knowledge_list = [
            item for item in self.kb_data.get("knowledge", {}).values()
            if item.get("chat_id") == chat_id
        ]

        if not knowledge_list:
            return self.create_text_response("📚 知识库为空，还没有常见问题")

        # 按浏览次数排序，获取最热门的
        knowledge_list.sort(key=lambda x: x.get("view_count", 0), reverse=True)

        text = "❓ **常见问题 FAQ**\n\n"

        for i, item in enumerate(knowledge_list[:10], 1):
            text += f"**{i}. {item['question']}**\n"
            text += f"{item['answer'][:100]}"
            if len(item['answer']) > 100:
                text += "..."
            text += f"\n_浏览 {item['view_count']} 次_\n\n"

        return self.create_text_response(text)
