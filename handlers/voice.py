"""
游戏语音处理器
包含：随机语音、角色语音、标签语音等
"""
from astrbot.api.event import AstrMessageEvent
import astrbot.api.message_components as Comp
from .base import BaseHandler


class VoiceHandler(BaseHandler):
    """游戏语音处理器"""

    # 场景映射
    SCENE_MAP = {
        "局内": "InGame", "局外": "OutGame",
        "ingame": "InGame", "outgame": "OutGame"
    }

    # 动作类型映射
    ACTION_MAP = {
        "呼吸": "Breath", "战斗": "Combat", "死亡": "Death", "受伤": "Pain",
        "breath": "Breath", "combat": "Combat", "death": "Death", "pain": "Pain"
    }

    async def send_voice(self, event: AstrMessageEvent, args: str = ""):
        """发送随机语音"""
        params = self._parse_voice_params(args)
        
        try:
            if params.get("category"):
                result = await self.api.get_random_audio(category=params["category"])
            elif params.get("tag"):
                result = await self.api.get_random_audio(tag=params["tag"])
            elif params.get("character") or params.get("scene") or params.get("action_type"):
                result = await self.api.get_character_audio(
                    character=params.get("character", ""),
                    scene=params.get("scene", ""),
                    action_type=params.get("action_type", "")
                )
            else:
                result = await self.api.get_random_audio()

            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 获取语音失败：{result.get('msg', '未知错误')}")
                return

            audios = result.get("data", {}).get("audios", [])
            if not audios:
                yield self.chain_reply(event, "未找到符合条件的语音\n使用 /三角洲 语音列表 查看可用内容")
                return

            audio = audios[0]
            audio_url = audio.get("url", "")
            if not audio_url:
                yield self.chain_reply(event, "❌ 语音URL为空")
                return

            # 构建语音信息
            char_name = audio.get("character", "未知")
            scene = audio.get("scene", "")
            action = audio.get("actionType", "")
            
            info_parts = [f"🎙️ {char_name}"]
            if scene:
                info_parts.append(f"场景: {scene}")
            if action:
                info_parts.append(f"动作: {action}")

            yield event.chain_result([
                Comp.Plain(" | ".join(info_parts) + "\n"),
                Comp.Record(file=audio_url)
            ])

        except Exception as e:
            yield self.chain_reply(event, f"❌ 发送语音失败：{e}")

    def _parse_voice_params(self, args: str) -> dict:
        """解析语音参数"""
        if not args:
            return {}

        parts = args.strip().split()
        result = {}

        if parts:
            first = parts[0]
            # 检查场景
            if first in self.SCENE_MAP or first.lower() in self.SCENE_MAP:
                result["scene"] = self.SCENE_MAP.get(first) or self.SCENE_MAP.get(first.lower())
            # 检查动作
            elif first in self.ACTION_MAP or first.lower() in self.ACTION_MAP:
                result["action_type"] = self.ACTION_MAP.get(first) or self.ACTION_MAP.get(first.lower())
            else:
                # 默认当作角色名
                result["character"] = first

        if len(parts) > 1:
            second = parts[1]
            if second in self.SCENE_MAP or second.lower() in self.SCENE_MAP:
                result["scene"] = self.SCENE_MAP.get(second) or self.SCENE_MAP.get(second.lower())
            elif second in self.ACTION_MAP or second.lower() in self.ACTION_MAP:
                result["action_type"] = self.ACTION_MAP.get(second) or self.ACTION_MAP.get(second.lower())

        return result

    async def get_voice_characters(self, event: AstrMessageEvent):
        """获取角色列表"""
        result = await self.api.get_audio_characters()
        if not self.is_success(result):
            yield self.chain_reply(event, f"❌ 获取失败：{result.get('msg', '未知错误')}")
            return

        characters = result.get("data", [])
        if not characters:
            yield self.chain_reply(event, "暂无角色数据")
            return

        lines = ["🎭【语音角色列表】", ""]
        for i, char in enumerate(characters[:30], 1):
            name = char.get("name") or char.get("character", "未知")
            count = char.get("count", 0)
            lines.append(f"{i}. {name} ({count}条)")

        if len(characters) > 30:
            lines.append(f"... 等共 {len(characters)} 个角色")

        lines.append("")
        lines.append("💡 用法：/三角洲 语音 <角色名> [场景] [动作]")

        yield self.chain_reply(event, "\n".join(lines))

    async def get_voice_tags(self, event: AstrMessageEvent):
        """获取标签列表"""
        result = await self.api.get_audio_tags()
        if not self.is_success(result):
            yield self.chain_reply(event, f"❌ 获取失败：{result.get('msg', '未知错误')}")
            return

        tags = result.get("data", [])
        if not tags:
            yield self.chain_reply(event, "暂无标签数据")
            return

        lines = ["🏷️【语音标签列表】", ""]
        for tag in tags[:20]:
            name = tag.get("name") or tag.get("tag", "未知")
            count = tag.get("count", 0)
            lines.append(f"• {name} ({count}条)")

        lines.append("")
        lines.append("💡 用法：/三角洲 语音 <标签名>")

        yield self.chain_reply(event, "\n".join(lines))

    async def get_voice_categories(self, event: AstrMessageEvent):
        """获取分类列表"""
        result = await self.api.get_audio_categories()
        if not self.is_success(result):
            yield self.chain_reply(event, f"❌ 获取失败：{result.get('msg', '未知错误')}")
            return

        categories = result.get("data", [])
        if not categories:
            yield self.chain_reply(event, "暂无分类数据")
            return

        lines = ["📂【语音分类列表】", ""]
        for cat in categories:
            name = cat.get("name") or cat.get("category", "未知")
            count = cat.get("count", 0)
            lines.append(f"• {name} ({count}条)")

        lines.append("")
        lines.append("💡 用法：/三角洲 语音 <分类名>")

        yield self.chain_reply(event, "\n".join(lines))

    async def get_voice_stats(self, event: AstrMessageEvent):
        """获取语音统计"""
        result = await self.api.get_audio_stats()
        if not self.is_success(result):
            yield self.chain_reply(event, f"❌ 获取失败：{result.get('msg', '未知错误')}")
            return

        data = result.get("data", {})
        lines = [
            "📊【语音统计】",
            f"总语音数：{data.get('totalAudios', 0)}",
            f"角色数量：{data.get('characterCount', 0)}",
            f"分类数量：{data.get('categoryCount', 0)}",
            f"标签数量：{data.get('tagCount', 0)}"
        ]

        yield self.chain_reply(event, "\n".join(lines))
