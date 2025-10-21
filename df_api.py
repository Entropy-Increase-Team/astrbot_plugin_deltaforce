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

    async def login_qq_get_qrcode(self):
        return await self.req_get(url="/login/qq/qr")
    
    async def login_qq_get_status(self, frameworkToken: str):
        return await self.req_get(url="/login/qq/status", params={"frameworkToken": frameworkToken})

    async def login_wechat_get_qrcode(self):
        return await self.req_get(url="/login/wechat/qr")

    async def login_wechat_get_status(self, frameworkToken: str):
        return await self.req_get(url="/login/wechat/status", params={"frameworkToken": frameworkToken})
