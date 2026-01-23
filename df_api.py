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

    async def get_money(self, frameworkToken: str):
        """获取货币信息"""
        return await self.req_get(
            url="/df/person/money",
            params = {
                "frameworkToken": frameworkToken
            }
        )

    async def get_personal_info(self, frameworkToken: str):
        """获取个人信息"""
        return await self.req_get(
            url="/df/person/info",
            params = {
                "frameworkToken": frameworkToken
            }
        )

    async def get_personal_data(self, frameworkToken: str, mode: str = "", season: str = "7"):
        """获取个人数据（烽火地带和全面战场）"""
        params = {"frameworkToken": frameworkToken}
        if mode:
            params["type"] = mode
        if season != "all":
            params["seasonid"] = season
        return await self.req_get(url="/df/person/personalData", params=params)

    async def get_flows(self, frameworkToken: str, flow_type: int, page: int = 1):
        """获取流水记录"""
        return await self.req_get(
            url="/df/person/flows",
            params={
                "frameworkToken": frameworkToken,
                "type": flow_type,
                "page": page
            }
        )

    async def get_collection(self, frameworkToken: str):
        """获取个人藏品"""
        return await self.req_get(
            url="/df/person/collection",
            params={"frameworkToken": frameworkToken}
        )

    async def get_map_stats(self, frameworkToken: str, seasonid: str, mode: str, map_id: str = ""):
        """获取地图数据统计"""
        params = {
            "frameworkToken": frameworkToken,
            "seasonid": seasonid,
            "type": mode
        }
        if map_id:
            params["mapId"] = map_id
        return await self.req_get(url="/df/person/mapStats", params=params)

    async def get_record(self, frameworkToken: str, mode_type: int, page: int = 1):
        """获取战绩记录"""
        return await self.req_get(
            url="/df/person/record",
            params={
                "frameworkToken": frameworkToken,
                "type": mode_type,
                "page": page
            }
        )

    async def get_operators(self):
        """获取所有干员信息"""
        return await self.req_get(url="/df/object/operator")

    async def get_maps(self):
        """获取所有地图信息"""
        return await self.req_get(url="/df/object/maps")

    async def search_object(self, keyword: str = "", object_ids: str = ""):
        """搜索物品"""
        params = {}
        if keyword:
            params["keyword"] = keyword
        if object_ids:
            params["id"] = object_ids
        return await self.req_get(url="/df/object/search", params=params)

    async def get_current_price(self, object_ids: str):
        """获取物品当前均价"""
        return await self.req_get(
            url="/df/object/price/latest",
            params={"id": object_ids}
        )

    async def get_price_history(self, object_id: str):
        """获取物品历史价格"""
        return await self.req_get(
            url="/df/object/price/history/v2",
            params={"objectId": object_id}
        )

    async def get_material_price(self, object_id: str = ""):
        """获取制造材料最低价格"""
        params = {"id": object_id} if object_id else {}
        return await self.req_get(url="/df/place/materialPrice", params=params)

    async def get_profit_rank(self, rank_type: str, place: str = "", limit: int = 20):
        """获取利润排行榜"""
        params = {"type": rank_type, "limit": limit}
        if place:
            params["place"] = place
        return await self.req_get(url="/df/place/profitRank/v1", params=params)

    async def get_health(self):
        """获取服务器健康状态"""
        return await self.req_get(url="/health/detailed")

    async def subscribe_record(self, platform_id: str, client_id: str, subscription_type: str = "both"):
        """订阅战绩"""
        return await self.req_post(
            url="/df/record/subscribe",
            json={
                "platformID": platform_id,
                "clientID": client_id,
                "subscriptionType": subscription_type
            }
        )

    async def unsubscribe_record(self, platform_id: str, client_id: str):
        """取消订阅战绩"""
        return await self.req_post(
            url="/df/record/unsubscribe",
            json={
                "platformID": platform_id,
                "clientID": client_id
            }
        )

    async def get_record_subscription(self, platform_id: str, client_id: str):
        """查询战绩订阅状态"""
        return await self.req_get(
            url="/df/record/subscription",
            params={
                "platformID": platform_id,
                "clientID": client_id
            }
        )

    # ==================== TTS语音 API ====================

    async def get_tts_health(self):
        """检查TTS服务状态"""
        return await self.req_get(url="/df/tts/health")

    async def get_tts_presets(self):
        """获取TTS角色预设列表"""
        return await self.req_get(url="/df/tts/presets")

    async def get_tts_preset_detail(self, character_id: str):
        """获取TTS角色预设详情"""
        return await self.req_get(url="/df/tts/preset", params={"characterId": character_id})

    async def tts_synthesize(self, text: str, character: str, emotion: str = ""):
        """TTS语音合成（队列模式）"""
        data = {"text": text, "character": character}
        if emotion:
            data["emotion"] = emotion
        return await self.req_post(url="/df/tts/synthesize", json=data)

    async def get_tts_task_status(self, task_id: str):
        """查询TTS任务状态"""
        return await self.req_get(url="/df/tts/task", params={"taskId": task_id})

    async def get_tts_queue_status(self):
        """查询TTS队列状态"""
        return await self.req_get(url="/df/tts/queue")

    # ==================== AI评价 API ====================

    async def get_ai_commentary(self, framework_token: str, mode_type: str, preset: str = ""):
        """获取AI锐评"""
        data = {"frameworkToken": framework_token, "type": mode_type}
        if preset:
            data["preset"] = preset
        return await self.req_post(url="/df/person/ai", json=data)

    async def get_ai_presets(self):
        """获取AI评价预设列表"""
        return await self.req_get(url="/df/person/ai/presets")

    # ==================== 日报/周报 API ====================

    async def get_daily_record(self, framework_token: str, mode: str = "", date: str = ""):
        """获取日报数据"""
        params = {"frameworkToken": framework_token}
        if mode:
            params["type"] = mode
        if date:
            params["date"] = date
        return await self.req_get(url="/df/person/daily", params=params)

    async def get_weekly_record(self, framework_token: str, mode: str = "", include_teammates: bool = False):
        """获取周报数据"""
        params = {"frameworkToken": framework_token, "includeTeammates": str(include_teammates).lower()}
        if mode:
            params["type"] = mode
        return await self.req_get(url="/df/person/weekly", params=params)

    # ==================== 特勤处 API ====================

    async def get_place_status(self, framework_token: str):
        """获取特勤处状态"""
        return await self.req_get(url="/df/place/status", params={"frameworkToken": framework_token})

    async def get_place_info(self, framework_token: str, place: str = ""):
        """获取特勤处信息"""
        params = {"frameworkToken": framework_token}
        if place:
            params["place"] = place
        return await self.req_get(url="/df/place/info", params=params)

    # ==================== 用户统计 API ====================

    async def get_user_stats(self):
        """获取用户统计信息"""
        return await self.req_get(url="/stats/users", params={"clientID": self.clientid})

    # ==================== 游戏语音 API ====================

    async def get_random_audio(self, category: str = "", tag: str = "", character: str = "", 
                                scene: str = "", action_type: str = "", count: int = 1):
        """随机获取音频"""
        params = {"count": count}
        if category:
            params["category"] = category
        if tag:
            params["tag"] = tag
        if character:
            params["character"] = character
        if scene:
            params["scene"] = scene
        if action_type:
            params["actionType"] = action_type
        return await self.req_get(url="/df/audio/random", params=params)

    async def get_character_audio(self, character: str = "", scene: str = "", action_type: str = "", count: int = 1):
        """获取角色随机音频"""
        params = {"count": count}
        if character:
            params["character"] = character
        if scene:
            params["scene"] = scene
        if action_type:
            params["actionType"] = action_type
        return await self.req_get(url="/df/audio/character", params=params)

    async def get_audio_categories(self):
        """获取音频分类列表"""
        return await self.req_get(url="/df/audio/categories")

    async def get_audio_characters(self):
        """获取角色列表"""
        return await self.req_get(url="/df/audio/characters")

    async def get_audio_stats(self):
        """获取音频统计信息"""
        return await self.req_get(url="/df/audio/stats")

    async def get_audio_tags(self):
        """获取特殊标签列表"""
        return await self.req_get(url="/df/audio/tags")

    # ==================== 鼠鼠音乐 API ====================

    async def get_shushu_music(self, artist: str = "", name: str = "", playlist: str = "", count: int = 1):
        """获取鼠鼠随机音乐"""
        params = {"count": count}
        if artist:
            params["artist"] = artist
        if name:
            params["name"] = name
        if playlist:
            params["playlist"] = playlist
        return await self.req_get(url="/df/audio/shushu", params=params)

    async def get_shushu_music_list(self, sort_by: str = "hot", playlist: str = "", artist: str = ""):
        """获取鼠鼠音乐列表"""
        params = {"sortBy": sort_by}
        if playlist:
            params["playlist"] = playlist
        if artist:
            params["artist"] = artist
        return await self.req_get(url="/df/audio/shushu/list", params=params)

    # ==================== 出红记录 API ====================

    async def get_red_list(self, framework_token: str):
        """获取藏品解锁记录列表"""
        return await self.req_get(url="/df/person/redlist", params={"frameworkToken": framework_token})

    async def get_red_record(self, framework_token: str, object_id: str):
        """获取指定藏品的详细记录"""
        return await self.req_get(url="/df/person/redone", params={"frameworkToken": framework_token, "objectid": object_id})

    # ==================== 健康状态 API ====================

    async def get_game_health(self, framework_token: str):
        """获取游戏角色健康状态"""
        return await self.req_get(url="/df/object/health", params={"frameworkToken": framework_token})

    # ==================== 开黑房间 API ====================

    async def get_room_list(self, room_type: str = "", has_password: str = ""):
        """获取房间列表"""
        params = {"clientID": self.clientid}
        if room_type:
            params["type"] = room_type
        if has_password:
            params["hasPassword"] = has_password
        return await self.req_get(url="/df/tools/Room/list", params=params)

    async def get_room_info(self, framework_token: str):
        """获取房间信息"""
        return await self.req_get(url="/df/tools/Room/info", params={
            "frameworkToken": framework_token, 
            "clientID": self.clientid
        })

    async def create_room(self, framework_token: str, room_type: str, map_id: str = "0", 
                          tag: str = "", password: str = "", only_current_client: bool = False):
        """创建房间"""
        return await self.req_post(url="/df/tools/Room/creat", json={
            "frameworkToken": framework_token,
            "clientID": self.clientid,
            "type": room_type,
            "mapid": map_id,
            "tag": tag,
            "password": password,
            "onlyCurrentlyClient": str(only_current_client)
        })

    async def join_room(self, framework_token: str, room_id: str, password: str = ""):
        """加入房间"""
        return await self.req_post(url="/df/tools/Room/join", json={
            "frameworkToken": framework_token,
            "clientID": self.clientid,
            "roomId": room_id,
            "password": password
        })

    async def quit_room(self, framework_token: str, room_id: str):
        """退出/解散房间"""
        return await self.req_post(url="/df/tools/Room/quit", json={
            "frameworkToken": framework_token,
            "clientID": self.clientid,
            "roomId": room_id
        })

    async def kick_member(self, framework_token: str, room_id: str, target_token: str):
        """踢出成员"""
        return await self.req_post(url="/df/tools/Room/kick", json={
            "frameworkToken": framework_token,
            "clientID": self.clientid,
            "roomId": room_id,
            "targetFrameworkToken": target_token
        })

    async def get_room_tags(self):
        """获取房间标签列表"""
        return await self.req_get(url="/df/tools/Room/tags")

    async def get_room_maps(self):
        """获取房间地图列表"""
        return await self.req_get(url="/df/tools/Room/maps")

    # ==================== 物品列表/利润V2 API ====================

    async def get_object_list(self, primary: str = "", second: str = ""):
        """获取物品列表"""
        params = {}
        if primary:
            params["primary"] = primary
        if second:
            params["second"] = second
        return await self.req_get(url="/df/object/list", params=params)

    async def get_profit_rank_v2(self, rank_type: str = "hour", place: str = ""):
        """获取利润排行榜V2（带场所分组）"""
        params = {"type": rank_type}
        if place:
            params["place"] = place
        return await self.req_get(url="/df/place/profitRank/v2", params=params)

    # ==================== 改枪方案 API ====================

    async def upload_solution(self, framework_token: str, platform_id: str, solution_code: str, 
                              desc: str = "", is_public: bool = False, solution_type: str = "sol",
                              weapon_id: str = "", accessory: str = ""):
        """上传改枪方案"""
        data = {
            "clientID": self.clientid,
            "clientType": "qq",
            "platformID": platform_id,
            "frameworkToken": framework_token,
            "solutionCode": solution_code,
            "desc": desc,
            "isPublic": is_public,
            "type": solution_type
        }
        if weapon_id:
            data["weaponId"] = weapon_id
        if accessory:
            data["Accessory"] = accessory
        return await self.req_post(url="/df/tools/solution/v2/upload", json=data)

    async def get_solution_list(self, framework_token: str, platform_id: str, weapon_id: str = "",
                                weapon_name: str = "", price_range: str = "", author_id: str = "", 
                                solution_type: str = ""):
        """获取方案列表"""
        params = {
            "clientID": self.clientid,
            "clientType": "qq",
            "platformID": platform_id,
            "frameworkToken": framework_token
        }
        if weapon_id:
            params["weaponId"] = weapon_id
        if weapon_name:
            params["weaponName"] = weapon_name
        if price_range:
            params["priceRange"] = price_range
        if author_id:
            params["authorPlatformID"] = author_id
        if solution_type:
            params["type"] = solution_type
        return await self.req_get(url="/df/tools/solution/v2/list", params=params)

    async def get_solution_detail(self, framework_token: str, platform_id: str, solution_id: str):
        """获取方案详情"""
        return await self.req_get(url="/df/tools/solution/v2/detail", params={
            "clientID": self.clientid,
            "clientType": "qq",
            "platformID": platform_id,
            "frameworkToken": framework_token,
            "solutionId": solution_id
        })

    async def vote_solution(self, framework_token: str, platform_id: str, solution_id: str, vote_type: str):
        """投票方案"""
        return await self.req_post(url="/df/tools/solution/v2/vote", json={
            "clientID": self.clientid,
            "clientType": "qq",
            "platformID": platform_id,
            "frameworkToken": framework_token,
            "solutionId": solution_id,
            "voteType": vote_type
        })

    async def delete_solution(self, framework_token: str, platform_id: str, solution_id: str):
        """删除方案"""
        return await self.req_post(url="/df/tools/solution/v2/delete", json={
            "clientID": self.clientid,
            "clientType": "qq",
            "platformID": platform_id,
            "frameworkToken": framework_token,
            "solutionId": solution_id
        })

    async def collect_solution(self, framework_token: str, platform_id: str, solution_id: str):
        """收藏方案"""
        return await self.req_post(url="/df/tools/solution/v2/collect", json={
            "clientID": self.clientid,
            "clientType": "qq",
            "platformID": platform_id,
            "frameworkToken": framework_token,
            "solutionId": solution_id
        })

    async def discollect_solution(self, framework_token: str, platform_id: str, solution_id: str):
        """取消收藏"""
        return await self.req_post(url="/df/tools/solution/v2/discollect", json={
            "clientID": self.clientid,
            "clientType": "qq",
            "platformID": platform_id,
            "frameworkToken": framework_token,
            "solutionId": solution_id
        })

    async def get_collect_list(self, framework_token: str, platform_id: str):
        """获取收藏列表"""
        return await self.req_get(url="/df/tools/solution/v2/collectlist", params={
            "clientID": self.clientid,
            "clientType": "qq",
            "platformID": platform_id,
            "frameworkToken": framework_token
        })

    ################################################################
    # OAuth 登录相关
    ################################################################
    async def login_qq_oauth_get_url(self, platform_id: str = None, bot_id: str = None):
        """QQ OAuth登录 - 获取授权链接"""
        params = {}
        if platform_id:
            params["platformID"] = platform_id
        if bot_id:
            params["botID"] = bot_id
        return await self.req_get(url="/login/qq/oauth", params=params)
    
    async def login_qq_oauth_submit(self, auth_url: str):
        """QQ OAuth登录 - 提交授权链接"""
        return await self.req_post(url="/login/qq/oauth", json={"authurl": auth_url})
    
    async def login_wechat_oauth_get_url(self, platform_id: str = None, bot_id: str = None):
        """微信OAuth登录 - 获取授权链接"""
        params = {}
        if platform_id:
            params["platformID"] = platform_id
        if bot_id:
            params["botID"] = bot_id
        return await self.req_get(url="/login/wechat/oauth", params=params)
    
    async def login_wechat_oauth_submit(self, auth_url: str):
        """微信OAuth登录 - 提交授权链接"""
        return await self.req_post(url="/login/wechat/oauth", json={"authurl": auth_url})

    async def login_qq_refresh(self, framework_token: str):
        """刷新QQ Token"""
        return await self.req_get(url="/login/qq/refresh", params={"frameworkToken": framework_token})
    
    async def login_wechat_refresh(self, framework_token: str):
        """刷新微信Token"""
        return await self.req_get(url="/login/wechat/refresh", params={"frameworkToken": framework_token})

    ################################################################
    # 文章相关
    ################################################################
    async def get_article_list(self):
        """获取文章列表"""
        return await self.req_post(url="/df/tools/article/list", json={})
    
    async def get_article_detail(self, thread_id: str):
        """获取文章详情"""
        return await self.req_get(url="/df/tools/article/detail", params={"threadID": thread_id})