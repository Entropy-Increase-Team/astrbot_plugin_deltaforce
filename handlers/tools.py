"""
工具处理器
包含：价格查询、物品搜索、利润排行等
"""
from astrbot.api.event import AstrMessageEvent
import astrbot.api.message_components as Comp
from .base import BaseHandler
from ..utils.render import Render


class ToolsHandler(BaseHandler):
    """工具处理器"""

    @staticmethod
    def format_price(price) -> str:
        """格式化价格显示"""
        if price is None or price == "":
            return "-"
        try:
            price = float(price)
            if price >= 1000000000:
                return f"{price / 1000000000:.2f}B"
            elif price >= 1000000:
                return f"{price / 1000000:.2f}M"
            elif price >= 1000:
                return f"{price / 1000:.2f}K"
            else:
                return f"{price:,.0f}"
        except:
            return str(price)

    @staticmethod
    def format_profit(profit) -> str:
        """格式化利润显示（带正负号）"""
        if profit is None or profit == "":
            return "-"
        try:
            profit = float(profit)
            sign = "+" if profit >= 0 else ""
            abs_profit = abs(profit)
            if abs_profit >= 1000000000:
                return f"{sign}{profit / 1000000000:.2f}B"
            elif abs_profit >= 1000000:
                return f"{sign}{profit / 1000000:.2f}M"
            elif abs_profit >= 1000:
                return f"{sign}{profit / 1000:.2f}K"
            else:
                return f"{sign}{profit:,.0f}"
        except:
            return str(profit)

    async def search_object(self, event: AstrMessageEvent, keyword: str):
        """物品搜索"""
        if not keyword or not keyword.strip():
            yield self.chain_reply(event, "请输入要搜索的物品名称\n示例: /三角洲 搜索 AK47")
            return

        keyword = keyword.strip()
        result = await self.api.search_object(keyword=keyword)
        
        if not result.get("success", False) and not self.is_success(result):
            yield self.chain_reply(event, f"搜索失败：{result.get('message', result.get('msg', '未知错误'))}")
            return

        data = result.get("data", {})
        items = data.get("keywords", [])
        
        if not items:
            yield self.chain_reply(event, f"未找到与「{keyword}」相关的物品")
            return

        output_lines = [f"🔍【搜索结果】「{keyword}」"]
        output_lines.append("━━━━━━━━━━━━━━━")
        output_lines.append(f"共找到 {len(items)} 个物品")
        output_lines.append("")

        for i, item in enumerate(items[:15], 1):
            name = item.get("name", item.get("objectName", "未知"))
            object_id = item.get("objectID", "")
            category = item.get("category", "")
            
            line = f"{i}. {name}"
            if object_id:
                line += f" (ID: {object_id})"
            if category:
                line += f" [{category}]"
            output_lines.append(line)

        if len(items) > 15:
            output_lines.append(f"\n... 共 {len(items)} 个结果，仅显示前15个")

        output_lines.append("")
        output_lines.append("💡 使用 /三角洲 价格 <名称> 查询价格")

        yield self.chain_reply(event, "\n".join(output_lines))

    async def get_current_price(self, event: AstrMessageEvent, query: str):
        """当前价格查询"""
        if not query or not query.strip():
            yield self.chain_reply(event, "请输入要查询的物品名称或ID\n示例: /三角洲 价格 AK47")
            return

        query = query.strip()
        
        # 先搜索物品获取ID
        object_ids = []
        items_info = []
        
        if query.isdigit():
            # 直接是ID
            object_ids = [query]
            items_info = [{"objectID": query, "name": f"物品ID: {query}"}]
        else:
            # 名称搜索
            search_result = await self.api.search_object(keyword=query)
            if search_result.get("success", False) or self.is_success(search_result):
                items = search_result.get("data", {}).get("keywords", [])
                if items:
                    # 取前5个结果
                    for item in items[:5]:
                        oid = str(item.get("objectID", ""))
                        if oid:
                            object_ids.append(oid)
                            items_info.append(item)

        if not object_ids:
            yield self.chain_reply(event, f"未找到与「{query}」相关的物品")
            return

        # 查询价格
        result = await self.api.get_current_price(",".join(object_ids))
        
        if not result.get("success", False) and not self.is_success(result):
            yield self.chain_reply(event, f"查询价格失败：{result.get('message', result.get('msg', '未知错误'))}")
            return

        price_data = result.get("data", {})
        
        output_lines = [f"💰【价格查询】「{query}」"]
        output_lines.append("━━━━━━━━━━━━━━━")

        for item in items_info:
            object_id = str(item.get("objectID", ""))
            name = item.get("name", item.get("objectName", "未知"))
            
            item_price = price_data.get(object_id, {})
            if isinstance(item_price, dict):
                avg_price = item_price.get("avgPrice", item_price.get("price", "-"))
                min_price = item_price.get("minPrice", "-")
                max_price = item_price.get("maxPrice", "-")
                update_time = item_price.get("updateTime", "")
            else:
                avg_price = item_price if item_price else "-"
                min_price = "-"
                max_price = "-"
                update_time = ""

            output_lines.append(f"")
            output_lines.append(f"📦 {name}")
            output_lines.append(f"  均价: {self.format_price(avg_price)}")
            if min_price != "-" and max_price != "-":
                output_lines.append(f"  最低: {self.format_price(min_price)} | 最高: {self.format_price(max_price)}")
            if update_time:
                output_lines.append(f"  更新: {update_time}")

        yield self.chain_reply(event, "\n".join(output_lines))

    async def get_price_history(self, event: AstrMessageEvent, query: str):
        """价格历史查询"""
        if not query or not query.strip():
            yield self.chain_reply(event, "请输入要查询的物品名称或ID\n示例: /三角洲 价格历史 AK47")
            return

        query = query.strip()
        yield self.chain_reply(event, "正在查询历史价格，请稍候...")

        # 先搜索物品获取ID
        object_id = None
        object_name = query

        if query.isdigit():
            object_id = query
        else:
            search_result = await self.api.search_object(keyword=query)
            if search_result.get("success", False) or self.is_success(search_result):
                items = search_result.get("data", {}).get("keywords", [])
                if items:
                    object_id = str(items[0].get("objectID", ""))
                    object_name = items[0].get("name", items[0].get("objectName", query))

        if not object_id:
            yield self.chain_reply(event, f"未找到与「{query}」相关的物品")
            return

        # 查询历史价格
        result = await self.api.get_price_history(object_id)

        if not result.get("success", False) and not self.is_success(result):
            yield self.chain_reply(event, f"查询失败：{result.get('message', result.get('msg', '未知错误'))}")
            return

        data = result.get("data", {})
        history = data.get("history", [])
        stats = data.get("stats", {})

        if not history:
            yield self.chain_reply(event, f"「{object_name}」暂无历史价格数据")
            return

        output_lines = [f"📈【{object_name} 价格历史】"]
        output_lines.append("━━━━━━━━━━━━━━━")

        # 统计信息
        if stats:
            output_lines.append("📊 统计数据 (7天):")
            output_lines.append(f"  当前价格: {self.format_price(stats.get('latestPrice', '-'))}")
            output_lines.append(f"  平均价格: {self.format_price(stats.get('avgPrice', '-'))}")
            output_lines.append(f"  最高价格: {self.format_price(stats.get('maxPrice', '-'))}")
            output_lines.append(f"  最低价格: {self.format_price(stats.get('minPrice', '-'))}")
            output_lines.append(f"  价格波动: {self.format_price(stats.get('priceRange', '-'))}")
            output_lines.append("")

        # 按天分组显示
        from datetime import datetime
        from collections import defaultdict

        daily_data = defaultdict(list)
        for item in history:
            try:
                ts = item.get("timestamp", "")
                if ts:
                    dt = datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    date_key = dt.strftime("%m-%d")
                    daily_data[date_key].append(float(item.get("avgPrice", 0)))
            except:
                continue

        if daily_data:
            output_lines.append("📅 每日价格:")
            for date_key in sorted(daily_data.keys(), reverse=True)[:7]:
                prices = daily_data[date_key]
                if prices:
                    avg = sum(prices) / len(prices)
                    high = max(prices)
                    low = min(prices)
                    output_lines.append(f"  {date_key}: 均{self.format_price(avg)} (高{self.format_price(high)}/低{self.format_price(low)})")

        yield self.chain_reply(event, "\n".join(output_lines))

    async def get_profit_history(self, event: AstrMessageEvent, query: str):
        """利润历史查询"""
        if not query or not query.strip():
            yield self.chain_reply(event, "请输入要查询的物品名称或ID\n示例: /三角洲 利润历史 低级燃料")
            return

        query = query.strip()
        yield self.chain_reply(event, "正在查询利润历史，请稍候...")

        # 先搜索物品获取ID
        object_id = None
        object_name = query

        if query.isdigit():
            object_id = query
        else:
            search_result = await self.api.search_object(keyword=query)
            if search_result.get("success", False) or self.is_success(search_result):
                items = search_result.get("data", {}).get("keywords", [])
                if items:
                    object_id = str(items[0].get("objectID", ""))
                    object_name = items[0].get("name", items[0].get("objectName", query))

        if not object_id:
            yield self.chain_reply(event, f"未找到与「{query}」相关的物品")
            return

        # 查询利润历史 (使用价格历史API + 材料价格计算)
        price_result = await self.api.get_price_history(object_id)
        material_result = await self.api.get_material_price(object_id)

        if not price_result.get("success", False) and not self.is_success(price_result):
            yield self.chain_reply(event, f"查询失败：{price_result.get('message', price_result.get('msg', '未知错误'))}")
            return

        price_data = price_result.get("data", {})
        history = price_data.get("history", [])
        stats = price_data.get("stats", {})

        # 获取材料成本
        material_cost = 0
        materials = []
        if material_result.get("success", False) or self.is_success(material_result):
            mat_data = material_result.get("data", {})
            if isinstance(mat_data, dict):
                materials = mat_data.get("materials", [])
                material_cost = mat_data.get("totalCost", 0)

        output_lines = [f"📈【{object_name} 利润分析】"]
        output_lines.append("━━━━━━━━━━━━━━━")

        # 当前利润
        current_price = stats.get("latestPrice", 0) if stats else 0
        if current_price and material_cost:
            current_profit = float(current_price) - float(material_cost)
            output_lines.append(f"💰 当前利润: {self.format_profit(current_profit)}")
            output_lines.append(f"  售价: {self.format_price(current_price)}")
            output_lines.append(f"  成本: {self.format_price(material_cost)}")
            output_lines.append("")

        # 材料明细
        if materials:
            output_lines.append("🧪 材料成本:")
            for mat in materials[:5]:
                mat_name = mat.get("name", mat.get("objectName", "未知"))
                mat_price = mat.get("price", mat.get("minPrice", 0))
                mat_count = mat.get("count", 1)
                output_lines.append(f"  • {mat_name} x{mat_count}: {self.format_price(mat_price)}")
            output_lines.append("")

        # 历史价格趋势
        if stats:
            output_lines.append("📊 价格统计 (7天):")
            output_lines.append(f"  平均: {self.format_price(stats.get('avgPrice', '-'))}")
            output_lines.append(f"  最高: {self.format_price(stats.get('maxPrice', '-'))}")
            output_lines.append(f"  最低: {self.format_price(stats.get('minPrice', '-'))}")

            # 计算平均利润
            if material_cost:
                avg_price = stats.get("avgPrice", 0)
                if avg_price:
                    avg_profit = float(avg_price) - float(material_cost)
                    output_lines.append(f"  平均利润: {self.format_profit(avg_profit)}")

        if not history and not materials:
            output_lines.append("暂无历史数据")

        yield self.chain_reply(event, "\n".join(output_lines))

    async def get_material_price(self, event: AstrMessageEvent, query: str = ""):
        """制造材料价格查询"""
        yield self.chain_reply(event, "正在查询材料价格，请稍候...")

        result = await self.api.get_material_price(query.strip() if query else "")
        
        if not result.get("success", False) and not self.is_success(result):
            yield self.chain_reply(event, f"查询失败：{result.get('message', result.get('msg', '未知错误'))}")
            return

        data = result.get("data", [])
        if not data:
            yield self.chain_reply(event, "暂无材料价格数据")
            return

        output_lines = ["🧪【材料价格】"]
        output_lines.append("━━━━━━━━━━━━━━━")

        if isinstance(data, list):
            for item in data[:20]:
                name = item.get("name", item.get("objectName", "未知"))
                price = item.get("price", item.get("minPrice", "-"))
                output_lines.append(f"  {name}: {self.format_price(price)}")
            
            if len(data) > 20:
                output_lines.append(f"\n... 共 {len(data)} 种材料")
        elif isinstance(data, dict):
            for name, price in list(data.items())[:20]:
                output_lines.append(f"  {name}: {self.format_price(price)}")

        yield self.chain_reply(event, "\n".join(output_lines))

    async def get_profit_rank(self, event: AstrMessageEvent, args: str = ""):
        """利润排行查询"""
        # 解析参数
        rank_type = "sol"  # 默认烽火地带
        place = ""
        
        if args:
            parts = args.strip().split()
            for part in parts:
                part_lower = part.lower()
                if part_lower in ["烽火", "烽火地带", "sol", "摸金"]:
                    rank_type = "sol"
                elif part_lower in ["全面", "全面战场", "战场", "mp"]:
                    rank_type = "mp"
                else:
                    place = part

        yield self.chain_reply(event, "正在查询利润排行，请稍候...")

        result = await self.api.get_profit_rank(rank_type=rank_type, place=place)
        
        if not result.get("success", False) and not self.is_success(result):
            yield self.chain_reply(event, f"查询失败：{result.get('message', result.get('msg', '未知错误'))}")
            return

        data = result.get("data", [])
        if not data:
            yield self.chain_reply(event, "暂无利润排行数据")
            return

        mode_name = "烽火地带" if rank_type == "sol" else "全面战场"
        output_lines = [f"📈【{mode_name}利润排行】"]
        if place:
            output_lines[0] += f" - {place}"
        output_lines.append("━━━━━━━━━━━━━━━")

        for i, item in enumerate(data[:15], 1):
            name = item.get("name", item.get("objectName", "未知"))
            profit = item.get("profit", item.get("avgProfit", 0))
            price = item.get("price", item.get("avgPrice", "-"))
            
            output_lines.append(f"{i}. {name}")
            output_lines.append(f"   利润: {self.format_profit(profit)} | 价格: {self.format_price(price)}")

        if len(data) > 15:
            output_lines.append(f"\n... 共 {len(data)} 个物品")

        yield self.chain_reply(event, "\n".join(output_lines))

    async def get_map_stats(self, event: AstrMessageEvent, args: str = ""):
        """地图统计查询"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        # 解析参数
        mode = ""
        season = "all"
        map_keyword = ""

        if args:
            parts = args.strip().split()
            for part in parts:
                part_lower = part.lower()
                if part_lower in ["烽火", "烽火地带", "sol", "摸金"]:
                    mode = "sol"
                elif part_lower in ["全面", "全面战场", "战场", "mp"]:
                    mode = "mp"
                elif part_lower in ["all", "全部"]:
                    season = "all"
                elif part.isdigit():
                    season = part
                else:
                    map_keyword = part

        if not mode:
            yield self.chain_reply(event, "请指定游戏模式\n示例: /三角洲 地图统计 烽火\n或: /三角洲 地图统计 mp")
            return

        yield self.chain_reply(event, "正在查询地图统计，请稍候...")

        result = await self.api.get_map_stats(
            frameworkToken=token,
            seasonid=season,
            mode=mode,
            map_id=""
        )

        if not self.is_success(result):
            yield self.chain_reply(event, f"查询失败：{result.get('msg', '未知错误')}")
            return

        data = result.get("data", [])
        if not data:
            yield self.chain_reply(event, "暂无地图统计数据")
            return

        mode_name = "烽火地带" if mode == "sol" else "全面战场"
        
        # 准备渲染数据
        map_stats_list = []
        for item in data:
            map_name = item.get("mapName", "未知地图")
            map_data = item.get("data", {})
            
            # 如果有地图关键词筛选
            if map_keyword and map_keyword not in map_name:
                continue

            stat_item = {
                'mapName': map_name,
                'mapImage': item.get('mapImage', ''),
            }

            if mode == "sol":
                total_games = map_data.get("zdj", map_data.get("cs", 0))
                escaped = map_data.get("isescapednum", 0)
                kills = map_data.get("killnum", 0)
                profit = map_data.get("a1", 0)
                
                try:
                    total_int = int(total_games) if total_games else 0
                    escaped_int = int(escaped) if escaped else 0
                    escape_rate = f"{(escaped_int / total_int * 100):.1f}%" if total_int > 0 else "0%"
                    failed = total_int - escaped_int
                except:
                    escape_rate = "0%"
                    failed = 0
                
                stat_item['sol'] = {
                    'totalGames': total_games,
                    'escaped': escaped,
                    'escapeRate': escape_rate,
                    'kill': kills,  # 模板期望 kill 而不是 kills
                    'failed': failed,
                    'profit': self.format_profit(profit),
                }
            else:
                total_games = map_data.get("zdjnum", 0)
                wins = map_data.get("winnum", 0)
                kills = map_data.get("killnum", 0)
                deaths = map_data.get("death", 0)
                
                try:
                    win_rate = f"{(int(wins) / int(total_games) * 100):.1f}%" if total_games and int(total_games) > 0 else "0%"
                    kd = f"{int(kills) / int(deaths):.2f}" if deaths and int(deaths) > 0 else str(kills)
                except:
                    win_rate = "0%"
                    kd = "0"
                
                stat_item['mp'] = {
                    'totalGames': total_games,
                    'win': wins,  # 模板期望 win 而不是 wins
                    'winRate': win_rate,
                    'kill': kills,  # 模板期望 kill 而不是 kills
                    'death': deaths,  # 模板期望 death 而不是 deaths
                    'kd': kd,
                }
            
            map_stats_list.append(stat_item)

        from datetime import datetime
        render_data = {
            'backgroundImage': Render.get_background_image(),
            'type': mode,
            'typeName': mode_name,
            'seasonid': f"赛季 {season}" if season != 'all' else '全部赛季',
            'totalMaps': len(map_stats_list),
            'mapStatsList': map_stats_list[:10],
            'currentDate': datetime.now().strftime("%Y-%m-%d %H:%M"),
        }

        yield await self.render_and_reply(
            event,
            'mapStats/mapStats.html',
            render_data,
            fallback_text=self._build_map_stats_text(map_stats_list, mode, mode_name, season),
            width=600,
            height=1000
        )

    def _build_map_stats_text(self, map_stats_list, mode, mode_name, season):
        """构建纯文本地图统计（渲染失败时的回退）"""
        output_lines = [f"🗺️【{mode_name}地图统计】"]
        output_lines.append(f"赛季: {season if season != 'all' else '全部'}")
        output_lines.append("━━━━━━━━━━━━━━━")

        for item in map_stats_list[:10]:
            map_name = item.get("mapName", "未知地图")
            output_lines.append(f"")
            output_lines.append(f"📍 {map_name}")

            if mode == "sol" and item.get('sol'):
                sol = item['sol']
                output_lines.append(f"  对局: {sol['totalGames']} | 撤离: {sol['escaped']} ({sol['escapeRate']})")
                output_lines.append(f"  击杀: {sol['kill']} | 收益: {sol['profit']}")
            elif mode == "mp" and item.get('mp'):
                mp = item['mp']
                output_lines.append(f"  对局: {mp['totalGames']} | 胜场: {mp['win']} ({mp['winRate']})")
                output_lines.append(f"  击杀: {mp['kill']} | 死亡: {mp['death']} | KD: {mp['kd']}")

        if len(map_stats_list) > 10:
            output_lines.append(f"\n... 共 {len(map_stats_list)} 张地图")

        return "\n".join(output_lines)

    async def get_object_list(self, event: AstrMessageEvent, args: str = ""):
        """物品列表查询"""
        # 默认值
        PAGE_SIZE = 20
        primary = "props"  # 默认一级分类
        second = "collection"  # 默认二级分类
        page = 1

        # 解析参数
        if args:
            parts = args.strip().split()
            remaining_parts = []
            
            for part in parts:
                if part.isdigit():
                    page = int(part)
                else:
                    remaining_parts.append(part)
            
            if len(remaining_parts) >= 1:
                primary = remaining_parts[0]
            if len(remaining_parts) >= 2:
                second = remaining_parts[1]

        yield self.chain_reply(event, f"正在获取物品列表 (分类: {primary}/{second}, 第{page}页)...")

        result = await self.api.get_object_list(primary=primary, second=second)
        
        if not result.get("success", False) and not self.is_success(result):
            yield self.chain_reply(event, f"查询失败：{result.get('message', result.get('msg', '未知错误'))}")
            return

        data = result.get("data", {})
        items = data.get("keywords", [])
        
        if not items:
            yield self.chain_reply(event, f"未找到分类 {primary}/{second} 下的物品")
            return

        total_pages = (len(items) + PAGE_SIZE - 1) // PAGE_SIZE
        if page < 1 or page > total_pages:
            yield self.chain_reply(event, f"页码超出范围，共 {total_pages} 页")
            return

        # 分页
        start_idx = (page - 1) * PAGE_SIZE
        end_idx = start_idx + PAGE_SIZE
        page_items = items[start_idx:end_idx]

        output_lines = [f"📦【物品列表】{primary}/{second}"]
        output_lines.append(f"第 {page}/{total_pages} 页 (共 {len(items)} 件)")
        output_lines.append("━━━━━━━━━━━━━━━")

        for item in page_items:
            name = item.get("objectName", item.get("name", "未知"))
            object_id = item.get("objectID", item.get("id", ""))
            price = item.get("avgPrice", item.get("price", "-"))
            grade = item.get("grade", "-")
            
            output_lines.append(f"• {name} (ID: {object_id})")
            output_lines.append(f"  价格: {self.format_price(price)} | 稀有度: {grade}")

        output_lines.append("")
        output_lines.append(f"💡 翻页: /三角洲 物品列表 {primary} {second} <页码>")
        
        yield self.chain_reply(event, "\n".join(output_lines))

    async def get_red_collection(self, event: AstrMessageEvent, args: str = ""):
        """大红收藏查询"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        # 解析赛季参数
        season = ""
        if args:
            args_stripped = args.strip()
            if args_stripped.isdigit():
                season = args_stripped

        yield self.chain_reply(event, "正在查询大红收藏...")

        result = await self.api.get_collection(frameworkToken=token)
        
        if not self.is_success(result):
            yield self.chain_reply(event, f"查询失败：{result.get('msg', '未知错误')}")
            return

        data = result.get("data", {})
        collections = data.get("collections", data.get("items", []))
        
        if not collections:
            yield self.chain_reply(event, "暂无收藏数据")
            return

        output_lines = ["🔴【大红收藏】"]
        if season:
            output_lines[0] += f" 第{season}赛季"
        output_lines.append("━━━━━━━━━━━━━━━")

        # 筛选大红品质的藏品
        red_items = []
        for item in collections:
            grade = item.get("grade", "").lower()
            item_season = str(item.get("season", ""))
            
            # 筛选红色稀有度
            if grade in ["red", "r", "红色", "大红"]:
                # 如果指定了赛季，则筛选
                if season and item_season != season:
                    continue
                red_items.append(item)

        if not red_items:
            msg = "暂无大红藏品"
            if season:
                msg += f" (第{season}赛季)"
            yield self.chain_reply(event, msg)
            return

        output_lines.append(f"共 {len(red_items)} 件大红藏品")
        output_lines.append("")

        for item in red_items[:15]:
            name = item.get("objectName", item.get("name", "未知"))
            count = item.get("count", 1)
            item_season = item.get("season", "-")
            price = item.get("avgPrice", item.get("price", "-"))
            
            output_lines.append(f"🔴 {name} x{count}")
            output_lines.append(f"   赛季: S{item_season} | 价格: {self.format_price(price)}")

        if len(red_items) > 15:
            output_lines.append(f"\n... 共 {len(red_items)} 件")

        yield self.chain_reply(event, "\n".join(output_lines))

    async def get_max_profit(self, event: AstrMessageEvent, args: str = ""):
        """最高利润查询 (V2)"""
        # 解析参数: [类型] [场所] [物品ID]
        rank_type = "hour"  # 默认小时利润
        place = ""
        object_id = ""

        if args:
            parts = args.strip().split()
            for part in parts:
                part_lower = part.lower()
                if part_lower in ["hour", "小时", "时利润", "hourprofit"]:
                    rank_type = "hour"
                elif part_lower in ["total", "总", "总利润", "totalprofit"]:
                    rank_type = "total"
                elif part_lower in ["tech", "技术中心", "科技"]:
                    place = "tech"
                elif part_lower in ["workbench", "工作台"]:
                    place = "workbench"
                elif part_lower in ["pharmacy", "制药台", "制药"]:
                    place = "pharmacy"
                elif part_lower in ["armory", "防具台", "防具"]:
                    place = "armory"
                elif part.isdigit():
                    object_id = part

        yield self.chain_reply(event, "正在查询最高利润...")

        result = await self.api.get_profit_rank_v2(rank_type=rank_type, place=place)
        
        if not result.get("success", False) and not self.is_success(result):
            yield self.chain_reply(event, f"查询失败：{result.get('message', result.get('msg', '未知错误'))}")
            return

        data = result.get("data", {})
        groups = data.get("groups", {})
        
        if not groups:
            yield self.chain_reply(event, "暂无利润排行数据")
            return

        type_name = "小时利润" if rank_type == "hour" else "总利润"
        output_lines = [f"📈【最高{type_name}排行 V2】"]
        if place:
            output_lines[0] += f" - {place}"
        output_lines.append("━━━━━━━━━━━━━━━")

        # 按场所显示
        for place_key, items in groups.items():
            if place and place_key != place:
                continue
            
            place_names = {
                "tech": "🔧 技术中心",
                "workbench": "🔨 工作台",
                "pharmacy": "💊 制药台",
                "armory": "🛡️ 防具台"
            }
            
            output_lines.append("")
            output_lines.append(place_names.get(place_key, place_key))
            
            # 按利润排序
            sorted_items = sorted(
                items,
                key=lambda x: x.get("today", {}).get("hourProfit" if rank_type == "hour" else "profit", 0) or 0,
                reverse=True
            )
            
            for i, item in enumerate(sorted_items[:5], 1):
                name = item.get("objectName", "未知")
                today = item.get("today", {})
                hour_profit = today.get("hourProfit", 0)
                total_profit = today.get("profit", 0)
                level = item.get("level", 0)
                
                profit_val = hour_profit if rank_type == "hour" else total_profit
                output_lines.append(f"  {i}. {name} (Lv.{level})")
                output_lines.append(f"     {type_name}: {self.format_profit(profit_val)}")

        yield self.chain_reply(event, "\n".join(output_lines))

    async def get_special_ops_profit(self, event: AstrMessageEvent, args: str = ""):
        """特勤处利润查询"""
        # 解析类型参数
        rank_type = "hour"  # 默认小时利润
        
        if args:
            args_lower = args.strip().lower()
            if args_lower in ["hour", "小时", "时利润", "hourprofit"]:
                rank_type = "hour"
            elif args_lower in ["total", "总", "总利润", "totalprofit", "profit"]:
                rank_type = "total"

        # 特勤处四个场所
        places = [
            {"key": "tech", "name": "🔧 技术中心"},
            {"key": "workbench", "name": "🔨 工作台"},
            {"key": "pharmacy", "name": "💊 制药台"},
            {"key": "armory", "name": "🛡️ 防具台"}
        ]

        type_name = "小时利润" if rank_type == "hour" else "总利润"
        yield self.chain_reply(event, f"正在查询特勤处{type_name}...")

        output_lines = [f"🏢【特勤处{type_name}总览】"]
        output_lines.append("四个制造场所TOP3排行")
        output_lines.append("━━━━━━━━━━━━━━━")

        for place_info in places:
            result = await self.api.get_profit_rank_v2(rank_type=rank_type, place=place_info["key"])
            
            if not result.get("success", False) and not self.is_success(result):
                output_lines.append(f"\n{place_info['name']}: 获取失败")
                continue

            data = result.get("data", {})
            groups = data.get("groups", {})
            items = groups.get(place_info["key"], [])
            
            if not items:
                output_lines.append(f"\n{place_info['name']}: 暂无数据")
                continue

            output_lines.append(f"\n{place_info['name']}")
            
            # 按利润排序
            sorted_items = sorted(
                items,
                key=lambda x: x.get("today", {}).get("hourProfit" if rank_type == "hour" else "profit", 0) or 0,
                reverse=True
            )
            
            for i, item in enumerate(sorted_items[:3], 1):
                name = item.get("objectName", "未知")
                today = item.get("today", {})
                hour_profit = today.get("hourProfit", 0)
                total_profit = today.get("profit", 0)
                level = item.get("level", 0)
                
                profit_val = hour_profit if rank_type == "hour" else total_profit
                output_lines.append(f"  {i}. {name} (Lv.{level}): {self.format_profit(profit_val)}")

        yield self.chain_reply(event, "\n".join(output_lines))

    async def get_article_list(self, event: AstrMessageEvent):
        """获取文章列表"""
        yield self.chain_reply(event, "正在获取最新文章列表...")
        
        result = await self.api.get_article_list()
        
        if not result.get("success", False) and not self.is_success(result):
            yield self.chain_reply(event, f"获取文章列表失败：{result.get('msg', '未知错误')}")
            return
        
        articles_data = result.get("data", {}).get("articles", {}).get("list", {})
        
        # 合并所有分类的文章
        all_articles = []
        for category, items in articles_data.items():
            if isinstance(items, list):
                all_articles.extend(items)
        
        # 按时间排序
        all_articles.sort(key=lambda x: x.get("createdAt", ""), reverse=True)
        
        # 限制显示数量
        articles_to_show = all_articles[:15]
        
        if not articles_to_show:
            yield self.chain_reply(event, "暂无文章数据")
            return
        
        output_lines = ["📰【三角洲行动 - 最新文章列表】"]
        output_lines.append("━━━━━━━━━━━━━━━")
        
        for i, article in enumerate(articles_to_show, 1):
            title = article.get("title", "无标题")
            author = article.get("author", "未知")
            thread_id = article.get("threadID", "")
            created_at = article.get("createdAt", "")[:10]  # 只取日期部分
            view_count = article.get("viewCount", 0)
            liked_count = article.get("likedCount", 0)
            
            output_lines.append(f"\n{i}. 【{title}】")
            output_lines.append(f"   作者: {author} | ID: {thread_id}")
            output_lines.append(f"   发布: {created_at} | 👁 {view_count} | 👍 {liked_count}")
        
        output_lines.append("\n━━━━━━━━━━━━━━━")
        output_lines.append("使用 /三角洲 文章详情 <ID> 查看具体内容")
        
        yield self.chain_reply(event, "\n".join(output_lines))

    async def get_article_detail(self, event: AstrMessageEvent, thread_id: str):
        """获取文章详情"""
        if not thread_id:
            yield self.chain_reply(event, "请提供文章ID，如：/三角洲 文章详情 12345")
            return
        
        yield self.chain_reply(event, f"正在获取文章详情 (ID: {thread_id})...")
        
        result = await self.api.get_article_detail(thread_id)
        
        if not result.get("success", False) and not self.is_success(result):
            yield self.chain_reply(event, f"获取文章详情失败：{result.get('msg', '文章不存在或已删除')}")
            return
        
        article = result.get("data", {}).get("article", {})
        
        if not article:
            yield self.chain_reply(event, "文章不存在或已被删除")
            return
        
        # 构建文章详情
        title = article.get("title", "无标题")
        author_info = article.get("author", {})
        author_name = author_info.get("nickname", "未知作者") if isinstance(author_info, dict) else str(author_info)
        created_at = article.get("createdAt", "")
        view_count = article.get("viewCount", 0)
        liked_count = article.get("likedCount", 0)
        article_id = article.get("id", thread_id)
        
        output_lines = [f"📄【{title}】"]
        output_lines.append("━━━━━━━━━━━━━━━")
        output_lines.append(f"作者: {author_name}")
        output_lines.append(f"发布时间: {created_at}")
        output_lines.append(f"浏览: {view_count} | 点赞: {liked_count}")
        output_lines.append(f"ID: {article_id}")
        
        # 获取标签
        ext = article.get("ext", {})
        if ext and ext.get("gicpTags"):
            tags = ext.get("gicpTags", [])
            if tags:
                output_lines.append(f"标签: {', '.join(tags)}")
        
        output_lines.append("━━━━━━━━━━━━━━━")
        
        # 处理文章内容
        content = article.get("content", {})
        if content and content.get("text"):
            import re
            # 去除HTML标签
            text_content = re.sub(r'<[^>]+>', '', content.get("text", ""))
            text_content = text_content.replace("&nbsp;", " ").strip()
            
            # 限制内容长度
            if len(text_content) > 800:
                text_content = text_content[:800] + "...\n\n[内容过长，已截断]"
            
            if text_content:
                output_lines.append(f"\n{text_content}")
        elif article.get("summary"):
            output_lines.append(f"\n{article.get('summary')}")
        else:
            output_lines.append("\n[该文章没有可显示的文字内容]")
        
        yield self.chain_reply(event, "\n".join(output_lines))
        
        # 尝试发送封面图片
        cover = article.get("cover")
        if cover:
            cover_url = cover if cover.startswith("http") else f"https:{cover}"
            try:
                chain = [Comp.Image.fromURL(cover_url)]
                yield event.chain_result(chain)
            except Exception:
                pass  # 图片加载失败时静默忽略
