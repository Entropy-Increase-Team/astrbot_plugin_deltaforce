"""
鼠鼠音乐处理器
包含：鼠鼠音乐播放、歌单、排行榜等
"""
import os
import time
from typing import Dict, Optional
from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent
import astrbot.api.message_components as Comp
from .base import BaseHandler
from ..utils.render import Render


# 音乐列表记忆（用于点歌功能）
# 结构: { userId: { list: [...], timestamp: float, type: 'rank|playlist' } }
music_list_memory: Dict[str, dict] = {}

# 音乐记忆存储（用于歌词功能）
# 结构: { userId: { music: {...}, timestamp: float } }
music_memory: Dict[str, dict] = {}

# 记忆过期时间（秒）
MEMORY_EXPIRE_TIME = 120  # 2分钟


class MusicHandler(BaseHandler):
    """鼠鼠音乐处理器"""

    def save_music_list_memory(self, user_id: str, music_list: list, list_type: str = "rank"):
        """保存音乐列表记忆"""
        music_list_memory[user_id] = {
            "list": music_list,
            "timestamp": time.time(),
            "type": list_type
        }

    def get_music_list_memory(self, user_id: str) -> Optional[dict]:
        """获取音乐列表记忆"""
        memory = music_list_memory.get(user_id)
        if not memory:
            return None
        
        # 检查是否过期
        if time.time() - memory["timestamp"] > MEMORY_EXPIRE_TIME:
            del music_list_memory[user_id]
            return None
        
        return memory

    def save_music_memory(self, user_id: str, music: dict):
        """保存当前播放音乐记忆（用于歌词查询）"""
        music_memory[user_id] = {
            "music": music,
            "timestamp": time.time()
        }

    def get_music_memory(self, user_id: str) -> Optional[dict]:
        """获取当前播放音乐记忆"""
        memory = music_memory.get(user_id)
        if not memory:
            return None
        
        # 检查是否过期
        if time.time() - memory["timestamp"] > MEMORY_EXPIRE_TIME:
            del music_memory[user_id]
            return None
        
        return memory

    async def send_music(self, event: AstrMessageEvent, args: str = ""):
        """发送鼠鼠音乐（语音形式）"""
        try:
            if args:
                args = args.strip()

            self.logger.info(f"[鼠鼠音乐] 开始获取音乐: {args}")
            result = await self.api.get_shushu_music(artist="", name=args, playlist="")
            
            if not self.is_success(result):
                self.logger.error(f"[鼠鼠音乐] API返回失败: {self.get_error_msg(result)}")
                yield self.chain_reply(event, f"❌ 获取音乐失败：{self.get_error_msg(result)}")
                return

            data = result.get("data", {})
            musics = data if isinstance(data, list) else data.get("musics", [])
            if not musics:
                self.logger.warning(f"[鼠鼠音乐] 未找到音乐: {args}")
                yield self.chain_reply(event, "未找到符合条件的音乐")
                return

            music = musics[0]
            
            # 获取音乐URL
            download = music.get("download")
            music_url = download.get("url", "") if isinstance(download, dict) else (download if isinstance(download, str) else "")
            
            if not music_url:
                self.logger.error(f"[鼠鼠音乐] 音乐URL为空")
                yield self.chain_reply(event, f"❌ 音乐URL为空")
                return

            # 保存到音乐记忆
            self.save_music_memory(event.get_sender_id(), music)
            
            # 构建音乐信息
            title = music.get("fileName") or music.get("title") or music.get("name", "未知歌曲")
            singer = music.get("artist", "未知艺术家")
            
            # 直接发送语音（音乐卡片被协议层禁止）
            from astrbot.core.message.message_event_result import MessageChain
            msg_parts = [f"♪ {title} - {singer}"]
            if music.get("playlist") and isinstance(music["playlist"], dict):
                playlist_name = music["playlist"].get("name")
                if playlist_name:
                    msg_parts.append(f"歌单: {playlist_name}")
            if music.get("metadata") and music["metadata"].get("hot"):
                msg_parts.append(f"🔥 {music['metadata']['hot']}")
            
            await event.send(MessageChain([Comp.Plain("\n".join(msg_parts))]))

            # 尝试发送 OneBot 音乐卡片
            if await self._try_send_music_card(event, music, music_url):
                return

            self.logger.info("[鼠鼠音乐] 音乐卡片发送未成功，正在回退到语音发送方案...")

            # 如果卡片发送失败（或者不支持），回退到发送语音
            # 修复：下载音频文件发送，避免 URL 发送出现 retcode=1200
            file_path = None
            try:
                self.logger.info(f"[鼠鼠音乐] 开始下载音乐用于语音发送: {title}")
                import aiohttp
                import tempfile
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(music_url) as resp:
                        if resp.status == 200:
                            data = await resp.read()
                            # 简单判断后缀
                            suffix = ".mp3"
                            if ".m4a" in music_url:
                                suffix = ".m4a"
                            elif ".wav" in music_url:
                                suffix = ".wav"
                                
                            fd, file_path = tempfile.mkstemp(suffix=suffix)
                            os.close(fd)
                            with open(file_path, "wb") as f:
                                f.write(data)
                            self.logger.info(f"[鼠鼠音乐] 音乐下载成功: {file_path}")
                        else:
                            self.logger.warning(f"[鼠鼠音乐] 下载音乐失败: status {resp.status}")
            except Exception as e:
                self.logger.warning(f"[鼠鼠音乐] 下载音乐异常，尝试直接使用URL发送: {e}")
            
            if file_path:
                try:
                    await event.send(MessageChain([Comp.Record(file=file_path)]))
                except Exception as e:
                    self.logger.error(f"[鼠鼠音乐] 发送本地音乐文件失败: {e}")
                    # 如果发送本地文件失败，尝试发送 URL
                    await event.send(MessageChain([Comp.Record(file=music_url)]))
                finally:
                    # 清理临时文件
                    try:
                        os.remove(file_path)
                    except:
                        pass
            else:
                self.logger.info("[鼠鼠音乐] 无本地文件，尝试直接发送 URL")
                await event.send(MessageChain([Comp.Record(file=music_url)]))

            self.logger.info(f"[鼠鼠音乐] 语音发送完成: {title}")

        except Exception as e:
            self.logger.error(f"[鼠鼠音乐] 发送音乐异常: {e}", exc_info=True)
            yield self.chain_reply(event, f"❌ 发送音乐失败：{e}")

    async def _try_send_music_card(self, event: AstrMessageEvent, music: dict, music_url: str) -> bool:
        """尝试发送 OneBot 音乐卡片"""
        try:
            self.logger.info("[鼠鼠音乐] 尝试构造并发送音乐卡片...")
            bot = getattr(event, "bot", None) 
            if not bot:
                self.logger.warning("[鼠鼠音乐] API不支持: 无法获取 bot 对象")
                return False
            
            call_action = getattr(bot, "call_action", None)
            if not call_action and hasattr(bot, "api"):
                call_action = getattr(bot.api, "call_action", None)
            if not call_action:
                self.logger.warning("[鼠鼠音乐] API不支持: 无法获取 call_action 接口")
                return False

            title = music.get("fileName") or music.get("title") or "未知歌曲"
            singer = music.get("artist") or "未知艺术家"
            cover = music.get("metadata", {}).get("cover", "")
            jump_url = "https://shushu.fan"

            payload = {
                "type": "music",
                "data": {
                    "type": "custom", 
                    "url": jump_url,
                    "audio": music_url,
                    "title": title,
                    "image": cover,
                    "content": singer  # OneBot v11 custom music uses 'content' for singer/desc
                }
            }
            
            def parse_id(s):
                if not s: return 0
                s = str(s)
                if ":" in s: return int(s.split(":")[-1])
                try: return int(s)
                except: return 0

            uid = parse_id(event.get_sender_id())
            gid = 0
            if hasattr(event, "get_group_id") and event.get_group_id():
                gid = parse_id(event.get_group_id())
            
            self.logger.info(f"[鼠鼠音乐] 准备发送卡片 (UID: {uid}, GID: {gid}) Payload: {payload}")
            
            # 使用 call_action 直接调用协议端接口，绕过框架可能的封装转换
            if gid: 
                await call_action("send_group_msg", group_id=gid, message=[payload])
            else: 
                await call_action("send_private_msg", user_id=uid, message=[payload])
            
            self.logger.info(f"[鼠鼠音乐] 音乐卡片发送请求调用成功")
            return True
        except Exception as e:
            self.logger.warning(f"[鼠鼠音乐] 音乐卡片发送失败，将回退到语音发送: {e}")
            return False

    async def get_music_list(self, event: AstrMessageEvent, args: str = ""):
        """获取音乐列表/排行榜"""
        try:
            # 解析参数
            sort_by = "hot"  # 默认热门排行
            playlist = ""
            page = 1
            
            if args:
                parts = args.strip().split()
                for part in parts:
                    if part.isdigit():
                        page = int(part)
                    elif part in ["hot", "热门", "default", "默认"]:
                        sort_by = "hot" if part in ["hot", "热门"] else "default"

            result = await self.api.get_shushu_music_list(sort_by=sort_by, playlist=playlist)
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 获取音乐列表失败：{self.get_error_msg(result)}")
                return

            data = result.get("data", {})
            # 处理 data 可能是列表或字典的情况
            if isinstance(data, list):
                musics = data
            else:
                musics = data.get("musics", [])
            if not musics:
                yield self.chain_reply(event, "暂无音乐数据")
                return

            # 保存列表到用户记忆（用于点歌功能）
            user_id = event.get_sender_id()
            self.save_music_list_memory(user_id, musics, "rank")

            # 分页显示
            page_size = 10
            start = (page - 1) * page_size
            end = start + page_size
            page_musics = musics[start:end]
            total_pages = (len(musics) + page_size - 1) // page_size

            # 处理音乐数据用于渲染
            processed_musics = []
            for i, music in enumerate(page_musics, start + 1):
                # 获取封面URL
                cover_url = ""
                if music.get("metadata") and music["metadata"].get("cover"):
                    cover_url = music["metadata"]["cover"]
                
                # 获取热度
                hot_value = None
                if music.get("metadata") and music["metadata"].get("hot"):
                    hot_value = music["metadata"]["hot"]
                
                # 获取歌单名称
                playlist_name = ""
                if music.get("playlist") and isinstance(music["playlist"], dict):
                    playlist_name = music["playlist"].get("name", "")
                
                processed_musics.append({
                    'index': i,
                    'name': music.get("fileName") or music.get("title") or music.get("name", "未知"),
                    'artist': music.get("artist", "未知"),
                    'cover': cover_url,
                    'hot': hot_value,
                    'playlist': playlist_name,
                })

            render_data = {
                'backgroundImage': Render.get_background_image(),
                'listTitle': '鼠鼠音乐排行榜' if sort_by == 'hot' else '鼠鼠音乐列表',
                'subtitle': f"第 {page}/{total_pages} 页",
                'totalCount': len(musics),
                'musicList': processed_musics,
            }

            # 尝试渲染图片
            yield await self.render_and_reply(
                event,
                'musicList/musicList.html',
                render_data,
                fallback_text=self._build_music_list_text(page, total_pages, page_musics, start),
width=1200,
            height=1000
            )

        except Exception as e:
            yield self.chain_reply(event, f"❌ 获取音乐列表失败：{e}")

    def _build_music_list_text(self, page, total_pages, page_musics, start):
        """构建纯文本音乐列表（渲染失败时的回退）"""
        lines = [f"🎵【鼠鼠音乐排行榜】第 {page}/{total_pages} 页", ""]
        
        for i, music in enumerate(page_musics, start + 1):
            title = music.get("title") or music.get("name", "未知")
            artist = music.get("artist", "未知")
            play_count = music.get("playCount", 0)
            lines.append(f"{i}. {title} - {artist}")
            if play_count:
                lines.append(f"   播放: {play_count:,}")

        lines.append("")
        lines.append(f"💡 使用 /三角洲 点歌 <序号> 播放")
        lines.append(f"💡 使用 /三角洲 鼠鼠音乐列表 <页码> 翻页")
        
        return "\n".join(lines)

    async def get_playlist(self, event: AstrMessageEvent, playlist_name: str = ""):
        """获取歌单"""
        try:
            result = await self.api.get_shushu_music_list(playlist=playlist_name)
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 获取歌单失败：{self.get_error_msg(result)}")
                return

            data = result.get("data", {})
            # 处理 data 可能是列表或字典的情况
            if isinstance(data, list):
                musics = data
                playlists = []
            else:
                musics = data.get("musics", [])
                playlists = data.get("playlists", [])

            if playlists and not playlist_name:
                # 显示歌单列表
                lines = ["📋【鼠鼠歌单列表】", ""]
                for pl in playlists[:15]:
                    name = pl.get("name", "未知")
                    count = pl.get("count", 0)
                    lines.append(f"• {name} ({count}首)")
                lines.append("")
                lines.append("💡 使用 /三角洲鼠鼠歌单 <歌单名> 查看详情")
                yield self.chain_reply(event, "\n".join(lines))
                return

            if not musics:
                yield self.chain_reply(event, f"歌单 [{playlist_name}] 暂无音乐")
                return

            # 保存列表到用户记忆（用于点歌功能）
            user_id = event.get_sender_id()
            self.save_music_list_memory(user_id, musics, "playlist")

            lines = [f"📋【歌单: {playlist_name}】共 {len(musics)} 首", ""]
            for i, music in enumerate(musics[:15], 1):
                title = music.get("title") or music.get("name", "未知")
                artist = music.get("artist", "未知")
                lines.append(f"{i}. {title} - {artist}")

            if len(musics) > 15:
                lines.append(f"... 等共 {len(musics)} 首")

            yield self.chain_reply(event, "\n".join(lines))

        except Exception as e:
            yield self.chain_reply(event, f"❌ 获取歌单失败：{e}")

    async def select_music_by_number(self, event: AstrMessageEvent, number: str = ""):
        """点歌功能 - 通过序号选择音乐"""
        try:
            user_id = event.get_sender_id()
            
            # 检查序号
            if not number or not number.isdigit():
                yield self.chain_reply(event, "请输入有效的数字序号\n例如: /三角洲点歌 1")
                return
            
            num = int(number)
            
            # 获取列表记忆
            memory = self.get_music_list_memory(user_id)
            if not memory:
                yield self.chain_reply(event, "您还没有获取音乐列表\n请先使用:\n• /三角洲音乐列表\n• /三角洲鼠鼠歌单 [歌单名]")
                return
            
            music_list = memory["list"]
            
            # 检查序号范围
            if num < 1 or num > len(music_list):
                yield self.chain_reply(event, f"序号超出范围\n请输入 1-{len(music_list)} 之间的数字")
                return
            
            # 获取选中的音乐
            music = music_list[num - 1]
            
            # 获取音乐URL
            music_url = ""
            if music.get("download"):
                download = music.get("download")
                if isinstance(download, dict):
                    music_url = download.get("url", "")
                elif isinstance(download, str):
                    music_url = download
            
            if not music_url:
                yield self.chain_reply(event, "❌ 该音乐暂无可播放链接")
                return
            
            # 保存到音乐记忆（用于歌词功能）
            self.save_music_memory(user_id, music)
            
            # 构建音乐信息
            title = music.get("fileName") or music.get("title") or music.get("name", "未知歌曲")
            singer = music.get("artist", "未知艺术家")
            preview = music.get("metadata", {}).get("cover", "") if music.get("metadata") else ""
            jump_url = "https://shushu.fan"
            
            # 先尝试发送音乐卡片
            if await self._try_send_music_card(event, music, music_url):
                return

            # 如果卡片发送失败（或者不支持），回退到发送语音
            self.logger.info(f"[点歌] 音乐卡片发送未成功，正在回退到语音发送方案...")
            
            from astrbot.core.message.message_event_result import MessageChain
            msg_parts = [f"♪ {title} - {singer}"]
            if music.get("playlist") and isinstance(music["playlist"], dict):
                playlist_name = music["playlist"].get("name")
                if playlist_name:
                    msg_parts.append(f"歌单: {playlist_name}")
            if music.get("metadata") and music["metadata"].get("hot"):
                msg_parts.append(f"🔥 {music['metadata']['hot']}")
            
            await event.send(MessageChain([Comp.Plain("\n".join(msg_parts))]))

            # 修复：下载音频文件发送，避免 URL 发送出现 retcode=1200
            file_path = None
            try:
                self.logger.info(f"[点歌] 开始下载音乐用于语音发送: {title}")
                import aiohttp
                import tempfile
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(music_url) as resp:
                        if resp.status == 200:
                            data = await resp.read()
                            # 简单判断后缀
                            suffix = ".mp3"
                            if ".m4a" in music_url:
                                suffix = ".m4a"
                            elif ".wav" in music_url:
                                suffix = ".wav"
                                
                            fd, file_path = tempfile.mkstemp(suffix=suffix)
                            os.close(fd)
                            with open(file_path, "wb") as f:
                                f.write(data)
                            self.logger.info(f"[点歌] 音乐下载成功: {file_path}")
                        else:
                            self.logger.warning(f"[点歌] 下载音乐失败: status {resp.status}")
            except Exception as e:
                self.logger.warning(f"[点歌] 下载音乐异常，尝试直接使用URL发送: {e}")
            
            if file_path:
                try:
                    await event.send(MessageChain([Comp.Record(file=file_path)]))
                except Exception as e:
                    self.logger.error(f"[点歌] 发送本地音乐文件失败: {e}")
                    # 如果发送本地文件失败，尝试发送 URL
                    await event.send(MessageChain([Comp.Record(file=music_url)]))
                finally:
                    # 清理临时文件
                    try:
                        os.remove(file_path)
                    except:
                        pass
            else:
                self.logger.info("[点歌] 无本地文件，尝试直接发送 URL")
                await event.send(MessageChain([Comp.Record(file=music_url)]))
                
            self.logger.info(f"[点歌] 语音发送完成: {title}")

        except Exception as e:
            yield self.chain_reply(event, f"❌ 点歌失败：{e}")

    async def get_lyrics(self, event: AstrMessageEvent):
        """获取歌词"""
        try:
            user_id = event.get_sender_id()
            
            # 获取音乐记忆
            memory = self.get_music_memory(user_id)
            if not memory:
                yield self.chain_reply(event, "暂无最近播放的音乐记录\n请先播放一首歌曲")
                return
            
            music = memory["music"]
            title = music.get("title") or music.get("name") or music.get("fileName", "未知歌曲")
            
            # 获取歌词链接
            lrc_url = None
            if music.get("metadata"):
                lrc_url = music["metadata"].get("lrc")
            if not lrc_url:
                lrc_url = music.get("lrc") or music.get("lyrics_url")
            
            if not lrc_url:
                yield self.chain_reply(event, f"歌曲「{title}」暂无歌词")
                return
            
            # 下载歌词
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(lrc_url) as resp:
                    if resp.status != 200:
                        yield self.chain_reply(event, "获取歌词失败")
                        return
                    lrc_content = await resp.text()
            
            # 解析LRC格式
            lyrics = self._parse_lrc(lrc_content)
            
            if not lyrics:
                yield self.chain_reply(event, f"歌曲「{title}」暂无歌词内容")
                return
            
            artist = music.get("artist", "")
            header = f"【{title}】"
            if artist:
                header += f"\n演唱：{artist}"
            
            yield self.chain_reply(event, f"{header}\n\n{lyrics}")

        except Exception as e:
            yield self.chain_reply(event, f"❌ 获取歌词失败：{e}")

    def _parse_lrc(self, lrc_content: str) -> str:
        """解析LRC格式歌词"""
        import re
        lines = lrc_content.split('\n')
        lyrics = []
        
        for line in lines:
            # 移除时间标签，提取歌词
            match = re.match(r'\[(\d+):(\d+)\.(\d+)\](.*)', line)
            if match and match.group(4).strip():
                lyrics.append(match.group(4).strip())
            else:
                # 处理元数据行（如：[ti:歌名]）
                meta_match = re.match(r'\[(ti|ar|al|by):(.+)\]', line)
                if not meta_match and line.strip() and not line.startswith('['):
                    lyrics.append(line.strip())
        
        return '\n'.join(lyrics) if lyrics else ""

    async def send_voice(self, event: AstrMessageEvent):
        """发送鼠鼠语音（随机）"""
        try:
            user_id = event.get_sender_id()
            
            # 修改：不使用记忆，总是随机获取
            yield self.chain_reply(event, "正在获取随机鼠鼠音乐...")
            result = await self.api.get_shushu_music(count=1)
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 获取音乐失败：{self.get_error_msg(result)}")
                return
            
            data = result.get("data", {})
            musics = data.get("musics", []) if isinstance(data, dict) else data
            if not musics:
                yield self.chain_reply(event, "未找到音乐")
                return
            
            music = musics[0]
            
            # 获取音乐URL
            music_url = (
                music.get("url") or 
                music.get("audioUrl") or 
                music.get("audio_url") or 
                ""
            )
            if not music_url and music.get("download"):
                download = music.get("download")
                if isinstance(download, dict):
                    music_url = download.get("url", "")
            
            if not music_url:
                yield self.chain_reply(event, "❌ 音乐URL为空")
                return
            
            title = music.get("title") or music.get("name") or music.get("fileName", "未知歌曲")
            artist = music.get("artist", "")
            
            # 保存记忆 (用于歌词)
            self.save_music_memory(user_id, music)
            
            # 使用下载方式发送语音，避免 retcode=1200
            file_path = None
            try:
                import aiohttp
                import tempfile
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(music_url) as resp:
                        if resp.status == 200:
                            data = await resp.read()
                            # 简单判断后缀
                            suffix = ".mp3"
                            if ".m4a" in music_url:
                                suffix = ".m4a"
                            elif ".wav" in music_url:
                                suffix = ".wav"
                                
                            fd, file_path = tempfile.mkstemp(suffix=suffix)
                            os.close(fd)
                            with open(file_path, "wb") as f:
                                f.write(data)
                        else:
                            self.logger.warning(f"[鼠鼠语音] 下载音乐失败: status {resp.status}")
            except Exception as e:
                self.logger.warning(f"[鼠鼠语音] 下载音乐异常: {e}")

            from astrbot.core.message.message_event_result import MessageChain
            msg_parts = [f"🎵 {title}" + (f" - {artist}" if artist else "")]
            
            await event.send(MessageChain([Comp.Plain("\n".join(msg_parts))]))
            
            if file_path:
                try:
                    await event.send(MessageChain([Comp.Record(file=file_path)]))
                except Exception as e:
                    self.logger.error(f"[鼠鼠语音] 发送本地语音失败: {e}")
                    await event.send(MessageChain([Comp.Record(file=music_url)]))
                finally:
                    try: os.remove(file_path)
                    except: pass
            else:
                await event.send(MessageChain([Comp.Record(file=music_url)]))

        except Exception as e:
            yield self.chain_reply(event, f"❌ 发送语音失败：{e}")
