"""
账号管理处理器
包含：登录、账号列表、绑定、解绑、切换等
"""
import time
from astrbot.api.event import AstrMessageEvent
import astrbot.api.message_components as Comp
from .base import BaseHandler


class AccountHandler(BaseHandler):
    """账号管理处理器"""

    async def login_by_qq_ck(self, event: AstrMessageEvent, cookie: str = None):
        """QQ Cookie 登录"""
        if not cookie:
            yield self.chain_reply(event, """三角洲ck登陆教程：
1. 准备via浏览器(或其他类似浏览器)，在浏览器中打开 https://pvp.qq.com/cp/a20161115tyf/page1.shtml
2. 在网页中进行QQ登陆
3. 点击左上角的网页名左侧的盾图标
4. 点击查看cookies，然后复制全部内容
5. 返回QQ，私聊机器人，发送 /三角洲 ck登陆 刚刚复制的cookies
6. 成功登陆""")
            return
        
        result_sig = await self.api.login_qqck_(cookie)
        if not self.is_success(result_sig):
            yield self.chain_reply(event, f"ck登录失败，错误代码：{result_sig.get('msg', '未知错误')}")
            return
        
        frameworkToken = result_sig.get("frameworkToken", "")
        while True:
            time.sleep(1)
            result_sig = await self.api.login_qqck_get_status(frameworkToken)
            code = result_sig.get("code", -2)
            if code == -2:
                yield self.chain_reply(event, "ck已过期，请重新获取！")
                return
            elif code == 0:
                frameworkToken = result_sig.get("frameworkToken", "")
                if not frameworkToken:
                    yield self.chain_reply(event, "获取登录信息失败，请重试！")
                    return
                break
        
        result_list = await self.api.user_acc_list(platformId=event.get_sender_id())
        if not self.is_success(result_list):
            yield self.chain_reply(event, f"获取账号列表失败，错误代码：{result_list.get('msg', '未知错误')}")
            return
        
        result_bind = await self.api.user_bind(platformId=event.get_sender_id(), frameworkToken=frameworkToken)
        result_db_bind = await self.db_manager.upsert_user(
            user=event.get_sender_id(), 
            selection=len(result_list.get("data", [])) + 1, 
            token=frameworkToken
        )
        
        if not self.is_success(result_bind) or not result_db_bind:
            yield self.chain_reply(event, f"绑定账号失败，错误代码：{result_bind.get('msg', '未知错误')}")
            return
        
        yield self.chain_reply(event, "登录绑定成功！")

    async def login_by_qq(self, event: AstrMessageEvent):
        """QQ 二维码登录"""
        result_sig = await self.api.login_qq_get_qrcode()
        if not self.is_success(result_sig):
            yield self.chain_reply(event, f"获取二维码失败，错误代码：{result_sig.get('msg', '未知错误')}")
            return
        
        frameworkToken = result_sig.get("frameworkToken", "")
        image = result_sig.get("qr_image", "")
        image_base64 = image.split(",")[1] if "," in image else image

        yield self.chain_reply(event, "获取二维码成功，请登录！", [Comp.Image.fromBase64(image_base64)])
        
        while True:
            time.sleep(1)
            result_sig = await self.api.login_qq_get_status(frameworkToken)
            code = result_sig.get("code", -3)
            if code == 1 or code == 2:
                continue
            elif code == -2:
                yield self.chain_reply(event, "二维码已过期，请重新获取！")
                return
            elif code == -3:
                yield self.chain_reply(event, "登录被拒绝，请尝试双机扫码或重试！")
                return
            elif code == 0:
                frameworkToken = result_sig.get("frameworkToken", "")
                if not frameworkToken:
                    yield self.chain_reply(event, "获取登录信息失败，请重试！")
                    return
                break
        
        result_list = await self.api.user_acc_list(platformId=event.get_sender_id())
        if not self.is_success(result_list):
            yield self.chain_reply(event, f"获取账号列表失败，错误代码：{result_list.get('msg', '未知错误')}")
            return
        
        result_bind = await self.api.user_bind(platformId=event.get_sender_id(), frameworkToken=frameworkToken)
        result_db_bind = await self.db_manager.upsert_user(
            user=event.get_sender_id(), 
            selection=len(result_list.get("data", [])) + 1, 
            token=frameworkToken
        )
        
        if not self.is_success(result_bind) or not result_db_bind:
            yield self.chain_reply(event, f"绑定账号失败，错误代码：{result_bind.get('msg', '未知错误')}")
            return
        
        yield self.chain_reply(event, "登录绑定成功！")

    async def login_by_wechat(self, event: AstrMessageEvent):
        """微信二维码登录"""
        result_sig = await self.api.login_wechat_get_qrcode()
        if not self.is_success(result_sig):
            yield self.chain_reply(event, f"获取二维码失败，错误代码：{result_sig.get('msg', '未知错误')}")
            return
        
        frameworkToken = result_sig.get("frameworkToken", "")
        image = result_sig.get("qr_image", "")

        yield self.chain_reply(event, "获取二维码成功，请登录！", [Comp.Image.fromURL(image)])
        
        while True:
            time.sleep(1)
            result_sig = await self.api.login_wechat_get_status(frameworkToken)
            code = result_sig.get("code", -3)
            if code == 1 or code == 2:
                continue
            elif code == -2:
                yield self.chain_reply(event, "二维码已过期，请重新获取！")
                return
            elif code == -3:
                yield self.chain_reply(event, "登录被拒绝，请尝试双机扫码或重试！")
                return
            elif code == 0:
                frameworkToken = result_sig.get("frameworkToken", "")
                if not frameworkToken:
                    yield self.chain_reply(event, "获取登录信息失败，请重试！")
                    return
                break
        
        result_list = await self.api.user_acc_list(platformId=event.get_sender_id())
        if not self.is_success(result_list):
            yield self.chain_reply(event, f"获取账号列表失败，错误代码：{result_list.get('msg', '未知错误')}")
            return
        
        result_bind = await self.api.user_bind(platformId=event.get_sender_id(), frameworkToken=frameworkToken)
        result_db_bind = await self.db_manager.upsert_user(
            user=event.get_sender_id(), 
            selection=len(result_list.get("data", [])) + 1, 
            token=frameworkToken
        )
        
        if not self.is_success(result_bind) or not result_db_bind:
            yield self.chain_reply(event, f"绑定账号失败，错误代码：{result_bind.get('msg', '未知错误')}")
            return
        
        yield self.chain_reply(event, "登录绑定成功！")

    async def login_by_qqsafe(self, event: AstrMessageEvent):
        """QQ安全中心登录"""
        result_sig = await self.api.login_qqsafe_qrcode()
        if not self.is_success(result_sig):
            yield self.chain_reply(event, f"获取二维码失败，错误代码：{result_sig.get('msg', '未知错误')}")
            return
        
        frameworkToken = result_sig.get("frameworkToken", "")
        image = result_sig.get("qr_image", "")
        image_base64 = image.split(",")[1] if "," in image else image

        yield self.chain_reply(event, "获取二维码成功，请登录！", [Comp.Image.fromBase64(image_base64)])
        
        while True:
            time.sleep(1)
            result_sig = await self.api.login_qqsafe_get_status(frameworkToken)
            code = result_sig.get("code", -2)
            if code == 1 or code == 2:
                continue
            elif code == -2:
                yield self.chain_reply(event, "二维码已过期，请重新获取！")
                return
            elif code == 0:
                frameworkToken = result_sig.get("frameworkToken", "")
                if not frameworkToken:
                    yield self.chain_reply(event, "获取登录信息失败，请重试！")
                    return
                break
        
        result_list = await self.api.user_acc_list(platformId=event.get_sender_id())
        if not self.is_success(result_list):
            yield self.chain_reply(event, f"获取账号列表失败，错误代码：{result_list.get('msg', '未知错误')}")
            return
        
        result_bind = await self.api.user_bind(platformId=event.get_sender_id(), frameworkToken=frameworkToken)
        result_db_bind = await self.db_manager.upsert_user(
            user=event.get_sender_id(), 
            selection=len(result_list.get("data", [])) + 1, 
            token=frameworkToken
        )
        
        if not self.is_success(result_bind) or not result_db_bind:
            yield self.chain_reply(event, f"绑定账号失败，错误代码：{result_bind.get('msg', '未知错误')}")
            return
        
        yield self.chain_reply(event, "登录绑定成功！")

    async def login_by_wegame(self, event: AstrMessageEvent):
        """WeGame 登录"""
        result_sig = await self.api.login_wegame_qrcode()
        if not self.is_success(result_sig):
            yield self.chain_reply(event, f"获取二维码失败，错误代码：{result_sig.get('msg', '未知错误')}")
            return
        
        frameworkToken = result_sig.get("frameworkToken", "")
        image = result_sig.get("qr_image", "")
        image_base64 = image.split(",")[1] if "," in image else image

        yield self.chain_reply(event, "获取二维码成功，请登录！", [Comp.Image.fromBase64(image_base64)])
        
        while True:
            time.sleep(1)
            result_sig = await self.api.login_wegame_get_status(frameworkToken)
            code = result_sig.get("code", -2)
            if code == 1 or code == 2:
                continue
            elif code == -2:
                yield self.chain_reply(event, "二维码已过期，请重新获取！")
                return
            elif code == 0:
                frameworkToken = result_sig.get("frameworkToken", "")
                if not frameworkToken:
                    yield self.chain_reply(event, "获取登录信息失败，请重试！")
                    return
                break
        
        result_list = await self.api.user_acc_list(platformId=event.get_sender_id())
        if not self.is_success(result_list):
            yield self.chain_reply(event, f"获取账号列表失败，错误代码：{result_list.get('msg', '未知错误')}")
            return
        
        result_bind = await self.api.user_bind(platformId=event.get_sender_id(), frameworkToken=frameworkToken)
        result_db_bind = await self.db_manager.upsert_user(
            user=event.get_sender_id(), 
            selection=len(result_list.get("data", [])) + 1, 
            token=frameworkToken
        )
        
        if not self.is_success(result_bind) or not result_db_bind:
            yield self.chain_reply(event, f"绑定账号失败，错误代码：{result_bind.get('msg', '未知错误')}")
            return
        
        yield self.chain_reply(event, "登录绑定成功！")

    async def list_account(self, event: AstrMessageEvent):
        """账号列表"""
        result_list = await self.api.user_acc_list(platformId=event.get_sender_id())
        if not self.is_success(result_list):
            yield self.chain_reply(event, f"获取账号列表失败，错误代码：{result_list.get('msg', '未知错误')}")
            return
        
        accounts = result_list.get("data", [])
        if not accounts:
            yield self.chain_reply(event, "您尚未绑定任何账号，请先使用登录命令绑定账号")
            return

        # 分类账号
        qq_wechat_accounts = []
        qqsafe_accounts = []
        wegame_accounts = []
        unknown_accounts = []

        for account in accounts:
            token_type = account.get("tokenType", "").lower()
            if token_type in ["qq", "wechat"]:
                qq_wechat_accounts.append(account)
            elif token_type == "qqsafe":
                qqsafe_accounts.append(account)
            elif token_type == "wegame":
                wegame_accounts.append(account)
            else:
                unknown_accounts.append(account)

        output_lines = [f"【{event.get_sender_name()}】绑定的账号列表："]

        # 获取当前选择
        current_selection = None
        user_data = await self.db_manager.get_user(event.get_sender_id())
        if user_data:
            current_selection, _ = user_data

        idx = 1
        
        if qq_wechat_accounts:
            output_lines.append("---QQ & 微信---")
            for account in qq_wechat_accounts:
                line = self._format_account_line(account, idx, current_selection)
                output_lines.append(line)
                idx += 1

        if wegame_accounts:
            output_lines.append("---Wegame---")
            for account in wegame_accounts:
                line = self._format_account_line(account, idx, current_selection, is_wegame=True)
                output_lines.append(line)
                idx += 1

        if qqsafe_accounts:
            output_lines.append("---QQ安全中心---")
            for account in qqsafe_accounts:
                line = self._format_account_line(account, idx, current_selection)
                output_lines.append(line)
                idx += 1

        if unknown_accounts:
            output_lines.append("---其他---")
            for account in unknown_accounts:
                line = self._format_account_line(account, idx, current_selection)
                output_lines.append(line)
                idx += 1

        output_lines.extend([
            "",
            "可通过 /三角洲 解绑 <序号> 来解绑账号登录数据。",
            "可通过 /三角洲 删除 <序号> 来删除QQ/微信登录数据。",
            "使用 /三角洲 账号切换 <序号> 可切换当前激活账号。"
        ])

        yield self.chain_reply(event, "\n".join(output_lines))

    def _format_account_line(self, account, idx, current_selection, is_wegame=False):
        """格式化账号行显示"""
        token_type = account.get("tokenType", "").upper()
        qq_number = account.get("qqNumber", "")
        open_id = account.get("openId", "")
        tgp_id = account.get("tgpId", "")
        login_type = account.get("loginType", "").upper()
        framework_token = account.get("frameworkToken", "")
        is_valid = account.get("isValid", False)

        # 确定显示ID
        if token_type == "QQ" and qq_number:
            masked_id = f"{qq_number[:4]}****"
        elif is_wegame and (qq_number or tgp_id):
            masked_id = f"{(qq_number or tgp_id)[:4]}****"
        elif open_id:
            masked_id = f"{open_id[:4]}****"
        else:
            masked_id = "未知"

        # 显示类型
        if is_wegame and login_type:
            display_type = f"{token_type}({login_type})"
        else:
            display_type = token_type

        masked_token = f"{framework_token[:4]}****{framework_token[-4:]}" if framework_token else "未知"
        is_current = (current_selection == idx)
        status_icon = "✅" if is_current else "❌"
        validity_status = "【有效】" if is_valid else "【失效】"
        
        return f"{idx}. {status_icon}【{display_type}】({masked_id}) {masked_token} {validity_status}"

    async def unbind_account(self, event: AstrMessageEvent, value: int):
        """解绑账号"""
        result_list = await self.api.user_acc_list(platformId=event.get_sender_id())
        if not self.is_success(result_list):
            yield self.chain_reply(event, f"获取账号列表失败，错误代码：{result_list.get('msg', '未知错误')}")
            return
        
        accounts = result_list.get("data", [])
        if not accounts:
            yield self.chain_reply(event, "您尚未绑定任何账号，请先使用登录命令绑定账号")
            return
        
        if value is None or value < 1 or value > len(accounts):
            yield self.chain_reply(event, "序号无效，请检查后重试")
            return
        
        frameworkToken = accounts[value - 1].get("frameworkToken", "")
        result_unbind = await self.api.user_unbind(platformId=event.get_sender_id(), frameworkToken=frameworkToken)
        result_db_unbind = await self.db_manager.upsert_user(user=event.get_sender_id(), selection=value - 1, token=None)
        
        if not self.is_success(result_unbind) or not result_db_unbind:
            yield self.chain_reply(event, f"解绑账号失败，错误代码：{result_unbind.get('msg', '未知错误')}")
            return
        
        yield self.chain_reply(event, "解绑账号成功")

    async def delete_account(self, event: AstrMessageEvent, value: int):
        """删除账号（仅支持QQ/微信）"""
        result_list = await self.api.user_acc_list(platformId=event.get_sender_id())
        if not self.is_success(result_list):
            yield self.chain_reply(event, f"获取账号列表失败，错误代码：{result_list.get('msg', '未知错误')}")
            return
        
        accounts = result_list.get("data", [])
        if not accounts:
            yield self.chain_reply(event, "您尚未绑定任何账号，请先使用登录命令绑定账号")
            return
        
        if value is None or value < 1 or value > len(accounts):
            yield self.chain_reply(event, "序号无效，请检查后重试")
            return
        
        account = accounts[value - 1]
        frameworkToken = account.get("frameworkToken", "")
        token_type = account.get("tokenType", "").lower()
        
        if token_type == "qq":
            result_delete = await self.api.login_qq_delete(frameworkToken=frameworkToken)
        elif token_type == "wechat":
            result_delete = await self.api.login_wechat_delete(frameworkToken=frameworkToken)
        else:
            yield self.chain_reply(event, "仅支持删除QQ和微信登录数据，其他类型暂不支持！")
            return
        
        result_db = await self.db_manager.upsert_user(user=event.get_sender_id(), selection=value - 1, token=None)
        
        if not self.is_success(result_delete) or not result_db:
            yield self.chain_reply(event, f"删除账号失败，错误代码：{result_delete.get('msg', '未知错误')}")
            return
        
        yield self.chain_reply(event, "删除账号登录数据成功")

    async def switch_account(self, event: AstrMessageEvent, value: int):
        """切换账号"""
        result_list = await self.api.user_acc_list(platformId=event.get_sender_id())
        if not self.is_success(result_list):
            yield self.chain_reply(event, f"获取账号列表失败，错误代码：{result_list.get('msg', '未知错误')}")
            return
        
        accounts = result_list.get("data", [])
        if not accounts:
            yield self.chain_reply(event, "您尚未绑定任何账号，请先使用登录命令绑定账号")
            return
        
        if value is None or value < 1 or value > len(accounts):
            yield self.chain_reply(event, "序号无效，请检查后重试")
            return
        
        frameworkToken = accounts[value - 1].get("frameworkToken", "")
        result_db = await self.db_manager.upsert_user(user=event.get_sender_id(), selection=value, token=frameworkToken)
        
        if not result_db:
            yield self.chain_reply(event, "切换账号失败")
            return
        
        yield self.chain_reply(event, "切换账号成功")

    async def refresh_qq(self, event: AstrMessageEvent):
        """刷新QQ登录"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        try:
            # 使用刷新API
            result = await self.api.login_qq_refresh(token)
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"刷新失败：{result.get('msg', '未知错误')}\n请重新扫码登录")
                return

            new_token = result.get("frameworkToken", "")
            if new_token and new_token != token:
                # 更新数据库中的token
                await self.db_manager.upsert_user(
                    user=event.get_sender_id(),
                    selection=None,  # 保持当前选择
                    token=new_token
                )
                yield self.chain_reply(event, "✅ QQ登录刷新成功！")
            else:
                yield self.chain_reply(event, "✅ QQ登录状态正常，无需刷新")

        except Exception as e:
            yield self.chain_reply(event, f"刷新失败：{e}")

    async def refresh_wechat(self, event: AstrMessageEvent):
        """刷新微信登录"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        try:
            # 使用刷新API
            result = await self.api.login_wechat_refresh(token)
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"刷新失败：{result.get('msg', '未知错误')}\n请重新扫码登录")
                return

            new_token = result.get("frameworkToken", "")
            if new_token and new_token != token:
                # 更新数据库中的token
                await self.db_manager.upsert_user(
                    user=event.get_sender_id(),
                    selection=None,
                    token=new_token
                )
                yield self.chain_reply(event, "✅ 微信登录刷新成功！")
            else:
                yield self.chain_reply(event, "✅ 微信登录状态正常，无需刷新")

        except Exception as e:
            yield self.chain_reply(event, f"刷新失败：{e}")

    async def login_qq_oauth(self, event: AstrMessageEvent, auth_url: str = None):
        """QQ OAuth 授权登录"""
        if not auth_url:
            # 获取授权链接
            result = await self.api.login_qq_oauth_get_url(
                platform_id=event.get_sender_id()
            )
            
            if not self.is_success(result) or not result.get("login_url"):
                yield self.chain_reply(event, f"获取授权链接失败：{result.get('msg', '未知错误')}")
                return
            
            login_url = result.get("login_url", "")
            help_text = f"""三角洲QQ OAuth授权登陆教程：
1. QQ内打开链接：{login_url}
2. 点击登陆
3. 登陆成功后，点击右上角，选择复制链接
4. 返回聊天界面，发送：
   /三角洲 QQ授权登录 刚刚复制的链接

⚠️ OAuth登录更安全稳定，推荐使用！"""
            
            yield self.chain_reply(event, help_text)
            return
        
        # 提交授权链接
        try:
            result = await self.api.login_qq_oauth_submit(auth_url)
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"OAuth授权失败：{result.get('msg', '未知错误')}")
                return
            
            framework_token = result.get("frameworkToken", "")
            if not framework_token:
                yield self.chain_reply(event, "获取登录信息失败，请重试！")
                return
            
            # 绑定账号
            result_list = await self.api.user_acc_list(platformId=event.get_sender_id())
            result_bind = await self.api.user_bind(platformId=event.get_sender_id(), frameworkToken=framework_token)
            result_db = await self.db_manager.upsert_user(
                user=event.get_sender_id(),
                selection=len(result_list.get("data", [])) + 1,
                token=framework_token
            )
            
            if self.is_success(result_bind) and result_db:
                yield self.chain_reply(event, "✅ QQ OAuth授权登录成功！")
            else:
                yield self.chain_reply(event, f"绑定账号失败：{result_bind.get('msg', '未知错误')}")
                
        except Exception as e:
            yield self.chain_reply(event, f"OAuth登录失败：{e}")

    async def login_wechat_oauth(self, event: AstrMessageEvent, auth_url: str = None):
        """微信 OAuth 授权登录"""
        if not auth_url:
            # 获取授权链接
            result = await self.api.login_wechat_oauth_get_url(
                platform_id=event.get_sender_id()
            )
            
            if not self.is_success(result) or not result.get("login_url"):
                yield self.chain_reply(event, f"获取授权链接失败：{result.get('msg', '未知错误')}")
                return
            
            login_url = result.get("login_url", "")
            help_text = f"""三角洲微信OAuth授权登陆教程：
1. 微信内打开链接：{login_url}
2. 点击登陆
3. 登陆成功后，点击右上角，选择复制链接
4. 返回聊天界面，发送：
   /三角洲 微信授权登录 刚刚复制的链接"""
            
            yield self.chain_reply(event, help_text)
            return
        
        # 提交授权链接
        try:
            result = await self.api.login_wechat_oauth_submit(auth_url)
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"OAuth授权失败：{result.get('msg', '未知错误')}")
                return
            
            framework_token = result.get("frameworkToken", "")
            if not framework_token:
                yield self.chain_reply(event, "获取登录信息失败，请重试！")
                return
            
            # 绑定账号
            result_list = await self.api.user_acc_list(platformId=event.get_sender_id())
            result_bind = await self.api.user_bind(platformId=event.get_sender_id(), frameworkToken=framework_token)
            result_db = await self.db_manager.upsert_user(
                user=event.get_sender_id(),
                selection=len(result_list.get("data", [])) + 1,
                token=framework_token
            )
            
            if self.is_success(result_bind) and result_db:
                yield self.chain_reply(event, "✅ 微信OAuth授权登录成功！")
            else:
                yield self.chain_reply(event, f"绑定账号失败：{result_bind.get('msg', '未知错误')}")
                
        except Exception as e:
            yield self.chain_reply(event, f"OAuth登录失败：{e}")
