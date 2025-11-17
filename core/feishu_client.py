"""
飞书API客户端
"""
import json
import time
import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FeishuClient:
    """飞书API客户端"""

    def __init__(self, app_id: str, app_secret: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.tenant_access_token = None
        self.token_expire_time = 0

        # API端点
        self.base_url = "https://open.feishu.cn/open-apis"

    def _get_tenant_access_token(self) -> str:
        """
        获取tenant_access_token
        """
        # 检查token是否过期
        if self.tenant_access_token and time.time() < self.token_expire_time:
            return self.tenant_access_token

        url = f"{self.base_url}/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json"}
        data = {
            "app_id": self.app_id,
            "app_secret": self.app_secret
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()

            if result.get("code") == 0:
                self.tenant_access_token = result.get("tenant_access_token")
                # 提前5分钟刷新token
                self.token_expire_time = time.time() + result.get("expire", 7200) - 300
                logger.info("成功获取tenant_access_token")
                return self.tenant_access_token
            else:
                logger.error(f"获取token失败: {result}")
                raise Exception(f"获取token失败: {result.get('msg')}")

        except Exception as e:
            logger.error(f"获取token异常: {e}")
            raise

    def send_message(self, receive_id: str, msg_type: str, content: Dict[str, Any],
                     receive_id_type: str = "chat_id") -> Dict[str, Any]:
        """
        发送消息

        Args:
            receive_id: 接收者ID（群聊ID或用户ID）
            msg_type: 消息类型（text/post/image/interactive等）
            content: 消息内容
            receive_id_type: 接收者ID类型（chat_id/user_id/open_id等）

        Returns:
            API响应结果
        """
        token = self._get_tenant_access_token()
        url = f"{self.base_url}/im/v1/messages"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        params = {"receive_id_type": receive_id_type}

        data = {
            "receive_id": receive_id,
            "msg_type": msg_type,
            "content": json.dumps(content)
        }

        try:
            response = requests.post(url, headers=headers, params=params,
                                     json=data, timeout=10)
            response.raise_for_status()
            result = response.json()

            if result.get("code") == 0:
                logger.info(f"消息发送成功: {receive_id}")
                return result
            else:
                logger.error(f"消息发送失败: {result}")
                return result

        except Exception as e:
            logger.error(f"发送消息异常: {e}")
            raise

    def send_text_message(self, receive_id: str, text: str,
                          receive_id_type: str = "chat_id") -> Dict[str, Any]:
        """
        发送文本消息

        Args:
            receive_id: 接收者ID
            text: 文本内容
            receive_id_type: 接收者ID类型

        Returns:
            API响应结果
        """
        content = {"text": text}
        return self.send_message(receive_id, "text", content, receive_id_type)

    def send_card_message(self, receive_id: str, card: Dict[str, Any],
                          receive_id_type: str = "chat_id") -> Dict[str, Any]:
        """
        发送卡片消息

        Args:
            receive_id: 接收者ID
            card: 卡片内容
            receive_id_type: 接收者ID类型

        Returns:
            API响应结果
        """
        return self.send_message(receive_id, "interactive", card, receive_id_type)

    def reply_message(self, message_id: str, msg_type: str,
                      content: Dict[str, Any]) -> Dict[str, Any]:
        """
        回复消息

        Args:
            message_id: 要回复的消息ID
            msg_type: 消息类型
            content: 消息内容

        Returns:
            API响应结果
        """
        token = self._get_tenant_access_token()
        url = f"{self.base_url}/im/v1/messages/{message_id}/reply"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        data = {
            "msg_type": msg_type,
            "content": json.dumps(content)
        }

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            response.raise_for_status()
            result = response.json()

            if result.get("code") == 0:
                logger.info(f"回复消息成功: {message_id}")
                return result
            else:
                logger.error(f"回复消息失败: {result}")
                return result

        except Exception as e:
            logger.error(f"回复消息异常: {e}")
            raise

    def get_chat_members(self, chat_id: str) -> list:
        """
        获取群成员列表

        Args:
            chat_id: 群聊ID

        Returns:
            成员列表
        """
        token = self._get_tenant_access_token()
        url = f"{self.base_url}/im/v1/chats/{chat_id}/members"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        params = {
            "member_id_type": "open_id",
            "page_size": 100
        }

        members = []
        page_token = None

        try:
            while True:
                if page_token:
                    params["page_token"] = page_token

                response = requests.get(url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
                result = response.json()

                if result.get("code") == 0:
                    data = result.get("data", {})
                    members.extend(data.get("items", []))

                    if not data.get("has_more"):
                        break

                    page_token = data.get("page_token")
                else:
                    logger.error(f"获取群成员失败: {result}")
                    break

            logger.info(f"获取群成员成功: {len(members)}人")
            return members

        except Exception as e:
            logger.error(f"获取群成员异常: {e}")
            return []

    def get_user_info(self, user_id: str, user_id_type: str = "open_id") -> Optional[Dict[str, Any]]:
        """
        获取用户信息

        Args:
            user_id: 用户ID
            user_id_type: 用户ID类型

        Returns:
            用户信息
        """
        token = self._get_tenant_access_token()
        url = f"{self.base_url}/contact/v3/users/{user_id}"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        params = {"user_id_type": user_id_type}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            result = response.json()

            if result.get("code") == 0:
                return result.get("data", {}).get("user", {})
            else:
                logger.error(f"获取用户信息失败: {result}")
                return None

        except Exception as e:
            logger.error(f"获取用户信息异常: {e}")
            return None
