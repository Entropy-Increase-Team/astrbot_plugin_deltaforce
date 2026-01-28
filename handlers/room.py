"""
开黑房间处理器
包含：创建/加入/退出房间等
"""
from astrbot.api.event import AstrMessageEvent
import astrbot.api.message_components as Comp
from .base import BaseHandler


class RoomHandler(BaseHandler):
    """开黑房间处理器"""

    async def get_room_list(self, event: AstrMessageEvent, args: str = ""):
        """获取房间列表"""
        try:
            # 解析参数
            room_type = ""
            has_password = ""
            
            if args:
                parts = args.strip().split()
                for part in parts:
                    if part in ["烽火", "sol", "烽火地带"]:
                        room_type = "sol"
                    elif part in ["战场", "mp", "全面战场"]:
                        room_type = "mp"
                    elif part in ["有密码", "加密"]:
                        has_password = "true"
                    elif part in ["无密码", "公开"]:
                        has_password = "false"

            result = await self.api.get_room_list(room_type=room_type, has_password=has_password)
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 获取房间列表失败：{self.get_error_msg(result)}")
                return

            # API返回的是列表，不是包含rooms的对象
            rooms = result.get("data", [])
            if isinstance(rooms, dict):
                rooms = rooms.get("rooms", [])
            if not rooms:
                yield self.chain_reply(event, "📭 暂无可用房间")
                return

            lines = ["🏠【开黑房间列表】", ""]
            for room in rooms[:10]:
                room_id = room.get("roomId", "?")
                room_type_name = "烽火" if room.get("type") == "sol" else "战场"
                member_count = room.get("memberCount", 0)
                max_members = room.get("maxMembers", 4)
                has_pwd = "🔒" if room.get("hasPassword") else "🔓"
                map_name = room.get("mapName", "")
                
                line = f"{has_pwd} #{room_id} [{room_type_name}] {member_count}/{max_members}人"
                if map_name:
                    line += f" 地图:{map_name}"
                lines.append(line)

            if len(rooms) > 10:
                lines.append(f"... 等共 {len(rooms)} 个房间")

            lines.append("")
            lines.append("💡 /三角洲 加入房间 <房间号> [密码]")
            lines.append("💡 /三角洲 创建房间 <模式> [地图] [密码]")

            yield self.chain_reply(event, "\n".join(lines))

        except Exception as e:
            yield self.chain_reply(event, f"❌ 获取房间列表失败：{e}")

    async def create_room(self, event: AstrMessageEvent, args: str = ""):
        """创建房间"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        if not args:
            yield self.chain_reply(event, (
                "❌ 请指定房间参数\n"
                "用法：/三角洲 创建房间 <模式> [地图ID] [标签] [密码]\n"
                "示例：/三角洲 创建房间 烽火\n"
                "示例：/三角洲 创建房间 战场 123456"
            ))
            return

        # 解析参数
        parts = args.strip().split()
        room_type = "sol"
        map_id = "0"
        tag = ""
        password = ""

        if parts:
            first = parts[0]
            if first in ["烽火", "sol", "烽火地带"]:
                room_type = "sol"
            elif first in ["战场", "mp", "全面战场"]:
                room_type = "mp"

        if len(parts) > 1:
            map_id = parts[1]
        if len(parts) > 2:
            tag = parts[2]
        if len(parts) > 3:
            password = parts[3]

        try:
            result = await self.api.create_room(token, room_type, map_id, tag, password)
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 创建房间失败：{self.get_error_msg(result)}")
                return

            room_data = result.get("data", {})
            room_id = room_data.get("roomId", "?")
            
            lines = [
                "✅ 房间创建成功！",
                f"房间号：{room_id}",
                f"模式：{'烽火地带' if room_type == 'sol' else '全面战场'}",
            ]
            if password:
                lines.append(f"密码：{password}")

            yield self.chain_reply(event, "\n".join(lines))

        except Exception as e:
            yield self.chain_reply(event, f"❌ 创建房间失败：{e}")

    async def join_room(self, event: AstrMessageEvent, room_id: str = "", password: str = ""):
        """加入房间"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        if not room_id:
            yield self.chain_reply(event, "❌ 请指定房间号\n用法：/三角洲 加入房间 <房间号> [密码]")
            return

        try:
            result = await self.api.join_room(token, room_id, password)
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 加入房间失败：{self.get_error_msg(result)}")
                return

            yield self.chain_reply(event, f"✅ 成功加入房间 #{room_id}")

        except Exception as e:
            yield self.chain_reply(event, f"❌ 加入房间失败：{e}")

    async def quit_room(self, event: AstrMessageEvent, room_id: str = ""):
        """退出/解散房间"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        if not room_id:
            yield self.chain_reply(event, "❌ 请指定房间号\n用法：/三角洲 退出房间 <房间号>")
            return

        try:
            result = await self.api.quit_room(token, room_id)
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 退出房间失败：{self.get_error_msg(result)}")
                return

            yield self.chain_reply(event, f"✅ 已退出房间 #{room_id}")

        except Exception as e:
            yield self.chain_reply(event, f"❌ 退出房间失败：{e}")

    async def get_room_info(self, event: AstrMessageEvent, room_id: str = ""):
        """获取当前房间信息"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        try:
            result = await self.api.get_room_info(token, room_id) if room_id else await self.api.get_room_info(token)
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 获取房间信息失败：{self.get_error_msg(result)}")
                return

            room = result.get("data", {})
            if not room or not room.get("roomId"):
                yield self.chain_reply(event, "📭 您当前未在任何房间中")
                return

            room_id = room.get("roomId", "?")
            room_type = "烽火地带" if room.get("type") == "sol" else "全面战场"
            members = room.get("members", [])
            max_members = room.get("maxMembers", 4)
            map_name = room.get("mapName", "未指定")
            is_owner = room.get("isOwner", False)

            lines = [
                f"🏠【房间信息】#{room_id}",
                f"模式：{room_type}",
                f"地图：{map_name}",
                f"人数：{len(members)}/{max_members}",
                f"身份：{'房主' if is_owner else '成员'}",
                "",
                "👥 成员列表："
            ]

            for member in members:
                name = self.decode_url(member.get("nickname", "未知"))
                is_host = "👑" if member.get("isOwner") else ""
                lines.append(f"  {is_host} {name}")

            yield self.chain_reply(event, "\n".join(lines))

        except Exception as e:
            yield self.chain_reply(event, f"❌ 获取房间信息失败：{e}")

    async def kick_member(self, event: AstrMessageEvent, room_id: str = "", target: str = ""):
        """踢出成员（房主）"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        if not room_id or not target:
            yield self.chain_reply(event, "❌ 参数不完整\n用法：/三角洲 踢人 <房间号> <目标token>")
            return

        try:
            result = await self.api.kick_member(token, room_id, target)
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 踢出失败：{self.get_error_msg(result)}")
                return

            yield self.chain_reply(event, "✅ 已踢出该成员")

        except Exception as e:
            yield self.chain_reply(event, f"❌ 踢出失败：{e}")

    async def get_room_tags(self, event: AstrMessageEvent):
        """获取房间标签列表"""
        try:
            result = await self.api.get_room_tags()
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 获取标签失败：{self.get_error_msg(result)}")
                return

            tags = result.get("data", [])
            if not tags:
                yield self.chain_reply(event, "暂无标签数据")
                return

            lines = ["🏷️【房间标签列表】", ""]
            for tag in tags:
                tag_id = tag.get("id", "?")
                tag_name = tag.get("name", "未知")
                lines.append(f"• {tag_name} (ID: {tag_id})")

            yield self.chain_reply(event, "\n".join(lines))

        except Exception as e:
            yield self.chain_reply(event, f"❌ 获取标签失败：{e}")

    async def get_room_maps(self, event: AstrMessageEvent):
        """获取房间地图列表"""
        try:
            result = await self.api.get_room_maps()
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 获取地图列表失败：{self.get_error_msg(result)}")
                return

            maps = result.get("data", [])
            if not maps:
                yield self.chain_reply(event, "暂无地图数据")
                return

            lines = ["🗺️【房间地图列表】", ""]
            for map_item in maps:
                map_id = map_item.get("id", "?")
                map_name = map_item.get("name", "未知")
                lines.append(f"• {map_name} (ID: {map_id})")

            lines.append("")
            lines.append("💡 创建房间时可指定地图ID")
            lines.append("示例: /三角洲 创建房间 烽火 <地图ID>")

            yield self.chain_reply(event, "\n".join(lines))

        except Exception as e:
            yield self.chain_reply(event, f"❌ 获取地图列表失败：{e}")
