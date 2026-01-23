"""
娱乐处理器
包含：TTS语音、AI锐评等
"""
import asyncio
from astrbot.api.event import AstrMessageEvent
import astrbot.api.message_components as Comp
from .base import BaseHandler


class EntertainmentHandler(BaseHandler):
    """娱乐处理器"""

    # ==================== TTS语音功能 ====================

    async def get_tts_health(self, event: AstrMessageEvent):
        """获取TTS服务状态"""
        try:
            result = await self.api.get_tts_health()
            
            if not result or not result.get("success", False):
                yield self.chain_reply(event, "❌ TTS服务异常，请稍后重试")
                return

            lines = [
                "🎤【TTS语音合成服务状态】",
                f"状态：{result.get('message', '正常')}",
                f"预设加载：{'✅ 已加载' if result.get('presetsLoaded') else '❌ 未加载'}",
                f"预设数量：{result.get('presetCount', 0)} 个"
            ]
            
            if result.get("timestamp"):
                from datetime import datetime
                try:
                    time_str = datetime.fromisoformat(result['timestamp'].replace('Z', '+00:00')).strftime("%Y-%m-%d %H:%M:%S")
                    lines.append(f"检查时间：{time_str}")
                except:
                    pass

            yield self.chain_reply(event, "\n".join(lines))
            
        except Exception as e:
            yield self.chain_reply(event, f"❌ 获取TTS状态失败：{e}")

    async def get_tts_presets(self, event: AstrMessageEvent):
        """获取TTS角色预设列表"""
        try:
            result = await self.api.get_tts_presets()
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 获取失败：{result.get('msg', result.get('message', '未知错误'))}")
                return

            presets = result.get("data", [])
            if not presets:
                yield self.chain_reply(event, "📭 暂无可用的TTS角色预设")
                return

            lines = ["🎭【TTS角色预设列表】", "━━━━━━━━━━━━━━━━━━━━"]
            
            for i, preset in enumerate(presets[:20], 1):  # 最多显示20个
                name = preset.get("name", "未知")
                char_id = preset.get("characterId", preset.get("id", ""))
                emotions = preset.get("emotions", [])
                emotion_str = f"（{len(emotions)}种情感）" if emotions else ""
                lines.append(f"{i}. {name} [{char_id}] {emotion_str}")

            if len(presets) > 20:
                lines.append(f"... 等共 {len(presets)} 个角色")

            lines.append("")
            lines.append("💡 使用 /三角洲 tts角色详情 <角色ID> 查看详情")
            lines.append("💡 使用 /三角洲 tts <文字> 进行语音合成")

            yield self.chain_reply(event, "\n".join(lines))
            
        except Exception as e:
            yield self.chain_reply(event, f"❌ 获取TTS角色列表失败：{e}")

    async def get_tts_preset_detail(self, event: AstrMessageEvent, character_id: str = ""):
        """获取TTS角色预设详情"""
        if not character_id:
            yield self.chain_reply(event, "❌ 请指定角色ID\n用法：/三角洲 tts角色详情 <角色ID>")
            return

        try:
            result = await self.api.get_tts_preset_detail(character_id)
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 获取失败：{result.get('msg', result.get('message', '未知错误'))}")
                return

            data = result.get("data", {})
            if not data:
                yield self.chain_reply(event, "❌ 未找到该角色预设")
                return

            name = data.get("name", "未知")
            char_id = data.get("characterId", character_id)
            description = data.get("description", "无描述")
            emotions = data.get("emotions", [])

            lines = [
                f"🎭【TTS角色详情】",
                f"名称：{name}",
                f"ID：{char_id}",
                f"描述：{description}"
            ]

            if emotions:
                lines.append("")
                lines.append("🎭 可用情感：")
                for emotion in emotions:
                    emo_id = emotion.get("id", "")
                    emo_name = emotion.get("name", "")
                    lines.append(f"  • {emo_name} [{emo_id}]")

            lines.append("")
            lines.append(f"💡 使用：/三角洲 tts {char_id} <文字> [情感ID]")

            yield self.chain_reply(event, "\n".join(lines))
            
        except Exception as e:
            yield self.chain_reply(event, f"❌ 获取角色详情失败：{e}")

    async def tts_synthesize(self, event: AstrMessageEvent, args: str = ""):
        """TTS语音合成"""
        if not args:
            yield self.chain_reply(event, "❌ 请输入要合成的文字\n用法：/三角洲 tts <角色ID> <文字> [情感ID]\n或：/三角洲 tts <文字>（使用默认角色）")
            return

        # 解析参数
        parts = args.strip().split(maxsplit=2)
        
        # 默认值
        character = "default"
        text = args
        emotion = ""
        
        if len(parts) >= 2:
            # 第一个参数可能是角色ID
            first_part = parts[0]
            # 如果第一个部分看起来像是角色ID（英文或数字组合）
            if first_part.replace("-", "").replace("_", "").isalnum() and not first_part.isdigit():
                character = first_part
                if len(parts) >= 3:
                    text = parts[1]
                    emotion = parts[2]
                else:
                    text = parts[1]

        if len(text) > 1000:
            yield self.chain_reply(event, "❌ 文字过长，最多支持1000字符")
            return

        try:
            yield self.chain_reply(event, "🔄 正在合成语音，请稍候...")
            
            # 提交合成任务
            result = await self.api.tts_synthesize(text, character, emotion)
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 合成失败：{result.get('msg', result.get('message', '未知错误'))}")
                return

            task_id = result.get("data", {}).get("taskId") or result.get("taskId")
            if not task_id:
                yield self.chain_reply(event, "❌ 未获取到任务ID")
                return

            # 轮询任务状态
            max_wait = 60  # 最大等待60秒
            poll_interval = 2  # 每2秒查询一次
            elapsed = 0

            while elapsed < max_wait:
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

                status_result = await self.api.get_tts_task_status(task_id)
                
                if not status_result:
                    continue

                status = status_result.get("status") or status_result.get("data", {}).get("status")
                
                if status == "completed":
                    audio_url = status_result.get("audioUrl") or status_result.get("data", {}).get("audioUrl")
                    if audio_url:
                        # 返回语音消息
                        yield event.chain_reply([Comp.Record(file=audio_url)])
                        return
                    else:
                        yield self.chain_reply(event, "✅ 合成完成，但未获取到音频URL")
                        return
                        
                elif status == "failed":
                    error = status_result.get("error") or status_result.get("data", {}).get("error", "未知错误")
                    yield self.chain_reply(event, f"❌ 合成失败：{error}")
                    return
                    
                elif status in ["queued", "processing"]:
                    continue

            yield self.chain_reply(event, "⏰ 合成超时，请稍后重试")
            
        except Exception as e:
            yield self.chain_reply(event, f"❌ TTS合成失败：{e}")

    # ==================== AI锐评功能 ====================

    async def get_ai_presets(self, event: AstrMessageEvent):
        """获取AI预设列表"""
        try:
            result = await self.api.get_ai_presets()
            
            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 获取失败：{result.get('msg', result.get('message', '未知错误'))}")
                return

            presets = result.get("data", [])
            if not presets:
                yield self.chain_reply(event, "📭 暂无可用的AI预设")
                return

            lines = ["🤖【AI锐评预设列表】", "━━━━━━━━━━━━━━━━━━━━"]
            
            for preset in presets:
                code = preset.get("code", "")
                name = preset.get("name", "未知")
                desc = preset.get("description", "")
                lines.append(f"• {name} [{code}]")
                if desc:
                    lines.append(f"  {desc[:50]}{'...' if len(desc) > 50 else ''}")

            lines.append("")
            lines.append("💡 使用：/三角洲 ai评价 <模式> [预设代码]")

            yield self.chain_reply(event, "\n".join(lines))
            
        except Exception as e:
            yield self.chain_reply(event, f"❌ 获取AI预设列表失败：{e}")

    async def get_ai_commentary(self, event: AstrMessageEvent, args: str = ""):
        """AI锐评战绩"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        # 解析模式参数
        parts = args.strip().split() if args else []
        mode_str = parts[0] if parts else ""
        preset = parts[1] if len(parts) > 1 else ""

        # 解析游戏模式
        mode_type = "sol"
        mode_name = "烽火地带"
        
        if mode_str:
            mode_lower = mode_str.lower()
            if mode_lower in ["sol", "烽火", "烽火地带", "摸金", "4"]:
                mode_type = "sol"
                mode_name = "烽火地带"
            elif mode_lower in ["mp", "战场", "大战场", "全面战场", "5"]:
                mode_type = "mp"
                mode_name = "全面战场"
            else:
                yield self.chain_reply(event, (
                    "❌ 无法识别的游戏模式，请使用以下格式：\n"
                    "• /三角洲 ai锐评 sol/烽火 (烽火地带)\n"
                    "• /三角洲 ai锐评 mp/战场 (全面战场)\n"
                    "• /三角洲 ai锐评 (默认烽火地带)"
                ))
                return

        try:
            yield self.chain_reply(event, f"🤖 正在分析您的{mode_name}近期战绩，请耐心等待...")

            result = await self.api.get_ai_commentary(token, mode_type, preset)

            if not result or not self.is_success(result):
                yield self.chain_reply(event, f"❌ AI锐评失败：{result.get('msg', result.get('message', '请求失败')) if result else '无响应'}")
                return

            data = result.get("data", "")
            if not data:
                yield self.chain_reply(event, f"❌ {mode_name}模式AI锐评失败，未能生成有效内容")
                return

            # 解析流式响应内容
            full_answer = ""
            if isinstance(data, str):
                lines = data.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('data:'):
                        json_data = line[5:].strip()
                        try:
                            import json
                            parsed = json.loads(json_data)
                            if parsed.get("answer"):
                                full_answer += parsed["answer"]
                        except:
                            pass
                
                # 如果没有解析到流式内容，直接使用原始数据
                if not full_answer:
                    full_answer = data

            if full_answer.strip():
                yield self.chain_reply(event, f"🤖【{mode_name} AI锐评】\n\n{full_answer.strip()}")
            else:
                yield self.chain_reply(event, f"❌ {mode_name}模式AI锐评失败，未能生成有效内容")

        except Exception as e:
            yield self.chain_reply(event, f"❌ AI锐评出错：{e}")

    # ==================== 日报/周报功能 ====================

    async def get_daily_report(self, event: AstrMessageEvent, args: str = ""):
        """获取日报"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        # 解析日期参数（可选）
        date_str = args.strip() if args else ""
        
        # 默认昨天
        if not date_str:
            from datetime import datetime, timedelta
            yesterday = datetime.now() - timedelta(days=1)
            date_str = yesterday.strftime("%Y%m%d")

        try:
            result = await self.api.get_daily_record(token, "", date_str)

            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 获取日报失败：{result.get('msg', result.get('message', '未知错误'))}")
                return

            data = result.get("data", {})
            sol_data = data.get("sol", {}).get("data", {}).get("data", {}).get("solDetail")
            mp_data = data.get("mp", {}).get("data", {}).get("data", {}).get("mpDetail")

            if not sol_data and not mp_data:
                yield self.chain_reply(event, f"📭 {date_str} 无游戏数据")
                return

            lines = [f"📅【{date_str} 日报】", "━━━━━━━━━━━━━━━━━━━━"]

            # 全面战场数据
            if mp_data and mp_data.get("recentDate", "").strip():
                lines.append("")
                lines.append("🎮【全面战场】")
                lines.append(f"对局数：{mp_data.get('totalFightNum', 0)}")
                lines.append(f"胜场数：{mp_data.get('totalWinNum', 0)}")
                lines.append(f"击杀数：{mp_data.get('totalKillNum', 0)}")
                lines.append(f"总得分：{mp_data.get('totalScore', 0):,}")
            
            # 烽火地带数据
            if sol_data and sol_data.get("recentGainDate", "").strip():
                lines.append("")
                lines.append("🔥【烽火地带】")
                lines.append(f"收益日期：{sol_data.get('recentGainDate', '-')}")
                lines.append(f"当日收益：{sol_data.get('recentGain', 0):,}")
                
                top_items = sol_data.get("userCollectionTop", {}).get("list", [])
                if top_items:
                    lines.append("📦 收获物品：")
                    for item in top_items[:5]:
                        name = item.get("objectName", "未知物品")
                        count = item.get("count", 0)
                        price = item.get("price", 0)
                        lines.append(f"  • {name} x{count} (￥{float(price):,.0f})")

            yield self.chain_reply(event, "\n".join(lines))

        except Exception as e:
            yield self.chain_reply(event, f"❌ 获取日报失败：{e}")

    async def get_yesterday_profit(self, event: AstrMessageEvent, args: str = ""):
        """获取昨日收益"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        try:
            yield self.chain_reply(event, "正在查询昨日收益数据...")

            # 计算昨日日期
            from datetime import datetime, timedelta
            yesterday = datetime.now() - timedelta(days=1)
            yesterday_str = yesterday.strftime("%Y%m%d")

            result = await self.api.get_daily_record(token, "", yesterday_str)

            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 获取失败：{result.get('msg', result.get('message', '未知错误'))}")
                return

            data = result.get("data", {})
            sol_detail = data.get("sol", {}).get("data", {}).get("data", {}).get("solDetail")

            if not sol_detail or not sol_detail.get("userCollectionTop"):
                yield self.chain_reply(event, "📭 暂无昨日收益数据，快去摸金吧！")
                return

            recent_gain = sol_detail.get("recentGain", 0)
            gain_date = sol_detail.get("recentGainDate", "昨日")
            top_items = sol_detail.get("userCollectionTop", {}).get("list", [])

            lines = [
                f"💰【昨日收益】{gain_date}",
                "━━━━━━━━━━━━━━━━━━━━",
                f"总收益：￥{int(recent_gain):,}",
                ""
            ]

            if top_items:
                lines.append("🏆 获取物品TOP:")
                for i, item in enumerate(top_items[:10], 1):
                    name = item.get("objectName", "未知")
                    price = int(item.get("price", 0))
                    count = item.get("count", 1)
                    lines.append(f"  {i}. {name} x{count} (￥{price:,})")

            yield self.chain_reply(event, "\n".join(lines))

        except Exception as e:
            yield self.chain_reply(event, f"❌ 获取昨日收益失败：{e}")

    async def get_weekly_report(self, event: AstrMessageEvent, args: str = ""):
        """获取周报"""
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return

        try:
            result = await self.api.get_weekly_record(token, "", True)

            if not self.is_success(result):
                yield self.chain_reply(event, f"❌ 获取周报失败：{result.get('msg', result.get('message', '未知错误'))}")
                return

            data = result.get("data", {})
            sol_data = data.get("sol", {}).get("data", {}).get("data")
            mp_data = data.get("mp", {}).get("data", {}).get("data")

            if not sol_data and not mp_data:
                yield self.chain_reply(event, "📭 本周无游戏数据")
                return

            from datetime import datetime
            current_date = datetime.now().strftime("%Y-%m-%d")
            lines = [f"📊【周报 截至{current_date}】", "━━━━━━━━━━━━━━━━━━━━"]

            # 全面战场周报
            if mp_data:
                total_games = mp_data.get("total_mp_num", 0)
                if total_games and int(total_games) > 0:
                    lines.append("")
                    lines.append("🎮【全面战场】")
                    lines.append(f"对局数：{total_games}")
                    lines.append(f"胜场数：{mp_data.get('win_mp_num', 0)}")
                    lines.append(f"总击杀：{mp_data.get('total_kill', 0)}")
                    lines.append(f"总死亡：{mp_data.get('total_death', 0)}")
                    lines.append(f"总得分：{int(mp_data.get('total_score', 0)):,}")
                    
                    # 计算KD
                    kills = int(mp_data.get("total_kill", 0))
                    deaths = int(mp_data.get("total_death", 0))
                    kd = f"{kills / deaths:.2f}" if deaths > 0 else "∞"
                    lines.append(f"K/D比：{kd}")

            # 烽火地带周报
            if sol_data:
                total_games = sol_data.get("total_sol_num", 0)
                if total_games and int(total_games) > 0:
                    lines.append("")
                    lines.append("🔥【烽火地带】")
                    lines.append(f"对局数：{total_games}")
                    
                    gained = float(sol_data.get("Gained_Price", 0))
                    consume = float(sol_data.get("consume_Price", 0))
                    profit = gained - consume
                    
                    lines.append(f"收益：￥{gained:,.0f}")
                    lines.append(f"消费：￥{consume:,.0f}")
                    lines.append(f"净利润：￥{profit:,.0f}")
                    
                    if consume > 0:
                        ratio = gained / consume
                        lines.append(f"赚损比：{ratio:.2f}")

            yield self.chain_reply(event, "\n".join(lines))

        except Exception as e:
            yield self.chain_reply(event, f"❌ 获取周报失败：{e}")
