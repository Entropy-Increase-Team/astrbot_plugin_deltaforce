"""
渲染模板使用示例
展示如何在 AstrBot 插件中使用渲染功能生成图片
"""
import astrbot.api.message_components as Comp
from astrbot.api.event import AstrMessageEvent
from ..utils.render import Render, render_image, render_base64


class RenderExample:
    """渲染示例类"""
    
    async def render_user_info_example(self, event: AstrMessageEvent):
        """
        渲染用户信息卡片示例
        使用 userInfo 模板
        """
        # 准备模板参数
        params = {
            # 背景图片（随机选择一个）
            'backgroundImage': Render.get_background_image(),
            
            # 用户基本信息
            'userAvatar': 'https://example.com/avatar.png',  # 用户头像URL
            'userName': '玩家昵称',
            'registerTime': '2024-01-01 12:00:00',
            'lastLoginTime': '2024-12-20 18:30:00',
            'accountStatus': '账号状态: 正常 | 封禁: 无 | 禁言: 无',
            
            # 烽火地带数据
            'solLevel': 50,
            'solRankName': '黄金 III',
            'solRankImage': Render.get_rank_image('黄金 III', 'sol'),  # 烽火地带段位
            'solTotalFight': 100,
            'solTotalEscape': 80,
            'solEscapeRatio': '80%',
            'solTotalKill': 500,
            'solDuration': '120小时30分',
            'hafCoin': '1,234,567',
            'totalAssets': '5.67M',
            
            # 全面战场数据
            'tdmLevel': 45,
            'tdmRankName': '尉官 II',
            'tdmRankImage': Render.get_rank_image('尉官 II', 'mp'),  # 全面战场段位
            'tdmTotalFight': 200,
            'tdmTotalWin': 120,
            'tdmWinRatio': '60%',
            'tdmTotalKill': 800,
            'tdmDuration': '80小时15分',
        }
        
        # 渲染模板为图片
        image_bytes = await render_image(
            'userInfo/userInfo.html',
            params,
            width=1365,
            height=640
        )
        
        if image_bytes:
            # 返回图片消息
            return Comp.Image.fromBytes(image_bytes)
        else:
            return Comp.Plain("渲染失败，请检查 playwright 是否安装")
    
    async def render_daily_report_example(self, event: AstrMessageEvent):
        """
        渲染日报示例
        使用 dailyReport 模板
        """
        params = {
            'type': 'daily',  # 'daily' 或 'profit'
            'userAvatar': 'https://example.com/avatar.png',
            'userName': '玩家昵称',
            'currentDate': '2024-12-20',
            
            # 烽火地带详情
            'solDetail': {
                'recentGainDate': '2024-12-19',
                'recentGain': '1,234,567',
                'isEmpty': False,
                'topItems': [
                    {'objectName': '高级武器', 'price': '500,000', 'imageUrl': ''},
                    {'objectName': '稀有护甲', 'price': '300,000', 'imageUrl': ''},
                ]
            },
            
            # 全面战场详情
            'mpDetail': {
                'recentDate': '2024-12-19',
                'isEmpty': False,
                'totalFightNum': 10,
                'totalWinNum': 6,
                'totalKillNum': 50,
                'totalScore': 12000,
                'operatorImage': 'imgs/operator/default.png',
                'bestMatch': {
                    'mapName': '营地突击',
                    'mapImage': 'imgs/map/default.png',
                    'dtEventTime': '18:30',
                    'isWinner': True,
                    'killNum': 15,
                    'death': 3,
                    'assist': 8,
                    'score': 2500,
                }
            }
        }
        
        image_bytes = await render_image(
            'dailyReport/dailyReport.html',
            params,
            width=1250,
            height=1000
        )
        
        if image_bytes:
            return Comp.Image.fromBytes(image_bytes)
        else:
            return Comp.Plain("渲染失败")
    
    async def render_to_html_string_example(self):
        """
        只渲染为 HTML 字符串（不生成图片）
        用于调试或其他用途
        """
        params = {
            'backgroundImage': 'imgs/background/bg2-1.webp',
            'userName': '测试用户',
            # ... 其他参数
        }
        
        html_content = Render.render_template(
            'userInfo/userInfo.html',
            params
        )
        
        return html_content


# ================== 在 Handler 中的使用示例 ==================

"""
在 handlers/info.py 中使用渲染功能的示例：

```python
from ..utils.render import Render, render_image

class InfoHandler(BaseHandler):
    
    async def get_personal_info_image(self, event: AstrMessageEvent):
        '''个人信息查询 - 图片版'''
        token, error = await self.get_active_token(event)
        if error:
            yield self.chain_reply(event, error)
            return
        
        # 获取数据
        result = await self.api.get_personal_info(frameworkToken=token)
        if not self.is_success(result):
            yield self.chain_reply(event, f"获取个人信息失败")
            return
        
        data = result.get("data", {})
        role_info = result.get("roleInfo", {})
        
        # 准备渲染参数
        params = {
            'backgroundImage': Render.get_background_image(),
            'userAvatar': f"https://q1.qlogo.cn/g?b=qq&nk={event.get_sender_id()}&s=640",
            'userName': self.decode_url(role_info.get("charac_name", "未知")),
            'registerTime': role_info.get("register_time", "-"),
            'lastLoginTime': role_info.get("last_login_time", "-"),
            # ... 其他参数
        }
        
        # 渲染图片
        image_bytes = await render_image(
            'userInfo/userInfo.html',
            params,
            width=1365,
            height=640
        )
        
        if image_bytes:
            yield event.chain_reply([Comp.Image.fromBytes(image_bytes)])
        else:
            yield self.chain_reply(event, "图片渲染失败，请确保已安装 playwright")
```
"""
