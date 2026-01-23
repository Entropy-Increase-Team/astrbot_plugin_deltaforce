"""
计算器处理器
包含：伤害计算、战备计算、维修计算
完整版本，支持交互式命令和快捷命令
"""
import json
import math
import os
import re
from typing import Dict, List, Optional, Tuple, Any
from astrbot.api.event import AstrMessageEvent
import astrbot.api.message_components as Comp
from .base import BaseHandler
from ..utils.calculate import Calculate


class CalculatorHandler(BaseHandler):
    """计算器处理器"""
    
    def __init__(self, api, db_manager):
        super().__init__(api, db_manager)
        self.data_loaded = False
        self.armors_data = {}
        self.weapons_sol = {}
        self.weapons_mp = {}
        self.bullets_data = {}
        self.equipment_data = {}
        self.calculator = Calculate()
        self._load_data()
        
        # 武器简写映射表
        self.weapon_shortcuts = {
            # 突击步枪
            'tenglong': '腾龙', 'tl': '腾龙',
            'ak': 'AK', 'm4': 'M4',
            'car': 'CAR', 'kc': 'KC',
            # 狙击步枪
            'awm': 'AWM', 'svd': 'SVD',
            'm24': 'M24', 'k98': 'K98',
            # 冲锋枪
            'mp5': 'MP5', 'mp7': 'MP7', 'ump': 'UMP',
            'vector': 'VECTOR', 'p90': 'P90',
            # 霰弹枪
            'spas': 'SPAS', 's12k': 'S12K',
            # 机枪
            'mg': 'MG', 'pkm': 'PKM',
            # 手枪
            'g18': 'G18', 'm1911': 'M1911', 'p9': 'P9',
        }
        
        # 护甲简写映射表
        self.armor_shortcuts = {
            'fs': '飞鲨', 'feisha': '飞鲨',
            'dich': '帝骋', 'dc': '帝骋', 'dich9': '帝骋',
            'titan': '泰坦', 'tt': '泰坦',
            'gn': '钢能', 'gnht': '钢能',
            'jw': '巨卫', 'juwei': '巨卫',
            'nh': '尼龙', 'nilong': '尼龙',
            'jy': '精英', 'jingying': '精英',
            'dt': 'DT', 'avs': 'AVS', 'dtavs': 'DT-AVS',
            'ss': '武士', 'wushi': '武士',
            'zs': '制式', 'zhishi': '制式',
            'tgh': 'TG-H',
            'gt5': 'GT5', 'gt': 'GT5',
            'h70': 'H70',
            'lsgg': '老式钢盔', '钢盔': '老式钢盔',
            'motuo': '摩托', 'mt': '摩托',
            'qx': '轻型', 'qingxing': '轻型',
        }
        
        # 子弹简写映射表
        self.bullet_shortcuts = {
            'ap': 'AP', 'fmj': 'FMJ', 'hp': 'HP',
            'jhp': 'JHP', 'rip': 'RIP',
            'dvc': 'DVC', 'hs': 'HS',
            'sp': 'SP', 'sub': 'SUB',
        }
        
        # 命中部位映射
        self.hit_part_map = {
            '头': '头部', '头部': '头部', 'head': '头部', '1': '头部',
            '胸': '胸部', '胸部': '胸部', 'chest': '胸部', '2': '胸部',
            '腹': '腹部', '腹部': '腹部', 'abdomen': '腹部', '3': '腹部',
            '大臂': '大臂', 'upper_arm': '大臂', '4': '大臂',
            '小臂': '小臂', 'lower_arm': '小臂', '5': '小臂',
            '大腿': '大腿', 'thigh': '大腿', '6': '大腿',
            '小腿': '小腿', 'calf': '小腿', '7': '小腿',
        }
        
        # 游戏模式映射
        self.mode_map = {
            'sol': 'sol', '烽火': 'sol', '烽火地带': 'sol', '摸金': 'sol',
            'mp': 'mp', '战场': 'mp', '全面': 'mp', '大战场': 'mp', '全面战场': 'mp',
        }
    
    def _load_data(self):
        """加载计算所需的本地数据"""
        try:
            # 获取数据目录路径
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "data")
            
            # 如果本地没有数据目录，标记为未加载
            if not os.path.exists(data_dir):
                self.data_loaded = False
                return
            
            # 尝试加载护甲数据
            armors_file = os.path.join(data_dir, "armors.json")
            if os.path.exists(armors_file):
                with open(armors_file, 'r', encoding='utf-8') as f:
                    self.armors_data = json.load(f)
            
            # 尝试加载武器数据（烽火）
            weapons_sol_file = os.path.join(data_dir, "weapons_sol.json")
            if os.path.exists(weapons_sol_file):
                with open(weapons_sol_file, 'r', encoding='utf-8') as f:
                    self.weapons_sol = json.load(f)
            
            # 尝试加载武器数据（全面战场）
            weapons_mp_file = os.path.join(data_dir, "weapons_mp.json")
            if os.path.exists(weapons_mp_file):
                with open(weapons_mp_file, 'r', encoding='utf-8') as f:
                    self.weapons_mp = json.load(f)
            
            # 尝试加载子弹数据
            bullets_file = os.path.join(data_dir, "bullets.json")
            if os.path.exists(bullets_file):
                with open(bullets_file, 'r', encoding='utf-8') as f:
                    self.bullets_data = json.load(f)
            
            # 尝试加载装备数据
            equipment_file = os.path.join(data_dir, "equipment.json")
            if os.path.exists(equipment_file):
                with open(equipment_file, 'r', encoding='utf-8') as f:
                    self.equipment_data = json.load(f)
            
            self.data_loaded = True
        except Exception as e:
            self.data_loaded = False
    
    # ==================== 数据搜索方法 ====================
    
    def _get_all_weapons(self, mode: str = 'sol') -> List[Dict]:
        """获取所有武器列表"""
        weapons_data = self.weapons_sol if mode == 'sol' else self.weapons_mp
        all_weapons = []
        
        if 'weapons' in weapons_data:
            for category, weapon_list in weapons_data['weapons'].items():
                if isinstance(weapon_list, list):
                    for weapon in weapon_list:
                        weapon['category'] = category
                        all_weapons.append(weapon)
        
        return all_weapons
    
    def _get_all_armors(self) -> List[Dict]:
        """获取所有护甲（包含头盔）列表"""
        all_armors = []
        
        if 'armors' in self.armors_data:
            armors = self.armors_data['armors']
            if 'body_armor' in armors:
                for armor in armors['body_armor']:
                    armor['is_helmet'] = False
                    all_armors.append(armor)
            if 'helmets' in armors:
                for helmet in armors['helmets']:
                    helmet['is_helmet'] = True
                    all_armors.append(helmet)
        
        return all_armors
    
    def _get_bullets_by_caliber(self, caliber: str) -> List[Dict]:
        """根据口径获取子弹列表"""
        if 'bullets' in self.bullets_data:
            for cal, bullets in self.bullets_data['bullets'].items():
                if cal == caliber or caliber in cal:
                    return bullets
        return []
    
    def _fuzzy_search_weapon(self, name: str, mode: str = 'sol') -> Optional[Dict]:
        """模糊搜索武器"""
        name_lower = name.lower()
        
        # 检查简写映射
        search_name = self.weapon_shortcuts.get(name_lower, name)
        
        all_weapons = self._get_all_weapons(mode)
        
        # 精确匹配
        for weapon in all_weapons:
            if weapon.get('name', '') == search_name:
                return weapon
        
        # 包含匹配
        for weapon in all_weapons:
            weapon_name = weapon.get('name', '')
            if search_name.lower() in weapon_name.lower():
                return weapon
        
        # 拼音/简写模糊匹配
        for weapon in all_weapons:
            weapon_name = weapon.get('name', '').lower()
            if name_lower in weapon_name:
                return weapon
        
        return None
    
    def _fuzzy_search_armor(self, name: str) -> Optional[Dict]:
        """模糊搜索护甲/头盔"""
        name_lower = name.lower()
        
        # 检查简写映射
        search_name = self.armor_shortcuts.get(name_lower, name)
        
        all_armors = self._get_all_armors()
        
        # 精确匹配
        for armor in all_armors:
            if armor.get('name', '') == search_name:
                return armor
        
        # 包含匹配
        for armor in all_armors:
            armor_name = armor.get('name', '')
            if search_name in armor_name:
                return armor
        
        return None
    
    def _fuzzy_search_bullet(self, name: str, caliber: str = None) -> Optional[Dict]:
        """模糊搜索子弹"""
        name_lower = name.lower()
        
        # 检查简写映射
        search_name = self.bullet_shortcuts.get(name_lower, name)
        
        # 如果指定了口径，优先在该口径中搜索
        if caliber:
            bullets = self._get_bullets_by_caliber(caliber)
            for bullet in bullets:
                bullet_name = bullet.get('name', '')
                if search_name.lower() in bullet_name.lower():
                    return bullet
        
        # 全局搜索
        if 'bullets' in self.bullets_data:
            for cal, bullets in self.bullets_data['bullets'].items():
                for bullet in bullets:
                    bullet_name = bullet.get('name', '')
                    if search_name.lower() in bullet_name.lower():
                        bullet['caliber'] = cal
                        return bullet
        
        return None
    
    def _parse_game_mode(self, mode_str: str) -> Optional[str]:
        """解析游戏模式"""
        mode_lower = mode_str.lower()
        return self.mode_map.get(mode_lower)
    
    def _parse_hit_parts(self, hit_str: str, total_shots: int) -> Dict:
        """
        解析命中部位分配
        支持格式：
        - "2" - 全部打胸部
        - "1:2,2:4" - 头部2发，胸部4发
        - "头:2,胸:4" - 头部2发，胸部4发
        """
        result = {'success': False, 'data': {}, 'error': ''}
        
        if ':' in hit_str or '：' in hit_str:
            # 高级格式
            hit_str = hit_str.replace('：', ':')
            parts = hit_str.split(',')
            
            hit_parts = {}
            total_allocated = 0
            
            for part in parts:
                if ':' not in part:
                    result['error'] = f"格式错误：{part}"
                    return result
                
                part_name, count_str = part.split(':')
                part_name = part_name.strip()
                
                try:
                    count = int(count_str.strip())
                except:
                    result['error'] = f"数量无效：{count_str}"
                    return result
                
                # 映射部位名称
                mapped_part = self.hit_part_map.get(part_name, part_name)
                if mapped_part not in ['头部', '胸部', '腹部', '大臂', '小臂', '大腿', '小腿']:
                    result['error'] = f"未知部位：{part_name}"
                    return result
                
                hit_parts[mapped_part] = hit_parts.get(mapped_part, 0) + count
                total_allocated += count
            
            if total_allocated != total_shots:
                result['error'] = f"分配数量({total_allocated})与射击次数({total_shots})不符"
                return result
            
            result['success'] = True
            result['data'] = hit_parts
        else:
            # 简单格式
            try:
                part_index = int(hit_str.strip())
            except:
                result['error'] = "请输入有效数字"
                return result
            
            part_names = ['头部', '胸部', '腹部', '大臂', '小臂', '大腿', '小腿']
            if part_index < 1 or part_index > len(part_names):
                result['error'] = f"部位序号需在1-{len(part_names)}之间"
                return result
            
            part_name = part_names[part_index - 1]
            result['success'] = True
            result['data'] = {part_name: total_shots}
        
        return result
    
    def _parse_armor_selection(self, armor_str: str) -> Dict:
        """
        解析护甲选择
        支持格式：
        - "1" - 无护甲
        - "2:3" - 头盔2+护甲3
        - "fs:tt" - 飞鲨头盔+泰坦护甲
        """
        result = {'success': False, 'armor': None, 'helmet': None, 'error': ''}
        
        all_armors = self._get_all_armors()
        
        if ':' in armor_str or '：' in armor_str:
            # 组合格式
            armor_str = armor_str.replace('：', ':')
            parts = armor_str.split(':')
            
            if len(parts) != 2:
                result['error'] = "组合格式应为：头盔:护甲"
                return result
            
            helmet_str, armor_part = parts
            
            # 搜索头盔
            try:
                helmet_idx = int(helmet_str) - 2
                if helmet_idx >= 0 and helmet_idx < len(all_armors):
                    helmet = all_armors[helmet_idx]
                else:
                    result['error'] = f"头盔序号无效：{helmet_str}"
                    return result
            except:
                helmet = self._fuzzy_search_armor(helmet_str)
                if not helmet:
                    result['error'] = f"未找到头盔：{helmet_str}"
                    return result
            
            # 搜索护甲
            try:
                armor_idx = int(armor_part) - 2
                if armor_idx >= 0 and armor_idx < len(all_armors):
                    armor = all_armors[armor_idx]
                else:
                    result['error'] = f"护甲序号无效：{armor_part}"
                    return result
            except:
                armor = self._fuzzy_search_armor(armor_part)
                if not armor:
                    result['error'] = f"未找到护甲：{armor_part}"
                    return result
            
            result['success'] = True
            result['helmet'] = helmet if helmet.get('is_helmet', False) or '头盔' in helmet.get('name', '') else None
            result['armor'] = armor if not armor.get('is_helmet', False) and '头盔' not in armor.get('name', '') else None
        else:
            # 单选格式
            if armor_str == '1' or armor_str.lower() == 'none' or armor_str == '无':
                result['success'] = True
                return result
            
            # 尝试序号
            try:
                armor_idx = int(armor_str) - 2
                if armor_idx >= 0 and armor_idx < len(all_armors):
                    armor = all_armors[armor_idx]
                    if armor.get('is_helmet', False) or '头盔' in armor.get('name', ''):
                        result['helmet'] = armor
                    else:
                        result['armor'] = armor
                    result['success'] = True
                    return result
            except:
                pass
            
            # 尝试模糊搜索
            armor = self._fuzzy_search_armor(armor_str)
            if armor:
                if armor.get('is_helmet', False) or '头盔' in armor.get('name', ''):
                    result['helmet'] = armor
                else:
                    result['armor'] = armor
                result['success'] = True
            else:
                result['error'] = f"未找到装备：{armor_str}"
        
        return result
    
    # ==================== 快捷伤害计算 ====================
    
    async def quick_damage(self, event: AstrMessageEvent, args: str):
        """
        快捷伤害计算
        格式：伤害 模式 武器名 子弹名 护甲 距离 次数 部位分配
        示例：伤害 烽火 腾龙 dvc12 41:37 50 6 1:2,2:4
        """
        if not args:
            help_msg = """💥【伤害计算帮助】

📝 命令格式:
/三角洲 伤害 <模式> <武器> <子弹> <护甲> <距离> <次数> <部位>

📋 参数说明:
• 模式: 烽火/全面 (sol/mp)
• 武器: 武器名称(支持模糊搜索)
• 子弹: 子弹类型(支持模糊搜索)
• 护甲: 1=无护甲, 序号, 或 头盔:护甲
• 距离: 射击距离(米)
• 次数: 射击次数(1-20)
• 部位: 2=全打胸部, 或 1:2,2:4

📌 示例:
• /三角洲 伤害 烽火 腾龙 dvc12 tt 50 6 2
• /三角洲 伤害 sol 腾龙 ap fs:tt 30 6 头:2,胸:4

💡 部位说明:
1=头部, 2=胸部, 3=腹部
4=大臂, 5=小臂, 6=大腿, 7=小腿"""
            yield self.chain_reply(event, help_msg)
            return
        
        parts = args.strip().split()
        if len(parts) < 7:
            yield self.chain_reply(event, "❌ 参数不足\n格式：伤害 模式 武器 子弹 护甲 距离 次数 部位")
            return
        
        mode_str, weapon_name, bullet_name, armor_str, distance_str, shots_str = parts[:6]
        hit_parts_str = parts[6] if len(parts) > 6 else "2"
        
        # 解析游戏模式
        mode = self._parse_game_mode(mode_str)
        if not mode:
            yield self.chain_reply(event, "❌ 游戏模式错误\n支持: sol/烽火/摸金, mp/全面/战场")
            return
        
        # 解析距离和次数
        try:
            distance = float(distance_str)
            shots = int(shots_str)
        except:
            yield self.chain_reply(event, "❌ 距离或次数格式错误")
            return
        
        if shots < 1 or shots > 20:
            yield self.chain_reply(event, "❌ 射击次数需在1-20之间")
            return
        
        # 搜索武器
        weapon = self._fuzzy_search_weapon(weapon_name, mode)
        if not weapon:
            yield self.chain_reply(event, f"❌ 未找到武器：{weapon_name}")
            return
        
        # 搜索子弹
        bullet = self._fuzzy_search_bullet(bullet_name, weapon.get('caliber'))
        if not bullet:
            yield self.chain_reply(event, f"❌ 未找到子弹：{bullet_name}")
            return
        
        # 解析护甲
        armor_result = self._parse_armor_selection(armor_str)
        if not armor_result['success']:
            yield self.chain_reply(event, f"❌ {armor_result['error']}")
            return
        
        # 解析命中部位
        hit_result = self._parse_hit_parts(hit_parts_str, shots)
        if not hit_result['success']:
            yield self.chain_reply(event, f"❌ {hit_result['error']}")
            return
        
        # 构建命中部位数组
        hit_parts_array = []
        for part_name, count in hit_result['data'].items():
            for _ in range(count):
                hit_parts_array.append(part_name)
        
        # 构建护甲数据
        armor_data = {
            'armor': armor_result['armor'],
            'helmet': armor_result['helmet']
        }
        
        # 执行计算
        result = self.calculator.calculate_damage(
            weapon=weapon,
            armor_data=armor_data,
            bullet=bullet,
            hit_data={
                'distance': distance,
                'hit_parts': hit_parts_array,
                'fire_mode': 1,
                'trigger_delay': 0
            }
        )
        
        if not result.get('success'):
            yield self.chain_reply(event, f"❌ 计算失败：{result.get('error', '未知错误')}")
            return
        
        # 格式化结果
        output = self._format_damage_result(result, mode, weapon, bullet, armor_result, distance, shots, hit_result['data'])
        yield self.chain_reply(event, output)
    
    def _format_damage_result(self, result: Dict, mode: str, weapon: Dict, bullet: Dict, 
                               armor_result: Dict, distance: float, shots: int, hit_parts: Dict) -> str:
        """格式化伤害计算结果"""
        mode_name = '烽火地带' if mode == 'sol' else '全面战场'
        
        lines = [
            f"💥【伤害计算结果】",
            f"━━━━━━━━━━━━━━━━",
            f"🎮 模式: {mode_name}",
            f"🔫 武器: {weapon.get('name', '')}",
            f"💢 子弹: {bullet.get('name', '')} (穿透{bullet.get('penetrationLevel', 0)}级)",
            f"📏 距离: {distance}米",
            f"🎯 射击: {shots}发",
            ""
        ]
        
        # 护甲信息
        armor = armor_result.get('armor')
        helmet = armor_result.get('helmet')
        if armor:
            lines.append(f"🛡️ 护甲: {armor.get('name', '无')} ({armor.get('protectionLevel', 0)}级)")
        if helmet:
            lines.append(f"⛑️ 头盔: {helmet.get('name', '无')} ({helmet.get('protectionLevel', 0)}级)")
        if not armor and not helmet:
            lines.append("🛡️ 护甲: 无")
        
        # 命中部位分配
        hit_str = ', '.join([f"{p}×{c}" for p, c in hit_parts.items()])
        lines.append(f"🎯 命中: {hit_str}")
        lines.append("")
        
        # 计算结果
        lines.append("📊 【计算结果】")
        lines.append(f"⚔️ 击杀用弹: {result.get('shotsToKill', '?')}发")
        lines.append(f"💔 总伤害: {result.get('totalDamage', 0):.1f}")
        lines.append(f"🛡️ 护甲伤害: {result.get('totalArmorDamage', 0):.1f}")
        lines.append(f"❤️ 剩余血量: {result.get('finalPlayerHealth', 0):.1f}")
        
        if result.get('isKilled'):
            lines.append(f"💀 结果: 击杀成功！")
        else:
            lines.append(f"⚠️ 结果: 未击杀")
        
        # 详细射击记录（简化版）
        shot_results = result.get('shotResults', [])
        if shot_results and len(shot_results) <= 10:
            lines.append("")
            lines.append("📋 【射击详情】")
            for shot in shot_results:
                prot_str = "🛡️" if shot.get('isProtected') else "💔"
                lines.append(f"  {shot['shotNumber']}发 {shot['hitPart']}: {shot['damage']:.1f}伤害 {prot_str}")
                if shot.get('isKill'):
                    lines.append(f"  → 击杀！")
                    break
        
        return '\n'.join(lines)
    
    # ==================== 战场伤害计算（全面战场） ====================
    
    async def battlefield_damage(self, event: AstrMessageEvent, args: str):
        """
        战场伤害计算（全面战场模式，无护甲影响）
        格式：战场伤害 武器名 距离 [部位]
        """
        if not args:
            help_msg = """⚔️【战场伤害计算帮助】

📝 命令格式:
/三角洲 战场伤害 <武器> <距离> [部位]

📋 参数说明:
• 武器: 武器名称(支持模糊搜索)
• 距离: 射击距离(米)
• 部位: 可选，默认胸部

📌 示例:
• /三角洲 战场伤害 腾龙 50
• /三角洲 战场伤害 m4 30 头"""
            yield self.chain_reply(event, help_msg)
            return
        
        parts = args.strip().split()
        if len(parts) < 2:
            yield self.chain_reply(event, "❌ 参数不足\n格式：战场伤害 武器名 距离 [部位]")
            return
        
        weapon_name = parts[0]
        distance_str = parts[1]
        hit_part = parts[2] if len(parts) > 2 else 'chest'
        
        # 解析距离
        try:
            distance = float(distance_str)
        except:
            yield self.chain_reply(event, "❌ 距离格式错误")
            return
        
        # 搜索武器
        weapon = self._fuzzy_search_weapon(weapon_name, 'mp')
        if not weapon:
            yield self.chain_reply(event, f"❌ 未找到武器：{weapon_name}")
            return
        
        # 映射部位
        part_map = {
            '头': 'head', '头部': 'head',
            '胸': 'chest', '胸部': 'chest',
            '腹': 'abdomen', '腹部': 'abdomen',
        }
        mapped_part = part_map.get(hit_part, hit_part)
        
        # 执行计算
        result = self.calculator.calculate_battlefield_damage(weapon, distance, mapped_part)
        
        if not result.get('success'):
            yield self.chain_reply(event, f"❌ 计算失败：{result.get('error', '未知错误')}")
            return
        
        # 格式化结果
        output_lines = [
            f"⚔️【战场伤害计算】",
            f"━━━━━━━━━━━━━━━━",
            f"🔫 武器: {weapon.get('name', '')}",
            f"📏 距离: {distance}米",
            f"🎯 部位: {result.get('hitPart', '')}",
            f"",
            f"📊 基础伤害: {result.get('baseDamage', 0)}",
            f"📉 距离衰减: ×{result.get('distanceMultiplier', 1)}",
            f"📈 部位倍率: ×{result.get('partMultiplier', 1)}",
            f"💥 最终伤害: {result.get('finalDamage', 0):.1f}",
            f"",
            f"💀 一击致命: {'是' if result.get('isKill') else '否'}"
        ]
        
        yield self.chain_reply(event, '\n'.join(output_lines))
    
    # ==================== 维修计算 ====================
    
    async def quick_repair(self, event: AstrMessageEvent, args: str):
        """
        快捷维修计算
        格式：修甲 装备名称 剩余耐久/当前上限 局内/局外
        示例：修甲 fs 0/100 局内
        """
        if not args:
            help_msg = """🔧【维修计算帮助】

📝 命令格式:
/三角洲 修甲 <装备名> <剩余/上限> <模式>

📋 参数说明:
• 装备名: 护甲名称(支持模糊搜索)
• 剩余/上限: 当前耐久/最大耐久
• 模式: 局内/局外

📌 示例:
• /三角洲 修甲 fs 0/100 局内
• /三角洲 修甲 泰坦 50/120 局外

💡 常用简写:
• fs = 飞鲨护甲
• dich = 帝骋护甲
• titan/tt = 泰坦护甲"""
            yield self.chain_reply(event, help_msg)
            return
        
        parts = args.strip().split()
        if len(parts) < 3:
            yield self.chain_reply(event, "❌ 参数不足\n格式：修甲 装备名 剩余/上限 局内/局外")
            return
        
        # 解析参数
        equip_name = parts[0]
        durability_str = parts[1]
        mode_str = parts[2] if len(parts) > 2 else "局外"
        
        # 解析耐久度
        if '/' not in durability_str and '／' not in durability_str:
            yield self.chain_reply(event, "❌ 耐久度格式错误\n正确格式：剩余/上限 (如 50/100)")
            return
        
        durability_str = durability_str.replace('／', '/')
        try:
            remaining, maximum = durability_str.split('/')
            remaining = float(remaining)
            maximum = float(maximum)
        except:
            yield self.chain_reply(event, "❌ 耐久度解析失败，请输入数字")
            return
        
        if remaining > maximum:
            yield self.chain_reply(event, "❌ 剩余耐久不能大于最大耐久")
            return
        
        if maximum <= 0:
            yield self.chain_reply(event, "❌ 最大耐久必须大于0")
            return
        
        # 搜索装备
        equipment = self._fuzzy_search_armor(equip_name)
        if not equipment:
            yield self.chain_reply(event, f"❌ 未找到装备：{equip_name}")
            return
        
        # 解析模式
        is_inside = mode_str in ['局内', 'inside', '内']
        
        # 执行计算
        if is_inside:
            result = self.calculator.calculate_inside_repair(
                equipment,
                {
                    'currentDurability': maximum,
                    'remainingDurability': remaining
                }
            )
        else:
            result = self.calculator.calculate_outside_repair(
                equipment,
                {
                    'repairLevel': 'intermediate',
                    'currentDurability': maximum,
                    'remainingDurability': remaining
                }
            )
        
        if not result.get('success'):
            yield self.chain_reply(event, f"❌ 计算失败：{result.get('error', '未知错误')}")
            return
        
        # 格式化结果
        output = self._format_repair_result(result, equipment, is_inside)
        yield self.chain_reply(event, output)
    
    def _format_repair_result(self, result: Dict, equipment: Dict, is_inside: bool) -> str:
        """格式化维修计算结果"""
        name = equipment.get('name', '未知')
        
        lines = [
            f"🔧【{name} 维修计算】",
            f"━━━━━━━━━━━━━━━━",
            f"📊 初始上限: {equipment.get('initialMax', '?')}",
            f"📊 当前上限: {result.get('currentMax', result.get('currentDurability', '?'))}",
            f"📊 剩余耐久: {result.get('remainingDurability', '?')}",
            ""
        ]
        
        if is_inside:
            lines.append("📦 【局内维修】")
            lines.append(f"🔄 维修后上限: {result.get('repairedMax', '?')}")
            lines.append("")
            
            # 维修包消耗
            packages = result.get('repairPackages', [])
            if packages:
                lines.append("📋 维修包消耗:")
                for pkg in packages:
                    consumption = pkg.get('consumption', '?')
                    if isinstance(consumption, (int, float)):
                        lines.append(f"  • {pkg['name']}: {consumption}点")
                    else:
                        lines.append(f"  • {pkg['name']}: {consumption}")
        else:
            lines.append("🏪 【局外维修】")
            lines.append(f"📈 维修等级: {result.get('repairLevel', '中级维修')}")
            lines.append(f"🔄 维修后上限: {result.get('finalUpper', '?')}")
            lines.append(f"💰 维修费用: {result.get('repairCost', '?')}")
            lines.append(f"📉 磨损程度: {result.get('wearPercentage', '?')}%")
            lines.append(f"🏷️ 市场状态: {result.get('marketStatus', '?')}")
        
        return '\n'.join(lines)
    
    # ==================== 战备计算 ====================
    
    async def readiness(self, event: AstrMessageEvent, args: str):
        """
        战备计算器
        格式：战备 目标战备值 [最高价格]
        """
        if not args:
            help_msg = """📦【战备计算帮助】

📝 命令格式:
/三角洲 战备 <目标值> [最高价格]

📋 参数说明:
• 目标值: 想要达到的战备值
• 最高价格: 可选，限制单件最高价格

📌 示例:
• /三角洲 战备 50000
• /三角洲 战备 100000 500000

💡 提示:
• 系统会自动计算最低成本配装
• 返回前3个最优方案"""
            yield self.chain_reply(event, help_msg)
            return
        
        parts = args.strip().split()
        
        try:
            target = int(parts[0])
        except:
            yield self.chain_reply(event, "❌ 目标战备值格式错误")
            return
        
        max_price = None
        if len(parts) > 1:
            try:
                max_price = int(parts[1])
            except:
                pass
        
        # 构建装备数据
        equipment = self._build_equipment_data()
        weapons = self._build_weapons_data()
        
        if not equipment or not weapons:
            yield self.chain_reply(event, "❌ 装备数据未加载，请稍后重试")
            return
        
        # 执行计算
        result = self.calculator.calculate_readiness(target, equipment, weapons, {'maxPrice': max_price})
        
        if not result.get('success'):
            yield self.chain_reply(event, f"❌ 计算失败：{result.get('error', '未知错误')}")
            return
        
        if not result.get('bestCombination'):
            yield self.chain_reply(event, f"❌ 未找到满足战备值 {target} 的配装方案")
            return
        
        # 格式化结果
        output = self._format_readiness_result(result, target)
        yield self.chain_reply(event, output)
    
    def _build_equipment_data(self) -> Dict:
        """构建装备数据"""
        equipment = {
            '头盔': [],
            '护甲': [],
            '胸挂': [],
            '背包': []
        }
        
        all_armors = self._get_all_armors()
        for armor in all_armors:
            if armor.get('is_helmet') or '头盔' in armor.get('name', ''):
                equipment['头盔'].append(armor)
            else:
                equipment['护甲'].append(armor)
        
        if 'equipment' in self.equipment_data:
            eq = self.equipment_data['equipment']
            if 'chest_rigs' in eq:
                equipment['胸挂'] = eq['chest_rigs']
            if 'backpacks' in eq:
                equipment['背包'] = eq['backpacks']
        
        return equipment
    
    def _build_weapons_data(self) -> Dict:
        """构建武器数据"""
        weapons = {}
        
        all_weapons = self._get_all_weapons('sol')
        for weapon in all_weapons:
            category = weapon.get('category', '其他')
            if category not in weapons:
                weapons[category] = []
            weapons[category].append(weapon)
        
        return weapons
    
    def _format_readiness_result(self, result: Dict, target: int) -> str:
        """格式化战备计算结果"""
        lines = [
            f"📦【战备计算结果】",
            f"━━━━━━━━━━━━━━━━",
            f"🎯 目标战备: {target}",
            f"📊 找到方案: {result.get('totalCombinations', 0)}种",
            ""
        ]
        
        top_combos = result.get('topCombinations', [])
        for i, combo in enumerate(top_combos[:3], 1):
            lines.append(f"🏆 方案{i}: 总成本 {combo['totalCost']:,}币 / 战备{combo['totalReadiness']}")
            
            equip = combo.get('equipment', {})
            if equip.get('weapon1', {}).get('name') != '无':
                lines.append(f"  🔫 主武器: {equip.get('weapon1', {}).get('name', '无')}")
            if equip.get('pistol', {}).get('name') != '无':
                lines.append(f"  🔫 手枪: {equip.get('pistol', {}).get('name', '无')}")
            if equip.get('helmet', {}).get('name') != '无':
                lines.append(f"  ⛑️ 头盔: {equip.get('helmet', {}).get('name', '无')}")
            if equip.get('armor', {}).get('name') != '无':
                lines.append(f"  🛡️ 护甲: {equip.get('armor', {}).get('name', '无')}")
            if equip.get('chest', {}).get('name') != '无':
                lines.append(f"  📦 胸挂: {equip.get('chest', {}).get('name', '无')}")
            if equip.get('backpack', {}).get('name') != '无':
                lines.append(f"  🎒 背包: {equip.get('backpack', {}).get('name', '无')}")
            lines.append("")
        
        return '\n'.join(lines)
    
    # ==================== 帮助命令 ====================
    
    async def calc_help(self, event: AstrMessageEvent, args: str):
        """显示计算器帮助"""
        help_msg = """🧮【三角洲计算器】

📋 可用命令:

💥 伤害计算:
• /三角洲 伤害 <模式> <武器> <子弹> <护甲> <距离> <次数> <部位>
• /三角洲 战场伤害 <武器> <距离> [部位]

🔧 维修计算:
• /三角洲 修甲 <装备名> <剩余/上限> <局内/局外>

📦 战备计算:
• /三角洲 战备 <目标值> [最高价格]

💡 使用各命令不带参数可查看详细帮助"""
        yield self.chain_reply(event, help_msg)
    
    async def mapping_table(self, event: AstrMessageEvent, args: str):
        """显示映射表"""
        msg = """📋【计算映射表】

🎮 游戏模式:
• 烽火地带: sol / 烽火 / 摸金
• 全面战场: mp / 全面 / 战场

🎯 命中部位:
1. 头部 (简写: 头)
2. 胸部 (简写: 胸)
3. 腹部 (简写: 腹)
4. 大臂
5. 小臂
6. 大腿
7. 小腿

🛡️ 护甲简写:
• fs = 飞鲨
• tt/titan = 泰坦
• dich = 帝骋
• gn = 钢能

📝 使用示例:
• 护甲组合: 2:5 或 dich:fs
• 部位分配: 1:2,2:4 或 头:2,胸:4"""
        yield self.chain_reply(event, msg)
