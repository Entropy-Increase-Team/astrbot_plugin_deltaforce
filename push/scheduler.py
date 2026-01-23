"""
推送调度器
使用 APScheduler 实现定时任务调度
"""
import asyncio
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime

from astrbot.api import logger

try:
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from apscheduler.triggers.cron import CronTrigger
    HAS_APSCHEDULER = True
except ImportError:
    HAS_APSCHEDULER = False
    logger.warning("APScheduler 未安装，定时推送功能将不可用。请安装: pip install apscheduler")


def normalize_cron(cron: str) -> Dict[str, str]:
    """
    将 cron 表达式规范化为 APScheduler 格式
    支持 5段(标准) 和 6段(带秒) 和 7段(Quartz带年) 格式
    
    Args:
        cron: cron 表达式，如 "0 8 * * *" 或 "0 0 8 * * *"
    
    Returns:
        APScheduler CronTrigger 参数字典
    """
    if not cron or not isinstance(cron, str):
        cron = "0 8 * * *"  # 默认每天8点
    
    # 替换 Quartz 的 ? 为 *
    cron = cron.replace("?", "*")
    parts = cron.strip().split()
    
    if len(parts) == 5:
        # 标准 5 段: 分 时 日 月 周
        minute, hour, day, month, day_of_week = parts
        second = "0"
    elif len(parts) == 6:
        # 6 段: 秒 分 时 日 月 周
        second, minute, hour, day, month, day_of_week = parts
    elif len(parts) == 7:
        # 7 段 Quartz: 秒 分 时 日 月 周 年 (忽略年)
        second, minute, hour, day, month, day_of_week, _ = parts
    else:
        # 默认每天8点
        second, minute, hour, day, month, day_of_week = "0", "0", "8", "*", "*", "*"
    
    return {
        "second": second,
        "minute": minute,
        "hour": hour,
        "day": day,
        "month": month,
        "day_of_week": day_of_week
    }


def cron_to_human(cron: str) -> str:
    """
    将 cron 表达式转换为中文描述
    """
    parts = cron.strip().replace("?", "*").split()
    
    # 规范化为 5 段
    if len(parts) == 6:
        parts = parts[1:]  # 去掉秒
    elif len(parts) == 7:
        parts = parts[1:6]  # 去掉秒和年
    
    if len(parts) != 5:
        return cron
    
    minute, hour, day, month, week = parts
    
    week_names = {
        "0": "周日", "1": "周一", "2": "周二", "3": "周三",
        "4": "周四", "5": "周五", "6": "周六", "7": "周日"
    }
    
    desc = []
    
    # 周
    if week != "*":
        if week in week_names:
            desc.append(week_names[week])
        else:
            desc.append(f"周{week}")
    
    # 日
    if day != "*":
        if day.startswith("*/"):
            desc.append(f"每{day[2:]}天")
        else:
            desc.append(f"{day}日")
    elif week == "*":
        desc.append("每天")
    
    # 时间
    time_parts = []
    if hour != "*":
        if hour.startswith("*/"):
            time_parts.append(f"每{hour[2:]}小时")
        else:
            time_parts.append(f"{hour}点")
    if minute != "*":
        if minute.startswith("*/"):
            time_parts.append(f"每{minute[2:]}分钟")
        else:
            time_parts.append(f"{minute}分")
    
    if time_parts:
        desc.append("".join(time_parts))
    
    return " ".join(desc) if desc else cron


class PushScheduler:
    """推送调度器"""
    
    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.jobs: Dict[str, Any] = {}
        self._started = False
    
    async def initialize(self):
        """初始化调度器"""
        if not HAS_APSCHEDULER:
            logger.error("APScheduler 未安装，无法初始化推送调度器")
            return False
        
        try:
            self.scheduler = AsyncIOScheduler(timezone="Asia/Shanghai")
            logger.info("推送调度器初始化成功")
            return True
        except Exception as e:
            logger.error(f"推送调度器初始化失败: {e}")
            return False
    
    async def start(self):
        """启动调度器"""
        if not self.scheduler:
            await self.initialize()
        
        if self.scheduler and not self._started:
            try:
                self.scheduler.start()
                self._started = True
                logger.info("推送调度器已启动")
            except Exception as e:
                logger.error(f"推送调度器启动失败: {e}")
    
    async def shutdown(self):
        """关闭调度器"""
        if self.scheduler and self._started:
            try:
                self.scheduler.shutdown(wait=False)
                self._started = False
                self.jobs.clear()
                logger.info("推送调度器已关闭")
            except Exception as e:
                logger.error(f"推送调度器关闭失败: {e}")
    
    def add_job(self, job_id: str, func: Callable, cron: str, **kwargs) -> bool:
        """
        添加定时任务
        
        Args:
            job_id: 任务唯一标识
            func: 要执行的异步函数
            cron: cron 表达式
            **kwargs: 传递给函数的参数
        
        Returns:
            是否添加成功
        """
        if not self.scheduler:
            logger.error("调度器未初始化")
            return False
        
        try:
            # 移除已存在的同名任务
            if job_id in self.jobs:
                self.remove_job(job_id)
            
            cron_params = normalize_cron(cron)
            trigger = CronTrigger(**cron_params)
            
            job = self.scheduler.add_job(
                func,
                trigger=trigger,
                id=job_id,
                name=job_id,
                kwargs=kwargs,
                replace_existing=True,
                misfire_grace_time=60  # 允许60秒的误差
            )
            
            self.jobs[job_id] = job
            logger.info(f"添加定时任务: {job_id} ({cron_to_human(cron)})")
            return True
            
        except Exception as e:
            logger.error(f"添加定时任务失败 [{job_id}]: {e}")
            return False
    
    def remove_job(self, job_id: str) -> bool:
        """移除定时任务"""
        if not self.scheduler:
            return False
        
        try:
            if job_id in self.jobs:
                self.scheduler.remove_job(job_id)
                del self.jobs[job_id]
                logger.info(f"移除定时任务: {job_id}")
                return True
        except Exception as e:
            logger.error(f"移除定时任务失败 [{job_id}]: {e}")
        
        return False
    
    def get_job_status(self) -> List[Dict[str, Any]]:
        """获取所有任务状态"""
        if not self.scheduler:
            return []
        
        status_list = []
        for job_id, job in self.jobs.items():
            next_run = job.next_run_time
            status_list.append({
                "id": job_id,
                "name": job.name,
                "next_run": next_run.strftime("%Y-%m-%d %H:%M:%S") if next_run else "未调度",
                "running": self._started
            })
        
        return status_list
    
    @property
    def is_running(self) -> bool:
        return self._started
