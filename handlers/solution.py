"""
改枪方案处理器
包含：上传/查询/点赞/收藏改枪码等
"""
from astrbot.api.event import AstrMessageEvent
import astrbot.api.message_components as Comp
from .base import BaseHandler


class SolutionHandler(BaseHandler):
    """改枪方案处理器"""

    async def upload_solution(self, event: AstrMessageEvent, args: str = ""):
        """上传改枪方案"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        if not args:
            yield self.chain_reply(event, (
                "❌ 请提供改枪码\n"
                "用法：/三角洲 上传改枪码 <改枪码> [描述] [模式]\n"
                "示例：/三角洲 上传改枪码 腾龙突击步枪-烽火地带-ABC123\n"
                "示例：/三角洲 上传改枪码 改枪码 满配腾龙 烽火"
            ))
            return

        # 解析参数
        parts = args.strip().split(maxsplit=2)
        solution_code = parts[0]
        desc = parts[1] if len(parts) > 1 else ""
        solution_type = "sol"  # 默认烽火

        if len(parts) > 2:
            type_str = parts[2].lower()
            if type_str in ["mp", "战场", "全面战场"]:
                solution_type = "mp"

        # 从描述中判断模式
        if desc:
            if "战场" in desc or "mp" in desc.lower():
                solution_type = "mp"
            elif "烽火" in desc or "sol" in desc.lower():
                solution_type = "sol"

        try:
            platform_id = str(event.get_sender_id())
            result = await self.api.upload_solution(
                token, platform_id, solution_code, desc, 
                is_public=False, solution_type=solution_type
            )
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 上传失败：{self.get_error_msg(result)}")
                return

            solution_data = result.get("data", {})
            solution_id = solution_data.get("solutionId", "?")
            weapon_name = solution_data.get("weaponName", "未知武器")

            lines = [
                "✅ 改枪方案上传成功！",
                f"方案ID：{solution_id}",
                f"武器：{weapon_name}",
                f"模式：{'烽火地带' if solution_type == 'sol' else '全面战场'}",
            ]
            if desc:
                lines.append(f"描述：{desc}")

            yield self.chain_reply(event, "\n".join(lines))

        except Exception as e:
            yield self.chain_reply(event, f"❌ 上传失败：{e}")

    async def get_solution_list(self, event: AstrMessageEvent, args: str = ""):
        """获取改枪方案列表"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        # 解析参数
        weapon_name = ""
        solution_type = ""
        
        if args:
            parts = args.strip().split()
            for part in parts:
                if part in ["烽火", "sol"]:
                    solution_type = "sol"
                elif part in ["战场", "mp"]:
                    solution_type = "mp"
                else:
                    weapon_name = part

        try:
            platform_id = str(event.get_sender_id())
            result = await self.api.get_solution_list(
                token, platform_id, 
                weapon_name=weapon_name, 
                solution_type=solution_type
            )
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 获取列表失败：{self.get_error_msg(result)}")
                return

            solutions = result.get("data", {}).get("solutions", [])
            if not solutions:
                yield self.chain_reply(event, "📭 暂无改枪方案")
                return

            lines = ["🔧【改枪方案列表】", ""]
            for sol in solutions[:10]:
                sol_id = sol.get("solutionId", "?")
                weapon = sol.get("weaponName", "未知武器")
                desc = sol.get("desc", "")[:20]
                likes = sol.get("likes", 0)
                sol_type = "烽" if sol.get("type") == "sol" else "战"
                
                line = f"#{sol_id} [{sol_type}] {weapon}"
                if desc:
                    line += f" - {desc}"
                line += f" 👍{likes}"
                lines.append(line)

            if len(solutions) > 10:
                lines.append(f"... 等共 {len(solutions)} 个方案")

            lines.append("")
            lines.append("💡 /三角洲 改枪码详情 <方案ID>")

            yield self.chain_reply(event, "\n".join(lines))

        except Exception as e:
            yield self.chain_reply(event, f"❌ 获取列表失败：{e}")

    async def get_solution_detail(self, event: AstrMessageEvent, solution_id: str = ""):
        """获取方案详情"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        if not solution_id:
            yield self.chain_reply(event, "❌ 请指定方案ID\n用法：/三角洲 改枪码详情 <方案ID>")
            return

        try:
            platform_id = str(event.get_sender_id())
            result = await self.api.get_solution_detail(token, platform_id, solution_id)
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 获取详情失败：{self.get_error_msg(result)}")
                return

            sol = result.get("data", {})
            if not sol:
                yield self.chain_reply(event, "❌ 未找到该方案")
                return

            weapon_name = sol.get("weaponName", "未知武器")
            solution_code = sol.get("solutionCode", "")
            desc = sol.get("desc", "无描述")
            sol_type = "烽火地带" if sol.get("type") == "sol" else "全面战场"
            likes = sol.get("likes", 0)
            dislikes = sol.get("dislikes", 0)
            author = sol.get("authorName", "匿名")
            created = sol.get("createdAt", "")[:10]
            
            lines = [
                f"🔧【改枪方案 #{solution_id}】",
                f"武器：{weapon_name}",
                f"模式：{sol_type}",
                f"描述：{desc}",
                f"作者：{author}",
                f"创建：{created}",
                f"评价：👍{likes} 👎{dislikes}",
                "",
                "📋 改枪码：",
                solution_code
            ]

            # 配件信息
            accessories = sol.get("accessories", [])
            if accessories:
                lines.append("")
                lines.append("🔩 配件：")
                for acc in accessories[:8]:
                    acc_name = acc.get("name", "未知")
                    lines.append(f"  • {acc_name}")

            yield self.chain_reply(event, "\n".join(lines))

        except Exception as e:
            yield self.chain_reply(event, f"❌ 获取详情失败：{e}")

    async def vote_solution(self, event: AstrMessageEvent, solution_id: str = "", vote_type: str = "like"):
        """点赞/点踩方案"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        if not solution_id:
            yield self.chain_reply(event, "❌ 请指定方案ID")
            return

        try:
            platform_id = str(event.get_sender_id())
            result = await self.api.vote_solution(token, platform_id, solution_id, vote_type)
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 投票失败：{self.get_error_msg(result)}")
                return

            action = "点赞" if vote_type == "like" else "点踩"
            yield self.chain_reply(event, f"✅ 已{action}方案 #{solution_id}")

        except Exception as e:
            yield self.chain_reply(event, f"❌ 投票失败：{e}")

    async def delete_solution(self, event: AstrMessageEvent, solution_id: str = ""):
        """删除方案"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        if not solution_id:
            yield self.chain_reply(event, "❌ 请指定方案ID")
            return

        try:
            platform_id = str(event.get_sender_id())
            result = await self.api.delete_solution(token, platform_id, solution_id)
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 删除失败：{self.get_error_msg(result)}")
                return

            yield self.chain_reply(event, f"✅ 已删除方案 #{solution_id}")

        except Exception as e:
            yield self.chain_reply(event, f"❌ 删除失败：{e}")

    async def collect_solution(self, event: AstrMessageEvent, solution_id: str = "", action: str = "collect"):
        """收藏/取消收藏方案"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        if not solution_id:
            yield self.chain_reply(event, "❌ 请指定方案ID")
            return

        try:
            platform_id = str(event.get_sender_id())
            
            if action == "collect":
                result = await self.api.collect_solution(token, platform_id, solution_id)
                action_text = "收藏"
            else:
                result = await self.api.discollect_solution(token, platform_id, solution_id)
                action_text = "取消收藏"
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ {action_text}失败：{self.get_error_msg(result)}")
                return

            yield self.chain_reply(event, f"✅ 已{action_text}方案 #{solution_id}")

        except Exception as e:
            yield self.chain_reply(event, f"❌ 操作失败：{e}")

    async def get_collect_list(self, event: AstrMessageEvent):
        """获取收藏列表"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        try:
            platform_id = str(event.get_sender_id())
            result = await self.api.get_collect_list(token, platform_id)
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 获取收藏列表失败：{self.get_error_msg(result)}")
                return

            solutions = result.get("data", {}).get("solutions", [])
            if not solutions:
                yield self.chain_reply(event, "📭 暂无收藏的方案")
                return

            lines = ["⭐【我的收藏】", ""]
            for sol in solutions[:15]:
                sol_id = sol.get("solutionId", "?")
                weapon = sol.get("weaponName", "未知武器")
                desc = sol.get("desc", "")[:15]
                sol_type = "烽" if sol.get("type") == "sol" else "战"
                
                line = f"#{sol_id} [{sol_type}] {weapon}"
                if desc:
                    line += f" - {desc}"
                lines.append(line)

            if len(solutions) > 15:
                lines.append(f"... 等共 {len(solutions)} 个方案")

            yield self.chain_reply(event, "\n".join(lines))

        except Exception as e:
            yield self.chain_reply(event, f"❌ 获取收藏列表失败：{e}")
