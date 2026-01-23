"""
渲染功能测试脚本
运行此脚本来验证渲染模块是否正常工作
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# Mock astrbot 模块用于独立测试
class MockLogger:
    def info(self, msg): print(f"[INFO] {msg}")
    def warning(self, msg): print(f"[WARN] {msg}")
    def error(self, msg): print(f"[ERROR] {msg}")
    def debug(self, msg): pass

class MockAstrbot:
    class api:
        logger = MockLogger()

sys.modules['astrbot'] = MockAstrbot()
sys.modules['astrbot.api'] = MockAstrbot.api


async def test_render():
    """测试渲染功能"""
    print("=" * 50)
    print("渲染功能测试")
    print("=" * 50)
    
    # 1. 测试导入
    print("\n[1] 测试模块导入...")
    try:
        from utils.render import Render, render_image
        print("    ✓ 模块导入成功")
    except ImportError as e:
        print(f"    ✗ 模块导入失败: {e}")
        return
    
    # 2. 测试路径
    print("\n[2] 检查资源路径...")
    print(f"    插件根目录: {Render.PLUGIN_ROOT}")
    print(f"    资源目录: {Render.RESOURCES_PATH}")
    print(f"    模板目录: {Render.TEMPLATE_PATH}")
    
    if Render.RESOURCES_PATH.exists():
        print("    ✓ 资源目录存在")
    else:
        print("    ✗ 资源目录不存在!")
        return
    
    # 3. 检查模板文件
    print("\n[3] 检查模板文件...")
    templates = [
        "common/common.html",
        "userInfo/userInfo.html",
        "userInfo/userInfo.css",
        "dailyReport/dailyReport.html",
        "dailyReport/dailyReport.css",
    ]
    for tpl in templates:
        tpl_path = Render.TEMPLATE_PATH / tpl
        if tpl_path.exists():
            print(f"    ✓ {tpl}")
        else:
            print(f"    ✗ {tpl} 不存在!")
    
    # 4. 检查资源文件
    print("\n[4] 检查资源文件...")
    resources = [
        "common/common.css",
        "fonts/p-med.ttf",
        "fonts/p-bold.ttf",
        "imgs/background/bg2-1.webp",
        "imgs/others/member-bg.webp",
        "imgs/rank/sol/3_3.webp",  # 黄金 III
    ]
    for res in resources:
        res_path = Render.RESOURCES_PATH / res
        if res_path.exists():
            print(f"    ✓ {res}")
        else:
            print(f"    ✗ {res} 不存在!")
    
    # 5. 测试工具函数
    print("\n[5] 测试工具函数...")
    bg = Render.get_background_image()
    print(f"    随机背景: {bg}")
    
    rank_sol = Render.get_rank_image("黄金 III", "sol")
    print(f"    烽火地带 黄金III 段位图: {rank_sol}")
    
    rank_mp = Render.get_rank_image("尉官 II", "mp")
    print(f"    全面战场 尉官II 段位图: {rank_mp}")
    
    # 6. 测试模板渲染
    print("\n[6] 测试模板渲染...")
    try:
        params = {
            'backgroundImage': Render.get_background_image(),
            'userAvatar': 'https://q1.qlogo.cn/g?b=qq&nk=123456&s=640',
            'userName': '测试用户',
            'registerTime': '2024-01-01 12:00:00',
            'lastLoginTime': '2024-12-20 18:30:00',
            'accountStatus': '账号状态: 正常',
            'solLevel': 50,
            'solRankName': '黄金 III',
            'solRankImage': Render.get_rank_image('黄金 III', 'sol'),
            'solTotalFight': 100,
            'solTotalEscape': 80,
            'solEscapeRatio': '80%',
            'solTotalKill': 500,
            'solDuration': '120小时30分',
            'hafCoin': '1,234,567',
            'totalAssets': '5.67M',
            'tdmLevel': 45,
            'tdmRankName': '尉官 II',
            'tdmRankImage': Render.get_rank_image('尉官 II', 'mp'),
            'tdmTotalFight': 200,
            'tdmTotalWin': 120,
            'tdmWinRatio': '60%',
            'tdmTotalKill': 800,
            'tdmDuration': '80小时15分',
        }
        
        html = Render.render_template('userInfo/userInfo.html', params)
        print(f"    ✓ HTML 渲染成功 (长度: {len(html)} 字符)")
        
        # 保存 HTML 用于调试
        output_html = Render.PLUGIN_ROOT / "test_output.html"
        output_html.write_text(html, encoding='utf-8')
        print(f"    ✓ HTML 已保存到: {output_html}")
        
    except Exception as e:
        print(f"    ✗ 模板渲染失败: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 7. 测试图片渲染（需要 playwright）
    print("\n[7] 测试图片渲染...")
    try:
        from playwright.async_api import async_playwright
        print("    ✓ playwright 已安装")
        
        image_bytes = await render_image(
            'userInfo/userInfo.html',
            params,
            width=1365,
            height=640
        )
        
        if image_bytes:
            output_img = Render.PLUGIN_ROOT / "test_output.png"
            output_img.write_bytes(image_bytes)
            print(f"    ✓ 图片渲染成功 (大小: {len(image_bytes)} 字节)")
            print(f"    ✓ 图片已保存到: {output_img}")
        else:
            print("    ✗ 图片渲染返回空")
            
    except ImportError:
        print("    ⚠ playwright 未安装，跳过图片渲染测试")
        print("    提示: pip install playwright && playwright install chromium")
    except Exception as e:
        print(f"    ✗ 图片渲染失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)


if __name__ == '__main__':
    asyncio.run(test_render())
