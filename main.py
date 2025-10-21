from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.api import AstrBotConfig
import time

from .df_api import DeltaForceAPI
from .df_sqlite import DeltaForceSQLiteManager

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
        self.db_manager = DeltaForceSQLiteManager()

    async def initialize(self):
        """可选择实现异步的插件初始化方法，当实例化该插件类之后会自动调用该方法。"""
        try:
            success = await self.db_manager.initialize_table()
            if success:
                logger.info("三角洲插件数据库初始化完成")
            else:
                logger.error("三角洲插件数据库初始化失败")
        except Exception as e:
            logger.error(f"插件初始化失败: {e}")
    
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
            if code == 1 or code == 2:
                continue
            elif code == -2:
                yield self.chain_reply(event, f"二维码已过期，请重新获取！")
                return
            elif code == -3:
                yield self.chain_reply(event, f"登录被拒绝，请尝试双机扫码或重试！")
                return
            elif code == 0:
                frameworkToken = result_sig.get("frameworkToken","")
                if not frameworkToken:
                    yield self.chain_reply(event, f"获取登录信息失败，请重试！")
                    return
                break
        result_bind = await self.api.user_bind(platformId=event.get_sender_id(), frameworkToken=frameworkToken)
        result_db_bind = await self.db_manager.upsert_user(user=event.get_sender_id(), selection=1, token=frameworkToken)
        if not self.is_success(result_bind) or not result_db_bind:
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
            if code == 1 or code == 2:
                continue
            elif code == -2:
                yield self.chain_reply(event, f"二维码已过期，请重新获取！")
                return
            elif code == -3:
                yield self.chain_reply(event, f"登录被拒绝，请尝试双机扫码或重试！")
                return
            elif code == 0:
                frameworkToken = result_sig.get("frameworkToken","")
                if not frameworkToken:
                    yield self.chain_reply(event, f"获取登录信息失败，请重试！")
                    return
                break
        result_bind = await self.api.user_bind(platformId=event.get_sender_id(), frameworkToken=frameworkToken)
        result_db_bind = await self.db_manager.upsert_user(user=event.get_sender_id(), selection=1, token=frameworkToken)
        if not self.is_success(result_bind) or not result_db_bind:
            yield self.chain_reply(event, f"绑定账号失败，错误代码：{result_bind.get('msg', '未知错误')}")
            return
        yield self.chain_reply(event, f"登录绑定成功！")
        return

    @deltaforce_cmd.command("账号切换", alias={"账号管理"})
    async def switch_account(self, event: AstrMessageEvent):
        """
        三角洲 账号切换
        """
        result_list = await self.api.user_acc_list(platformId=event.get_sender_id())
        if not self.is_success(result_list):
            yield self.chain_reply(event, f"获取账号列表失败，错误代码：{result_list.get('msg', '未知错误')}")
            return
        accounts = result_list.get("data", [])
    
        if not accounts:
            yield self.chain_reply(event, "您尚未绑定任何账号，请先使用登录命令绑定账号")
            return

        output_lines = [f"【{event.get_sender_name()}】绑定的账号列表：", "---QQ & 微信---"]

        for i, account in enumerate(accounts, 1):
            token_type = account.get("tokenType", "").upper()
            qq_number = account.get("qqNumber", "")
            open_id = account.get("openId", "")
            framework_token = account.get("frameworkToken", "")
            is_valid = account.get("isValid", False)

            if token_type == "qq" and qq_number:
                masked_id = f"{qq_number[:4]}****"
            elif open_id:
                masked_id = f"{open_id[:4]}****"
            else:
                masked_id = "未知"
            
            masked_token = f"{framework_token[:4]}****{framework_token[-4:]}" if framework_token else "未知"
            selection, _ = await self.db_manager.get_user(event.get_sender_id())
            if _ and selection == i:
                status_icon = "✅"
            else:
                status_icon = "❌"
        
            output_lines.append(f"{i}. {status_icon}【{token_type}】({masked_id}) {masked_token} {'【有效】' if is_valid else '【无效】'}")

        output_lines.extend([
            "",
            "可通过 /三角洲 解绑 <序号> 来解绑账号登录数据。",
            "可通过 /三角洲 删除 <序号> 来删除QQ/微信登录数据。",
            "使用 /三角洲 账号切换 <序号> 可切换当前激活账号。"
        ])
        yield self.chain_reply(event, "\n".join(output_lines))
    
    @deltaforce_cmd.command("解绑", alias={"账号解绑"})
    async def unbind_account(self, event: AstrMessageEvent, value: str):
        """
        三角洲 账号解绑
        """
        value = int(value)
        result_list = await self.api.user_acc_list(platformId=event.get_sender_id())
        if not self.is_success(result_list):
            yield self.chain_reply(event, f"获取账号列表失败，错误代码：{result_list.get('msg', '未知错误')}")
            return
        accounts = result_list.get("data", [])
        if not accounts:
            yield self.chain_reply(event, "您尚未绑定任何账号，请先使用登录命令绑定账号")
            return
        if value is None or value < 1 or value > len(accounts):
            yield self.chain_reply(event, "当前没有激活的账号，无法解绑，请先切换账号后再解绑")
            return
        frameworkToken = accounts[value - 1].get("frameworkToken","")
        result_unbind = await self.api.user_unbind(platformId=event.get_sender_id(), frameworkToken=frameworkToken)
        result_db_unbind = await self.db_manager.upsert_user(user=event.get_sender_id(), selection=0, token=None)
        if not self.is_success(result_unbind) or not result_db_unbind:
            yield self.chain_reply(event, f"解绑账号失败，错误代码：{result_unbind.get('msg', '未知错误')}")
            return
        yield self.chain_reply(event, "解绑账号成功")
        return

    @deltaforce_cmd.command("删除", alias={"账号删除"})
    async def delete_account(self, event: AstrMessageEvent, value: str):
        """
        三角洲 账号删除 仅支持微信QQ
        """
        value = int(value)
        result_list = await self.api.user_acc_list(platformId=event.get_sender_id())
        if not self.is_success(result_list):
            yield self.chain_reply(event, f"获取账号列表失败，错误代码：{result_list.get('msg', '未知错误')}")
            return
        accounts = result_list.get("data", [])
        if not accounts:
            yield self.chain_reply(event, "您尚未绑定任何账号，请先使用登录命令绑定账号")
            return
        if value is None or value < 1 or value > len(accounts):
            yield self.chain_reply(event, "当前没有激活的账号，无法删除，请先切换账号后再删除")
            return
        frameworkToken = accounts[value - 1].get("frameworkToken","")
        if accounts[value - 1].get("tokenType","") == "qq":
            result_unbind = await self.api.login_qq_delete(frameworkToken=frameworkToken)
        elif accounts[value - 1].get("tokenType","") == "wechat":
            result_unbind = await self.api.login_wechat_delete(frameworkToken=frameworkToken)
        else:
            yield self.chain_reply(event, "仅支持删除QQ和微信登录数据，其他类型暂不支持！")
            return
        result_db_unbind = await self.db_manager.upsert_user(user=event.get_sender_id(), selection=0, token=None)
        if not self.is_success(result_unbind) or not result_db_unbind:
            yield self.chain_reply(event, f"删除账号失败，错误代码：{result_unbind.get('msg', '未知错误')}")
            return
        yield self.chain_reply(event, "删除账号登录数据成功")
        return

    async def terminate(self):
        """可选择实现异步的插件销毁方法，当插件被卸载/停用时会调用。"""
