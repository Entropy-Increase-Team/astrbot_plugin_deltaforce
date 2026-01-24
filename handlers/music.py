"""
鼠鼠音乐处理器
包含：鼠鼠音乐播放、歌单、排行榜等
"""
from astrbot.api.event import AstrMessageEvent
import astrbot.api.message_components as Comp
from .base import BaseHandler
from ..utils.render import Render


class MusicHandler(BaseHandler):
    """鼠鼠音乐处理器"""

    async def send_music(self, event: AstrMessageEvent, args: str = ""):
        """发送鼠鼠音乐"""
        try:
            # 解析参数
            artist = ""
            name = ""
            playlist = ""
            
            if args:
                # 简单解析：可能是艺术家、歌曲名或歌单
                args = args.strip()
                # 这里简化处理，直接当作搜索词
                name = args

            result = await self.api.get_shushu_music(artist=artist, name=name, playlist=playlist)
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 获取音乐失败：{result.get('msg', '未知错误')}")
                return

            musics = result.get("data", {}).get("musics", [])
            if not musics:
                yield self.chain_reply(event, "未找到符合条件的音乐")
                return

            music = musics[0]
            music_url = music.get("url", "")
            if not music_url:
                yield self.chain_reply(event, "❌ 音乐URL为空")
                return

            # 构建音乐信息
            title = music.get("title") or music.get("name", "未知歌曲")
            artist_name = music.get("artist", "未知艺术家")
            
            yield event.chain_result([
                Comp.Plain(f"🎵 {title}\n🎤 {artist_name}\n"),
                Comp.Record(file=music_url)
            ])

        except Exception as e:
            yield self.chain_reply(event, f"❌ 发送音乐失败：{e}")

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
                yield self.chain_reply(event, f"❌ 获取音乐列表失败：{result.get('msg', '未知错误')}")
                return

            musics = result.get("data", {}).get("musics", [])
            if not musics:
                yield self.chain_reply(event, "暂无音乐数据")
                return

            # 分页显示
            page_size = 10
            start = (page - 1) * page_size
            end = start + page_size
            page_musics = musics[start:end]
            total_pages = (len(musics) + page_size - 1) // page_size

            # 处理音乐数据用于渲染
            processed_musics = []
            for i, music in enumerate(page_musics, start + 1):
                processed_musics.append({
                    'index': i,
                    'name': music.get("title") or music.get("name", "未知"),
                    'artist': music.get("artist", "未知"),
                    'cover': music.get("cover", ""),
                    'hot': f"{music.get('playCount', 0):,}" if music.get("playCount") else None,
                    'playlist': music.get("playlist", ""),
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
                yield self.chain_reply(event, f"❌ 获取歌单失败：{result.get('msg', '未知错误')}")
                return

            musics = result.get("data", {}).get("musics", [])
            playlists = result.get("data", {}).get("playlists", [])

            if playlists and not playlist_name:
                # 显示歌单列表
                lines = ["📋【鼠鼠歌单列表】", ""]
                for pl in playlists[:15]:
                    name = pl.get("name", "未知")
                    count = pl.get("count", 0)
                    lines.append(f"• {name} ({count}首)")
                lines.append("")
                lines.append("💡 使用 /三角洲 鼠鼠歌单 <歌单名> 查看详情")
                yield self.chain_reply(event, "\n".join(lines))
                return

            if not musics:
                yield self.chain_reply(event, f"歌单 [{playlist_name}] 暂无音乐")
                return

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
