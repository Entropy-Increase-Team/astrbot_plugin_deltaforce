import aiohttp, json

class DeltaForceAPI():
    """ 三角洲 API 封装类 """
    def __init__(self, token: str, clientid: str):
        self.token = token
        self.clientid = clientid
        self.baseurl = "https://df-api.shallow.ink"
        
    async def req_get(self, url, params=None):
        headers = {"Authorization": f"Bearer {self.token}"}
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url=f"{self.baseurl}{url}", 
                headers=headers, 
                params=params
            ) as response:
                return await response.json()
    
    async def req_post(self, url, json=None, data=None):
        headers = {"Authorization": f"Bearer {self.token}"}
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=f"{self.baseurl}{url}", 
                headers=headers, 
                json=json,
                data=data
            ) as response:
                return await response.json()

    ################################################################
    async def user_bind(self, platformId:str, frameworkToken:str):
        return await self.req_post(
            url = "/user/bind",
            data = {
                "platformID": platformId,
                "frameworkToken": frameworkToken,
                "clientID": self.clientid,
                "clientType": "AstrBot"
            }
        )

    async def user_unbind(self, platformId:str, frameworkToken:str):
        return await self.req_post(
            url = "/user/unbind",
            data = {
                "platformID": platformId,
                "frameworkToken": frameworkToken,
                "clientID": self.clientid,
                "clientType": "AstrBot"
            }
        )

    async def user_acc_list(self, platformId:str):
        return await self.req_get(
            url = "/user/list",
            params = {
                "platformID": platformId,
                "clientID": self.clientid,
                "clientType": "AstrBot"
            }
        )


    async def login_qqck_(self, cookie: str):
        return await self.req_post(
            url="/login/qq/ck",
            data = {"cookie": cookie}
        )
    
    async def login_qqck_get_status(self, frameworkToken: str):
        return await self.req_get(
            url="/login/qq/status", 
            params = {
                "frameworkToken": frameworkToken
            }
        )

    async def login_qq_get_qrcode(self):
        return await self.req_get(url="/login/qq/qr")
    
    async def login_qq_get_status(self, frameworkToken: str):
        return await self.req_get(
            url="/login/qq/status", 
            params = {
                "frameworkToken": frameworkToken
            }
        )

    async def login_qq_delete(self, frameworkToken: str):
        return await self.req_get(
            url = "/login/qq/delete",
            params = {
                "frameworkToken": frameworkToken,
            }
        )

    async def login_wechat_get_qrcode(self):
        return await self.req_get(url="/login/wechat/qr")

    async def login_wechat_get_status(self, frameworkToken: str):
        return await self.req_get(
            url="/login/wechat/status", 
            params = {
                "frameworkToken": frameworkToken
            }
        )

    async def login_wechat_delete(self, frameworkToken: str):
        return await self.req_get(
            url = "/login/wechat/delete",
            params = {
                "frameworkToken": frameworkToken,
            }
        )
    
    async def login_qqsafe_qrcode(self):
        return await self.req_get(url="/login/qqsafe/qr")
    
    async def login_qqsafe_get_status(self, frameworkToken: str):
        return await self.req_get(
            url="/login/qqsafe/status", 
            params = {
                "frameworkToken": frameworkToken
            }
        )

    async def login_wegame_qrcode(self):
        return await self.req_get(url="/login/wegame/qr")
    
    async def login_wegame_get_status(self, frameworkToken: str):
        return await self.req_get(
            url="/login/wegame/status", 
            params = {
                "frameworkToken": frameworkToken
            }
        )
    ################################################################

    async def get_daily_keyword(self):
        return await self.req_get(url="/df/tools/dailykeyword")

    async def get_ban_history(self, frameworkToken: str):
        return await self.req_get(
            url="/login/qqsafe/ban",
            params = {
                "frameworkToken": frameworkToken
            }
        )