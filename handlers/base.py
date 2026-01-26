"""
基础处理器类，包含通用的辅助方法
"""
from astrbot.api.event import AstrMessageEvent
import astrbot.api.message_components as Comp
import urllib.parse
from typing import Optional, Dict, Any, Union
from ..utils.render import Render


class BaseHandler:
    """基础处理器，提供通用方法"""
    
    def __init__(self, api, db_manager):
        self.api = api
        self.db_manager = db_manager
    
    def is_success(self, response) -> bool:
        """判断接口请求是否成功
        支持两种响应格式：
        1. {"code": 0, ...} - 旧格式
        2. {"success": true, ...} - 新格式
        支持非字典响应（如 HTML 错误页面）
        """
        # 如果响应不是字典，直接返回 False
        if not isinstance(response, dict):
            return False
        # 先检查 success 字段（新格式）
        if "success" in response:
            return response.get("success", False) == True
        # 检查 code 字段（旧格式，code 可能是数字或字符串）
        code = response.get("code", -1)
        if isinstance(code, str):
            return code == "0" or code.upper() == "SUCCESS"
        return code == 0

    def get_error_msg(self, response, default: str = "未知错误") -> str:
        """从响应中获取错误消息
        支持多种字段名：msg, message, error
        支持非字典响应（如 HTML 错误页面）
        """
        if not isinstance(response, dict):
            # 如果响应不是字典，可能是 HTML 错误页面或其他错误
            if isinstance(response, str) and ("<html" in response.lower() or "<!doctype" in response.lower()):
                return "服务器错误，请稍后重试"
            return default
        
        # 获取错误消息
        msg = response.get("msg") or response.get("message") or response.get("error") or default
        
        # 检查错误消息是否包含 HTML 内容
        if isinstance(msg, str) and ("<html" in msg.lower() or "<!doctype" in msg.lower()):
            return "服务器错误，请稍后重试"
        
        return msg

    def chain_reply(self, event: AstrMessageEvent, raw_text: str = None, components: list = None):
        """发送消息链的辅助方法"""
        chain = []
        chain.append(Comp.At(qq=event.get_sender_id()))
        if raw_text:
            chain.append(Comp.Plain(raw_text))
        if components:
            chain.extend(components)
        return event.chain_result(chain)

    async def get_active_token(self, event: AstrMessageEvent):
        """获取当前用户激活的 token"""
        result_list = await self.api.user_acc_list(platformId=event.get_sender_id())
        if not self.is_success(result_list):
            return None, f"获取账号列表失败：{self.get_error_msg(result_list)}"
        
        accounts = result_list.get("data", [])
        if not accounts:
            return None, "您尚未绑定任何账号，请先使用登录命令绑定账号"
        
        user_data = await self.db_manager.get_user(event.get_sender_id())
        if not user_data:
            return None, "您尚未选择激活账号，请先使用 /三角洲 账号切换 命令选择账号"
        
        current_selection, _ = user_data
        if current_selection < 1 or current_selection > len(accounts):
            return None, "当前选择的账号序号无效，请重新选择账号"
        
        current_account = accounts[current_selection - 1]
        if not current_account.get("isValid", False):
            return None, "当前账号已失效，请重新登录"
        
        framework_token = current_account.get("frameworkToken")
        if not framework_token:
            return None, "当前账号 token 无效"
        
        return framework_token, None

    async def get_qqsafe_token(self, event: AstrMessageEvent):
        """获取QQ安全中心账号的 token"""
        result_list = await self.api.user_acc_list(platformId=event.get_sender_id())
        if not self.is_success(result_list):
            return None, f"获取账号列表失败：{self.get_error_msg(result_list)}"
        
        accounts = result_list.get("data", [])
        if not accounts:
            return None, "您尚未绑定任何账号，请先使用登录命令绑定账号"
        
        user_data = await self.db_manager.get_user(event.get_sender_id())
        if not user_data:
            return None, "您尚未选择激活账号，请先使用 /三角洲 账号切换 命令选择账号"
        
        current_selection, _ = user_data
        if current_selection < 1 or current_selection > len(accounts):
            return None, "当前选择的账号序号无效，请重新选择账号"
        
        current_account = accounts[current_selection - 1]
        if current_account.get("tokenType", "").lower() != "qqsafe":
            return None, "当前激活账号不是QQ安全中心账号\n请先使用 /三角洲 账号切换 命令切换到QQ安全中心账号"
        
        if not current_account.get("isValid", False):
            return None, "当前QQ安全中心账号已失效，请重新绑定"
        
        framework_token = current_account.get("frameworkToken")
        if not framework_token:
            return None, "当前QQ安全中心账号token无效"
        
        return framework_token, None

    @staticmethod
    def decode_url(text: str) -> str:
        """URL 解码"""
        try:
            return urllib.parse.unquote(text or "")
        except:
            return text or ""

    @staticmethod
    def format_duration(seconds, unit="seconds") -> str:
        """格式化游戏时长"""
        try:
            if unit == "minutes":
                seconds = int(seconds) * 60
            else:
                seconds = int(seconds)
            if seconds < 3600:
                return f"{seconds // 60}分钟"
            elif seconds < 86400:
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                return f"{hours}小时{minutes}分钟"
            else:
                days = seconds // 86400
                hours = (seconds % 86400) // 3600
                return f"{days}天{hours}小时"
        except:
            return "未知"

    @staticmethod
    def format_timestamp(timestamp: Union[int, float, str]) -> str:
        """格式化时间戳"""
        import time
        if not timestamp:
            return "未知时间"
        try:
            # 尝试转换为浮点数
            ts = float(timestamp)
            if ts <= 0:
                return "未知时间"
            # 兼容毫秒级时间戳 (如果大于 3000年的时间戳，认为是毫秒)
            if ts > 32503680000:
                ts = ts / 1000
            return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        except:
            return "时间格式错误"

    @staticmethod
    def format_ban_duration(duration: int) -> str:
        """格式化封禁持续时间"""
        try:
            if duration < 60:
                return f"{duration}秒"
            elif duration < 3600:
                return f"{duration // 60}分钟"
            elif duration < 86400:
                return f"{duration // 3600}小时"
            elif duration < 31536000:
                return f"{duration // 86400}天"
            else:
                return f"{duration // 31536000}年"
        except:
            return "未知时长"

    async def render_and_reply(
        self,
        event: AstrMessageEvent,
        template_name: str,
        params: Dict[str, Any],
        fallback_text: str = None,
        **render_kwargs
    ):
        """
        渲染模板为图片并回复
        
        Args:
            event: 消息事件
            template_name: 模板名称，如 'userInfo/userInfo.html'
            params: 模板参数
            fallback_text: 渲染失败时的回退文本
            **render_kwargs: 传递给渲染器的额外参数
        
        Returns:
            chain_result 用于 yield
        """
        try:
            image_bytes = await Render.render_to_image(template_name, params, **render_kwargs)
            if image_bytes:
                # 渲染成功，发送图片
                return self.image_reply(event, image_bytes)
            else:
                # 渲染失败，发送文本
                return self.chain_reply(event, fallback_text or "图片渲染失败，请检查 playwright 是否正确安装")
        except Exception as e:
            from astrbot.api import logger
            logger.error(f"[渲染失败] {e}")
            return self.chain_reply(event, fallback_text or f"渲染出错：{str(e)}")

    def image_reply(self, event: AstrMessageEvent, image_data: bytes):
        """发送图片回复的辅助方法"""
        import base64
        chain = [
            Comp.At(qq=event.get_sender_id()),
            Comp.Image.fromBase64(base64.b64encode(image_data).decode('utf-8'))
        ]
        return event.chain_result(chain)
