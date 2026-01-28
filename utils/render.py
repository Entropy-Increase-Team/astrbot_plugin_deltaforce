"""
渲染工具类
基于 Jinja2 模板引擎，提供 HTML 模板渲染和截图功能
用于生成游戏数据图片等
"""
import os
import base64
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, Union
from jinja2 import Environment, FileSystemLoader, select_autoescape
from astrbot.api import logger

# 尝试导入 playwright 用于截图
try:
    from playwright.async_api import async_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False
    logger.warning("未安装 playwright，图片渲染功能不可用。请执行: pip install playwright && playwright install chromium")


class Render:
    """渲染工具类"""
    
    # Jinja2 环境（类级别单例）
    _env: Optional[Environment] = None
    _plugin_root: Optional[Path] = None
    _resources_path: Optional[Path] = None
    _template_path: Optional[Path] = None
    
    @classmethod
    def _init_paths(cls):
        """延迟初始化路径，确保在运行时解析"""
        if cls._plugin_root is None:
            cls._plugin_root = Path(__file__).parent.parent.resolve()
            cls._resources_path = cls._plugin_root / "resources"
            
            # 模板目录 (处理大小写问题)
            cls._template_path = cls._resources_path / "Template"
            if not cls._template_path.exists():
                # 尝试小写
                lower_template = cls._resources_path / "template"
                if lower_template.exists():
                    cls._template_path = lower_template
                    
            logger.info(f"[Render] 插件根目录: {cls._plugin_root}")
            logger.info(f"[Render] 资源目录: {cls._resources_path}")
            logger.info(f"[Render] 模板目录: {cls._template_path}")
            logger.info(f"[Render] 模板目录存在: {cls._template_path.exists()}")
    
    @classmethod
    def get_plugin_root(cls) -> Path:
        cls._init_paths()
        return cls._plugin_root
    
    @classmethod
    def get_resources_dir(cls) -> Path:
        cls._init_paths()
        return cls._resources_path
    
    @classmethod
    def get_template_dir(cls) -> Path:
        cls._init_paths()
        return cls._template_path
    
    @classmethod
    def get_common_dir(cls) -> Path:
        cls._init_paths()
        return cls._resources_path / "common"
    
    # 兼容旧代码的属性访问
    @property
    def PLUGIN_ROOT(self) -> Path:
        return self.get_plugin_root()
    
    @property
    def RESOURCES_PATH(self) -> Path:
        return self.get_resources_dir()
    
    @property
    def TEMPLATE_PATH(self) -> Path:
        return self.get_template_dir()
    
    @property
    def COMMON_PATH(self) -> Path:
        return self.get_common_dir()
    
    @classmethod
    def get_env(cls) -> Environment:
        """获取 Jinja2 环境实例"""
        cls._init_paths()
        
        if cls._env is None:
            # 确保模板路径存在
            if not cls._template_path.exists():
                logger.error(f"[Render] 模板目录不存在: {cls._template_path}")
                # 列出资源目录内容帮助调试
                if cls._resources_path.exists():
                    contents = list(cls._resources_path.iterdir())
                    logger.error(f"[Render] 资源目录内容: {[c.name for c in contents]}")
            
            cls._env = Environment(
                loader=FileSystemLoader([
                    str(cls._template_path),
                    str(cls._resources_path),
                ]),
                autoescape=select_autoescape(['html', 'xml']),
                # 启用扩展
                extensions=['jinja2.ext.do'],
            )
            # 注意：不要覆盖 Jinja2 内置的 default 过滤器
            # Jinja2 内置的 default(value, default_value='', boolean=False) 已经够用
            cls._env.globals['_res_path'] = cls._resources_path.as_uri() + '/'
        return cls._env
    
    @classmethod
    def get_resources_path(cls) -> str:
        """获取资源目录的文件URI"""
        cls._init_paths()
        return cls._resources_path.as_uri() + '/'
    
    @classmethod
    def render_template(
        cls,
        template_name: str,
        params: Dict[str, Any],
        **kwargs
    ) -> str:
        """
        渲染模板为 HTML 字符串
        
        Args:
            template_name: 模板文件名，如 'userInfo/userInfo.html'
            params: 模板参数
            **kwargs: 额外参数
        
        Returns:
            渲染后的 HTML 字符串
        """
        env = cls.get_env()
        
        # 准备渲染参数
        render_params = {
            '_res_path': cls.get_resources_path(),
            'copyright': 'Created By AstrBot & DeltaForce-Plugin',
            **params
        }
        
        try:
            template = env.get_template(template_name)
            return template.render(**render_params)
        except Exception as e:
            logger.error(f"[Render] 模板渲染失败: {e}")
            raise
    
    @classmethod
    async def render_to_image(
        cls,
        template_name: str,
        params: Dict[str, Any],
        width: int = 1400,
        height: int = 10000,
        scale: float = 1.5,
        timeout: int = 60000,
        **kwargs
    ) -> Optional[bytes]:
        """
        渲染模板为图片
        
        Args:
            template_name: 模板文件名
            params: 模板参数
            width: 视口宽度
            height: 视口高度（会自动裁剪到实际内容高度）
            scale: 缩放比例
            timeout: 超时时间（毫秒）
            **kwargs: 额外参数
        
        Returns:
            图片的 bytes 数据，失败返回 None
        """
        if not HAS_PLAYWRIGHT:
            logger.error("[Render] playwright 未安装，无法进行图片渲染")
            return None
        
        try:
            # 先渲染 HTML
            html_content = cls.render_template(template_name, params, **kwargs)
            
            # 使用 playwright 截图
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--allow-file-access-from-files',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process'
                    ]
                )
                
                page = await browser.new_page(
                    viewport={'width': width, 'height': height},
                    device_scale_factor=scale
                )
                
                # 将 HTML 写入临时文件，使用 file:// 协议加载
                # 这样可以确保本地资源（图片、CSS等）能够正确加载
                temp_html_path = None
                try:
                    # 创建临时文件，放在资源目录下以便相对路径正确解析
                    temp_dir = cls.RESOURCES_PATH
                    temp_html_path = temp_dir / f"_temp_render_{os.getpid()}.html"
                    temp_html_path.write_text(html_content, encoding='utf-8')
                    
                    # 使用 file:// 协议加载临时文件
                    file_url = temp_html_path.as_uri()
                    await page.goto(file_url, wait_until='networkidle', timeout=timeout)
                    
                    # 等待字体和图片加载
                    await page.wait_for_timeout(800)
                    
                    # 等待所有图片加载完成
                    await page.evaluate("""
                        () => {
                            return Promise.all(
                                Array.from(document.images)
                                    .filter(img => !img.complete)
                                    .map(img => new Promise(resolve => {
                                        img.onload = img.onerror = resolve;
                                    }))
                            );
                        }
                    """)
                
                    # 获取实际内容区域 - 优先查找容器
                    container = await page.query_selector('#container')
                    if not container:
                        container = await page.query_selector('.container')
                    if not container:
                        container = await page.query_selector('.red-record-container')
                    if not container:
                        container = await page.query_selector('.red-record-list-container')
                    if not container:
                        container = await page.query_selector('.music-list-container')
                    if not container:
                        container = await page.query_selector('body')

                    if container:
                        # 直接对容器元素进行截图，这会自动处理尺寸和裁剪，且不会有额外白边
                        screenshot = await container.screenshot(type='png')
                    else:
                        screenshot = await page.screenshot(full_page=True, type='png')
                    
                    await browser.close()
                    return screenshot
                finally:
                    # 清理临时文件
                    if temp_html_path and temp_html_path.exists():
                        try:
                            temp_html_path.unlink()
                        except Exception:
                            pass
                
        except Exception as e:
            error_msg = str(e)
            if "loading shared libraries" in error_msg or "libnspr4.so" in error_msg:
                logger.error(f"[Render] 图片渲染失败: 缺少系统依赖。如果你在 Linux/Docker 环境下运行，请尝试运行: playwright install-deps")
            else:
                logger.error(f"[Render] 图片渲染失败: {e}")
            return None
    
    @classmethod
    async def render_to_base64(
        cls,
        template_name: str,
        params: Dict[str, Any],
        **kwargs
    ) -> Optional[str]:
        """
        渲染模板为 base64 图片字符串
        
        Args:
            template_name: 模板文件名
            params: 模板参数
            **kwargs: 传递给 render_to_image 的参数
        
        Returns:
            base64 编码的图片字符串，失败返回 None
        """
        image_bytes = await cls.render_to_image(template_name, params, **kwargs)
        if image_bytes:
            return base64.b64encode(image_bytes).decode('utf-8')
        return None
    
    @classmethod
    async def render_to_file(
        cls,
        template_name: str,
        params: Dict[str, Any],
        output_path: Union[str, Path],
        **kwargs
    ) -> bool:
        """
        渲染模板并保存为图片文件
        
        Args:
            template_name: 模板文件名
            params: 模板参数
            output_path: 输出文件路径
            **kwargs: 传递给 render_to_image 的参数
        
        Returns:
            是否保存成功
        """
        image_bytes = await cls.render_to_image(template_name, params, **kwargs)
        if image_bytes:
            try:
                output_path = Path(output_path)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                output_path.write_bytes(image_bytes)
                return True
            except Exception as e:
                logger.error(f"[Render] 图片保存失败: {e}")
        return False
    
    @classmethod
    def get_background_image(cls, index: int = None) -> str:
        """
        获取背景图片路径
        
        Args:
            index: 背景图片索引（1-7），为 None 时随机选择
        
        Returns:
            背景图片的 absolute file URI
        """
        import random
        if index is None:
            index = random.randint(1, 7)
        index = max(1, min(7, index))  # 限制范围
        return (cls.RESOURCES_PATH / f"imgs/background/bg2-{index}.webp").as_uri()
    
    @classmethod
    def get_rank_image(cls, rank_name: str, mode: str = 'sol') -> Optional[str]:
        """
        根据段位名称获取段位图片路径
        
        Args:
            rank_name: 段位名称（如"铂金 II"）
            mode: 游戏模式 ('sol' 烽火地带 或 'mp'/'tdm' 全面战场)
        
        Returns:
            段位图片的 absolute file URI，未找到返回 None
        """
        if not rank_name or '分数无效' in str(rank_name) or '未知' in str(rank_name):
            return None
        
        # 清理段位名称，移除分数和星级信息
        import re
        clean_rank_name = re.sub(r'\s*\(\d+\)', '', str(rank_name))
        clean_rank_name = re.sub(r'\d+星', '', clean_rank_name).strip()
        
        # 段位映射表
        rank_mappings = {
            'sol': {
                '青铜 V': '1_5', '青铜 IV': '1_4', '青铜 III': '1_3', '青铜 II': '1_2', '青铜 I': '1_1',
                '白银 V': '2_5', '白银 IV': '2_4', '白银 III': '2_3', '白银 II': '2_2', '白银 I': '2_1',
                '黄金 V': '3_5', '黄金 IV': '3_4', '黄金 III': '3_3', '黄金 II': '3_2', '黄金 I': '3_1',
                '铂金 V': '4_5', '铂金 IV': '4_4', '铂金 III': '4_3', '铂金 II': '4_2', '铂金 I': '4_1',
                '钻石 V': '5_5', '钻石 IV': '5_4', '钻石 III': '5_3', '钻石 II': '5_2', '钻石 I': '5_1',
                '黑鹰 V': '6_5', '黑鹰 IV': '6_4', '黑鹰 III': '6_3', '黑鹰 II': '6_2', '黑鹰 I': '6_1',
                '三角洲巅峰': '7'
            },
            'mp': {
                '列兵 V': '1_5', '列兵 IV': '1_4', '列兵 III': '1_3', '列兵 II': '1_2', '列兵 I': '1_1',
                '上等兵 V': '2_5', '上等兵 IV': '2_4', '上等兵 III': '2_3', '上等兵 II': '2_2', '上等兵 I': '2_1',
                '军士长 V': '3_5', '军士长 IV': '3_4', '军士长 III': '3_3', '军士长 II': '3_2', '军士长 I': '3_1',
                '尉官 V': '4_5', '尉官 IV': '4_4', '尉官 III': '4_3', '尉官 II': '4_2', '尉官 I': '4_1',
                '校官 V': '5_5', '校官 IV': '5_4', '校官 III': '5_3', '校官 II': '5_2', '校官 I': '5_1',
                '将军 V': '6_5', '将军 IV': '6_4', '将军 III': '6_3', '将军 II': '6_2', '将军 I': '6_1',
                '统帅': '7'
            }
        }
        
        # 统一模式名称
        mode_key = 'mp' if mode == 'tdm' else mode
        mappings = rank_mappings.get(mode_key)
        
        if not mappings:
            logger.warning(f"[Render] 未知的游戏模式: {mode}")
            return None
        
        rank_code = mappings.get(clean_rank_name)
        if not rank_code:
            logger.warning(f"[Render] 未找到段位映射: {clean_rank_name} (模式: {mode_key})")
            return None
        
        return (cls.RESOURCES_PATH / f"imgs/rank/{mode_key}/{rank_code}.webp").as_uri()

    @classmethod
    def get_map_image(cls, map_name: str, mode: str = 'sol') -> Optional[str]:
        """
        获取地图图片路径
        
        Args:
            map_name: 地图名称（如"零号大坝-常规"）
            mode: 游戏模式 ('sol' 烽火地带 或 'mp'/'tdm' 全面战场)
        
        Returns:
            地图图片的 absolute file URI
        """
        if not map_name:
            return None
            
        prefix = "烽火" if mode == 'sol' else "全面"
        ext = "png" if mode == 'sol' else "jpg"
        
        # 尝试直接拼接
        file_name = f"{prefix}-{map_name}.{ext}"
        file_path = cls.RESOURCES_PATH / f"imgs/map/{file_name}"
        
        if file_path.exists():
            return file_path.as_uri()
            
        # 尝试去掉后缀匹配 (仅烽火)
        if mode == 'sol':
             import re
             # 清理后缀，尝试匹配基础地图图片（如果有的话，或者回退逻辑）
             # 这里简单处理，如果找不到且是烽火模式，尝试查找包含该名称的文件
             # 但目前看图片命名是完整的，所以直接返回可能存在的默认图或者None
             pass

        return None


# 便捷函数
async def render_image(
    template_name: str,
    params: Dict[str, Any],
    **kwargs
) -> Optional[bytes]:
    """渲染模板为图片的便捷函数"""
    return await Render.render_to_image(template_name, params, **kwargs)


async def render_base64(
    template_name: str,
    params: Dict[str, Any],
    **kwargs
) -> Optional[str]:
    """渲染模板为 base64 的便捷函数"""
    return await Render.render_to_base64(template_name, params, **kwargs)
