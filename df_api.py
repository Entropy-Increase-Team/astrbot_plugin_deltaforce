import aiohttp
import asyncio
import json
import logging
from typing import Optional, Dict, Any, List, Set

logger = logging.getLogger(__name__)


class ServerError(Exception):
    """服务器错误异常（5xx），用于触发重试和地址切换"""
    def __init__(self, status_code: int, message: str = ""):
        self.status_code = status_code
        self.message = message
        super().__init__(f"服务器错误 ({status_code}): {message}")


class ApiUrlManager:
    """
    API URL 管理器
    负责管理多个后端地址，支持故障转移和模式切换
    使用 Timeout 机制和重试逻辑
    """
    
    # 三个后端地址
    URLS = {
        "default": "https://df-api.shallow.ink",
        "eo": "https://df-api-eo.shallow.ink",
        "esa": "https://df-api-esa.shallow.ink"
    }
    
    # 有效模式列表
    VALID_MODES = ["auto", "default", "eo", "esa"]
    
    def __init__(self, mode: str = "auto", timeout: int = 30, retry_count: int = 3):
        """
        初始化 API URL 管理器
        
        Args:
            mode: API模式 ('auto' | 'default' | 'eo' | 'esa')
            timeout: 请求超时时间（秒）
            retry_count: 每个地址的重试次数
        """
        self._mode = mode if mode in self.VALID_MODES else "auto"
        self.timeout = timeout
        self.retry_count = retry_count
        self.failed_urls: Set[str] = set()
    
    @property
    def mode(self) -> str:
        return self._mode
    
    @mode.setter
    def mode(self, value: str):
        if value in self.VALID_MODES:
            self._mode = value
            self.failed_urls.clear()
        else:
            logger.warning(f"[ApiUrlManager] 无效的模式: {value}，使用默认 auto")
            self._mode = "auto"
    
    def get_available_urls(self) -> List[str]:
        """获取可用的地址列表（过滤掉失败的地址）"""
        if self._mode == "auto":
            # 优先使用 eo 和 esa，default 作为备用
            urls = [self.URLS["eo"], self.URLS["esa"], self.URLS["default"]]
        else:
            urls = [self.URLS.get(self._mode, self.URLS["default"])]
        
        return [url for url in urls if url not in self.failed_urls]
    
    def get_base_url(self) -> str:
        """获取当前应该使用的 API 地址"""
        available_urls = self.get_available_urls()
        return available_urls[0] if available_urls else self.URLS["default"]
    
    def mark_url_failed(self, url: str):
        """标记地址为失败"""
        self.failed_urls.add(url)
        logger.warning(f"[ApiUrlManager] 标记地址为失败: {url}")
    
    def reset_failures(self):
        """重置所有失败记录"""
        self.failed_urls.clear()
        logger.info("[ApiUrlManager] 已重置所有失败记录")
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态信息（用于调试）"""
        available_urls = self.get_available_urls()
        return {
            "mode": self._mode,
            "current_url": available_urls[0] if available_urls else self.URLS["default"],
            "available_urls": available_urls,
            "failed_urls": list(self.failed_urls),
            "total_urls": 3 if self._mode == "auto" else 1
        }


class DeltaForceAPI:
    """三角洲 API 封装类"""
    
    def __init__(self, token: str, clientid: str, api_mode: str = "auto", 
                 timeout: int = 30, retry_count: int = 3):
        """
        初始化 API 客户端
        
        Args:
            token: API 授权令牌
            clientid: 客户端ID
            api_mode: API模式 ('auto' | 'default' | 'eo' | 'esa')
            timeout: 请求超时时间（秒）
            retry_count: 重试次数
        """
        self.token = token
        self.clientid = clientid
        self.url_manager = ApiUrlManager(mode=api_mode, timeout=timeout, retry_count=retry_count)
    
    def set_api_mode(self, mode: str):
        """设置API模式"""
        self.url_manager.mode = mode
    
    def get_api_status(self) -> Dict[str, Any]:
        """获取API状态信息"""
        return self.url_manager.get_status()
    
    async def _make_request(self, method: str, url: str, params: Optional[Dict] = None,
                            json_data: Optional[Dict] = None, form_data: Optional[Dict] = None,
                            auth: bool = True) -> Dict:
        """
        统一的请求方法，支持自动重试和故障转移
        
        Args:
            method: HTTP方法 ('GET' 或 'POST')
            url: API路径（不含基础URL）
            params: URL参数
            json_data: JSON请求体
            form_data: 表单数据
            auth: 是否需要鉴权 Header
        
        Returns:
            API响应结果
        """
        headers = {}
        if auth and self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        # 获取可用地址列表
        available_urls = self.url_manager.get_available_urls()
        
        # 如果没有可用地址，重置失败记录并重新获取
        if not available_urls:
            logger.warning("[ApiUrlManager] 所有地址都标记为失败，重置失败记录")
            self.url_manager.reset_failures()
            available_urls = self.url_manager.get_available_urls()
        
        last_error = None
        last_result = None
        
        # 遍历所有可用地址
        for base_url in available_urls:
            # 对当前地址重试指定次数
            for attempt in range(1, self.url_manager.retry_count + 1):
                try:
                    full_url = f"{base_url}{url}"
                    timeout = aiohttp.ClientTimeout(total=self.url_manager.timeout)
                    
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        if method.upper() == "GET":
                            async with session.get(full_url, headers=headers, params=params) as response:
                                result = await self._handle_response(response)
                                # 请求成功（业务成功）
                                if result.get("code") == 200 or result.get("code") == 0:
                                    logger.debug(f"[ApiUrlManager] 请求成功: {base_url}")
                                    return result
                                # 5xx服务器错误，应该重试和切换地址
                                status_code = result.get("code", 0)
                                if 500 <= status_code < 600:
                                    last_error = f"服务器错误 ({status_code})"
                                    last_result = result
                                    logger.warning(f"[ApiUrlManager] 地址 {base_url} 第 {attempt} 次请求返回 {status_code}")
                                    # 继续重试，不直接返回
                                    raise ServerError(status_code, result.get("msg", "服务器错误"))
                                # 其他非5xx错误（如400、401、403、404等），直接返回，不重试
                                return result
                        else:  # POST
                            async with session.post(full_url, headers=headers, 
                                                   json=json_data, data=form_data) as response:
                                result = await self._handle_response(response)
                                # 请求成功（业务成功）
                                if result.get("code") == 200 or result.get("code") == 0:
                                    logger.debug(f"[ApiUrlManager] 请求成功: {base_url}")
                                    return result
                                # 5xx服务器错误，应该重试和切换地址
                                status_code = result.get("code", 0)
                                if 500 <= status_code < 600:
                                    last_error = f"服务器错误 ({status_code})"
                                    last_result = result
                                    logger.warning(f"[ApiUrlManager] 地址 {base_url} 第 {attempt} 次请求返回 {status_code}")
                                    # 继续重试，不直接返回
                                    raise ServerError(status_code, result.get("msg", "服务器错误"))
                                # 其他非5xx错误（如400、401、403、404等），直接返回，不重试
                                return result
                
                except ServerError as e:
                    last_error = str(e)
                    # ServerError表示5xx错误，继续重试逻辑
                except asyncio.TimeoutError:
                    last_error = f"请求超时 ({self.url_manager.timeout}s)"
                    logger.warning(f"[ApiUrlManager] 地址 {base_url} 第 {attempt} 次请求超时")
                except aiohttp.ClientError as e:
                    last_error = str(e)
                    logger.warning(f"[ApiUrlManager] 地址 {base_url} 第 {attempt} 次请求失败: {e}")
                except Exception as e:
                    # 避免捕获ServerError以外的自定义异常
                    if isinstance(e, ServerError):
                        last_error = str(e)
                    else:
                        last_error = str(e)
                        logger.warning(f"[ApiUrlManager] 地址 {base_url} 第 {attempt} 次请求异常: {e}")
                
                # 如果不是最后一次重试，等待后继续
                if attempt < self.url_manager.retry_count:
                    await asyncio.sleep(0.5 * attempt)  # 递增等待时间
            
            # 当前地址所有重试都失败，标记为失败并尝试下一个地址
            logger.error(f"[ApiUrlManager] 地址 {base_url} 重试 {self.url_manager.retry_count} 次后仍然失败")
            self.url_manager.mark_url_failed(base_url)
            logger.info(f"[ApiUrlManager] 切换到下一个可用地址")
        
        # 所有地址都失败
        if last_result:
            return last_result
        return {"code": -1, "msg": f"所有 API 地址都请求失败: {last_error}", "data": None}
    
    async def _handle_response(self, response: aiohttp.ClientResponse) -> Dict:
        """处理响应"""
        if response.status != 200:
            text = await response.text()
            if "<html" in text.lower() or "<!doctype" in text.lower():
                error_msg = f"服务器错误 ({response.status})"
            else:
                error_msg = text[:200] if len(text) > 200 else text
            return {"code": response.status, "msg": error_msg, "data": None}
        
        try:
            return await response.json()
        except (aiohttp.ContentTypeError, json.JSONDecodeError):
            text = await response.text()
            if "<html" in text.lower() or "<!doctype" in text.lower():
                error_msg = "服务器返回了无效响应"
            else:
                error_msg = f"响应格式错误: {text[:100]}"
            return {"code": response.status, "msg": error_msg, "data": None}
    
    async def req_get(self, url: str, params: Optional[Dict] = None, auth: bool = True) -> Dict:
        """GET 请求"""
        return await self._make_request("GET", url, params=params, auth=auth)
    
    async def req_post(self, url: str, json: Optional[Dict] = None, data: Optional[Dict] = None, auth: bool = True) -> Dict:
        """POST 请求"""
        return await self._make_request("POST", url, json_data=json, form_data=data, auth=auth)

    ################################################################
    async def user_bind(self, platformId:str, frameworkToken:str):
        return await self.req_post(
            url = "/user/bind",
            json = {
                "platformID": platformId,
                "frameworkToken": frameworkToken,
                "clientID": self.clientid,
                "clientType": "AstrBot"
            }
        )

    async def user_unbind(self, platformId:str, frameworkToken:str):
        return await self.req_post(
            url = "/user/unbind",
            json = {
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
            url="/login/qq/ck/status", 
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
                "token": frameworkToken
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

    async def get_personal_info(self, frameworkToken: str, seasonid: str = ""):
        """获取个人信息"""
        params = {"frameworkToken": frameworkToken}
        if seasonid:
            params["seasonid"] = seasonid
        return await self.req_get(
            url="/df/person/personalinfo",
            params=params
        )

    async def get_personal_data(self, frameworkToken: str, mode: str = "", season: str = "7"):
        """获取个人数据（烽火地带和全面战场）"""
        params = {"frameworkToken": frameworkToken}
        if mode:
            params["type"] = mode
        if season != "all":
            params["seasonid"] = season
        return await self.req_get(url="/df/person/PersonalData", params=params)

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
        import json
        # API expects JSON array format like ["id1","id2"]
        if "," in object_ids:
            ids_list = [id.strip() for id in object_ids.split(",")]
            id_param = json.dumps(ids_list)
        else:
            id_param = json.dumps([object_ids])
        return await self.req_get(
            url="/df/object/price/latest",
            params={"id": id_param}
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
        return await self.req_get(url="/df/person/dailyRecord", params=params)

    async def get_weekly_record(self, framework_token: str, mode: str = "", is_show_null_friend: bool = False, date: str = ""):
        """获取周报数据"""
        params = {"frameworkToken": framework_token}
        if mode:
            params["type"] = mode
        if is_show_null_friend:
            params["isShowNullFriend"] = "true"
        if date:
            params["date"] = date
        return await self.req_get(url="/df/person/weeklyRecord", params=params)

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
