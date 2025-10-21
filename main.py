from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api import AstrBotConfig
import time

from .df_api import DeltaForceAPI


@register(
    "delta_force_plugin",
    "EntropyIncrease",
    "三角洲行动 AstrBot 插件",
    "v0.0.2",
    "https://github.com/Entropy-Increase-Team/astrbot_plugin_deltaforce",
)
class DeltaForce(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.token = config.get("token", "")
        self.clientid = config.get("clientid", "")
        self.api = DeltaForceAPI(self.token, self.clientid)

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
    
    def is_success(self, response: dict) -> bool:
        """判断接口请求是否成功的辅助方法"""
        return response.get("code", -1) == 0

    def chain_reply(self, event: AstrMessageEvent, raw_text: str = None, components: list = None):
        """发送消息链的辅助方法"""
        chain = []
        chain.append(Comp.At(qq=event.get_sender_id()))
        if raw_text:
            chain.append(Comp.Plain(raw_text))
        if components:
            chain.extend(components)
        return event.chain_result(chain)

    @filter.command_group("三角洲", alias={"洲"})
    async def deltaforce_cmd(self, event: AstrMessageEvent):
        """
        三角洲 插件 主命令组
        """
        pass

    @deltaforce_cmd.command("QQ登录", alias={"登录"})
    async def login_by_qq(self, event: AstrMessageEvent):
        """
        三角洲 QQ 登录
        """
        result_sig = await self.api.login_qq_get_qrcode()
        if not self.is_success(result_sig):
            yield self.chain_reply(event, f"获取二维码失败，错误代码：{result_sig.get('msg', '未知错误')}")
            return
        frameworkToken = result_sig.get("frameworkToken","")
        image = result_sig.get("qr_image","")
        image_base64 = image.split(",")[1] if "," in image else image

        yield self.chain_reply(event, f"获取二维码成功，请登录！", [Comp.Image.fromBase64(image_base64)])
        while True:
            time.sleep(1)
            result_sig = await self.api.login_qq_get_status(frameworkToken)
            code = result_sig.get("code",-3)
            status = result_sig.get("status","expired")
            if status == "pending" or status == "scanned":
                continue
            elif status == "expired":
                yield self.chain_reply(event, f"二维码已过期，请重新获取！")
                return
            elif code == -3 or status == "rejected":
                yield self.chain_reply(event, f"登录被拒绝，请尝试双机扫码或重试！")
                return
            elif status == "done":
                frameworkToken = result_sig.get("frameworkToken","")
                if not frameworkToken:
                    yield self.chain_reply(event, f"获取登录信息失败，请重试！")
                    return
                break
        result_bind = await self.api.user_bind(platformId=event.get_sender_id(), frameworkToken=frameworkToken)
        if not self.is_success(result_bind):
            yield self.chain_reply(event, f"绑定账号失败，错误代码：{result_bind.get('msg', '未知错误')}")
            return
        yield self.chain_reply(event, f"登录绑定成功！")
        return

    @deltaforce_cmd.command("微信登录")
    async def login_by_wechat(self, event: AstrMessageEvent):
        """
        三角洲 微信 登录
        """
        result_sig = await self.api.login_wechat_get_qrcode()
        if not self.is_success(result_sig):
            yield self.chain_reply(event, f"获取二维码失败，错误代码：{result_sig.get('msg', '未知错误')}")
            return
        frameworkToken = result_sig.get("frameworkToken","")
        image = result_sig.get("qr_image","")

        yield self.chain_reply(event, f"获取二维码成功，请登录！", [Comp.Image.fromURL(image)])
        while True:
            time.sleep(1)
            result_sig = await self.api.login_wechat_get_status(frameworkToken)
            code = result_sig.get("code",-3)
            status = result_sig.get("status","expired")
            if status == "pending" or status == "scanned":
                continue
            elif status == "expired":
                yield self.chain_reply(event, f"二维码已过期，请重新获取！")
                return
            elif code == -3 or status == "rejected":
                yield self.chain_reply(event, f"登录被拒绝，请尝试双机扫码或重试！")
                return
            elif status == "done":
                print(result_sig)
                frameworkToken = result_sig.get("frameworkToken","")
                if not frameworkToken:
                    yield self.chain_reply(event, f"获取登录信息失败，请重试！")
                    return
                break
        result_bind = await self.api.user_bind(platformId=event.get_sender_id(), frameworkToken=frameworkToken)
        if not self.is_success(result_bind):
            yield self.chain_reply(event, f"绑定账号失败，错误代码：{result_bind.get('msg', '未知错误')}")
            return
        yield self.chain_reply(event, f"登录绑定成功！")
        return


    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""