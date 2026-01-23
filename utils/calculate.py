"""
计算工具类
提供伤害计算、战备计算、维修计算等核心算法
严格按照繁星攻略组 Python 代码的计算逻辑实现
"""
import math
from typing import Dict, List, Optional, Tuple, Any


class Calculate:
    """三角洲行动计算工具类"""
    
    def __init__(self):
        pass
    
    # ==================== 伤害计算 ====================
    
    def calculate_damage(
        self, 
        weapon: Dict, 
        armor_data: Optional[Dict], 
        bullet: Dict, 
        hit_data: Dict
    ) -> Dict:
        """
        夺金伤害计算 - 击杀模拟计算（从满血满甲到击杀）
        
        Args:
            weapon: 武器数据
            armor_data: 护甲数据（可包含armor和helmet）
            bullet: 子弹数据
            hit_data: 命中数据 {distance, hit_parts, fire_mode, trigger_delay}
        
        Returns:
            计算结果字典
        """
        try:
            distance = hit_data.get('distance', 0)
            hit_parts = hit_data.get('hit_parts', [])  # 命中部位数组
            
            if not weapon or not bullet:
                return {'success': False, 'error': '缺少武器或子弹数据'}
            
            # 初始状态
            player_health = 100.0
            current_armor_durability = 0
            current_helmet_durability = 0
            
            # 护甲参数
            armor_level = 0
            helmet_level = 0
            max_armor_durability = 0
            max_helmet_durability = 0
            armor_info = None
            helmet_info = None
            
            # 处理护甲数据
            if armor_data:
                if armor_data.get('armor') and armor_data.get('helmet'):
                    # 组合模式：头盔+护甲
                    armor_info = armor_data['armor']
                    helmet_info = armor_data['helmet']
                    armor_level = armor_info.get('protectionLevel', 0)
                    helmet_level = helmet_info.get('protectionLevel', 0)
                    current_armor_durability = armor_info.get('initialMax', 0)
                    current_helmet_durability = helmet_info.get('initialMax', 0)
                    max_armor_durability = armor_info.get('initialMax', 0)
                    max_helmet_durability = helmet_info.get('initialMax', 0)
                elif armor_data.get('armor'):
                    armor_info = armor_data['armor']
                    armor_level = armor_info.get('protectionLevel', 0)
                    current_armor_durability = armor_info.get('initialMax', 0)
                    max_armor_durability = armor_info.get('initialMax', 0)
                elif armor_data.get('helmet'):
                    helmet_info = armor_data['helmet']
                    helmet_level = helmet_info.get('protectionLevel', 0)
                    current_helmet_durability = helmet_info.get('initialMax', 0)
                    max_helmet_durability = helmet_info.get('initialMax', 0)
                elif armor_data.get('protectionLevel'):
                    # 兼容旧格式：单个护甲对象
                    name = armor_data.get('name', '')
                    if '头盔' in name or '帽' in name or '盔' in name:
                        helmet_info = armor_data
                        helmet_level = armor_data.get('protectionLevel', 0)
                        current_helmet_durability = armor_data.get('initialMax', 0)
                        max_helmet_durability = armor_data.get('initialMax', 0)
                    else:
                        armor_info = armor_data
                        armor_level = armor_data.get('protectionLevel', 0)
                        current_armor_durability = armor_data.get('initialMax', 0)
                        max_armor_durability = armor_data.get('initialMax', 0)
            
            # 计算武器距离衰减倍率
            weapon_decay_multiplier = self.calculate_weapon_decay(distance, weapon)
            
            # 获取子弹参数
            penetration_level = bullet.get('penetrationLevel', 0)
            base_damage_multiplier = bullet.get('baseDamageMultiplier', 1.0)
            base_armor_multiplier = bullet.get('baseArmorMultiplier', 1.0)
            armor_decay_factors = bullet.get('armorDecayFactors', [])
            
            # 武器基础参数
            weapon_damage = weapon.get('baseDamage', 0)
            weapon_armor_damage = weapon.get('armorDamage', 0)
            
            # 特殊处理：.338 Lap Mag弹药始终完全穿透护甲
            caliber = bullet.get('caliber', '')
            bullet_name = bullet.get('name', '')
            is_338_lap_mag = caliber == '338lapmag' or '.338 Lap Mag' in bullet_name
            
            # 部位倍率映射
            body_part_multipliers = {
                '头部': weapon.get('headMultiplier', 2.1),
                '胸部': weapon.get('chestMultiplier', 1.0),
                '腹部': weapon.get('abdomenMultiplier', 1.0),
                '下腹部': weapon.get('abdomenMultiplier', 1.0),
                '大臂': weapon.get('upperArmMultiplier', 1.0),
                '小臂': weapon.get('lowerArmMultiplier', 1.0),
                '大腿': weapon.get('thighMultiplier', 1.0),
                '小腿': weapon.get('calfMultiplier', 1.0),
            }
            
            # 根据护甲类型定义保护部位
            def get_armor_protected_areas(armor_type: str) -> List[str]:
                type_map = {
                    '半甲': ['胸部', '腹部'],
                    '全甲': ['胸部', '腹部', '下腹部'],
                    '重甲': ['胸部', '腹部', '下腹部', '大臂']
                }
                return type_map.get(armor_type, [])
            
            armor_protected_areas = get_armor_protected_areas(armor_info.get('type', '')) if armor_info else []
            helmet_protected_areas = ['头部']
            
            # 模拟结果
            shot_results = []
            total_damage = 0
            total_armor_damage = 0
            shot_count = 0
            
            # 逐发模拟直到击杀
            for i, hit_part in enumerate(hit_parts):
                if player_health <= 0:
                    break
                    
                shot_count += 1
                
                # 判断保护状态
                is_protected = False
                protector_level = 0
                is_helmet_protected = False
                is_armor_protected = False
                
                # 检查头盔保护
                if helmet_level > 0 and current_helmet_durability > 0 and hit_part in helmet_protected_areas:
                    is_helmet_protected = True
                    is_protected = True
                    protector_level = helmet_level
                
                # 检查护甲保护
                if armor_level > 0 and current_armor_durability > 0 and hit_part in armor_protected_areas:
                    is_armor_protected = True
                    if not is_protected:
                        is_protected = True
                        protector_level = armor_level
                
                # 确定保护器类型
                protector_type = None
                current_protector_durability = 0
                
                if is_helmet_protected:
                    protector_type = 'helmet'
                    current_protector_durability = current_helmet_durability
                elif is_armor_protected:
                    protector_type = 'armor'
                    current_protector_durability = current_armor_durability
                
                final_damage = 0
                armor_damage_value = 0
                protector_destroyed = False
                armor_damage_dealt = 0
                
                if is_protected:
                    # 计算穿透倍率
                    level_diff = penetration_level - protector_level
                    if level_diff < 0:
                        penetration_multiplier = 0.0
                    elif level_diff == 0:
                        penetration_multiplier = 0.5
                    elif level_diff == 1:
                        penetration_multiplier = 0.75
                    else:
                        penetration_multiplier = 1.0
                    
                    # 计算护甲伤害
                    armor_decay_multiplier = armor_decay_factors[protector_level - 1] if protector_level <= len(armor_decay_factors) else 0
                    armor_damage_value = weapon_armor_damage * base_armor_multiplier * armor_decay_multiplier * weapon_decay_multiplier
                    
                    # 计算剩余耐久
                    remaining_durability = max(0, current_protector_durability - armor_damage_value)
                    protector_destroyed = remaining_durability <= 0
                    armor_damage_dealt = current_protector_durability - remaining_durability
                    total_armor_damage += armor_damage_dealt
                    
                    # 更新耐久
                    if protector_type == 'helmet':
                        current_helmet_durability = remaining_durability
                    else:
                        current_armor_durability = remaining_durability
                    
                    # 计算伤害
                    part_multiplier = body_part_multipliers.get(hit_part, 1.0)
                    
                    if is_338_lap_mag:
                        # .338弹药完全穿透护甲
                        final_damage = weapon_damage * base_damage_multiplier * part_multiplier * weapon_decay_multiplier
                    else:
                        denominator = weapon_armor_damage * base_armor_multiplier * weapon_decay_multiplier * armor_decay_multiplier
                        
                        if denominator == 0:
                            final_damage = weapon_damage * base_damage_multiplier * part_multiplier * weapon_decay_multiplier
                        elif current_protector_durability >= armor_damage_value:
                            # 护甲未被击穿
                            final_damage = weapon_damage * base_damage_multiplier * part_multiplier * penetration_multiplier * weapon_decay_multiplier
                        else:
                            # 护甲被击穿的情况
                            ratio = current_protector_durability / denominator
                            part1 = ratio * weapon_damage * base_damage_multiplier * part_multiplier * penetration_multiplier * weapon_decay_multiplier
                            part2 = (1 - ratio) * weapon_damage * base_damage_multiplier * part_multiplier * weapon_decay_multiplier
                            final_damage = part1 + part2
                else:
                    # 未受保护
                    part_multiplier = body_part_multipliers.get(hit_part, 1.0)
                    final_damage = weapon_damage * base_damage_multiplier * part_multiplier * weapon_decay_multiplier
                
                # 四舍五入
                final_damage = round(final_damage * 100) / 100
                armor_damage_value = round(armor_damage_value * 100) / 100
                
                # 扣除生命值
                player_health -= final_damage
                total_damage += final_damage
                
                # 记录这发子弹的结果
                shot_results.append({
                    'shotNumber': shot_count,
                    'hitPart': hit_part,
                    'damage': final_damage,
                    'armorDamage': armor_damage_dealt,
                    'isProtected': is_protected,
                    'protectorDestroyed': protector_destroyed,
                    'protectorType': protector_type,
                    'playerHealthAfter': max(0, round(player_health * 100) / 100),
                    'armorDurabilityAfter': round(current_armor_durability * 10) / 10,
                    'helmetDurabilityAfter': round(current_helmet_durability * 10) / 10,
                    'isKill': player_health <= 0
                })
            
            return {
                'success': True,
                'weapon': weapon.get('name', ''),
                'armor': armor_info.get('name', '无') if armor_info else '无',
                'helmet': helmet_info.get('name', '无') if helmet_info else '无',
                'bullet': bullet.get('name', ''),
                'distance': distance,
                'baseDamage': weapon_damage,
                'weaponDecayMultiplier': round(weapon_decay_multiplier * 1000) / 1000,
                'penetrationLevel': penetration_level,
                'armorLevel': armor_level,
                'helmetLevel': helmet_level,
                'is338LapMag': is_338_lap_mag,
                'shotsToKill': shot_count,
                'totalDamage': round(total_damage * 100) / 100,
                'totalArmorDamage': round(total_armor_damage * 100) / 100,
                'shotResults': shot_results,
                'finalPlayerHealth': max(0, round(player_health * 100) / 100),
                'finalArmorDurability': round(current_armor_durability * 10) / 10,
                'finalHelmetDurability': round(current_helmet_durability * 10) / 10,
                'maxArmorDurability': max_armor_durability,
                'maxHelmetDurability': max_helmet_durability,
                'armorType': armor_info.get('type') if armor_info else None,
                'helmetType': helmet_info.get('type') if helmet_info else None,
                'isKilled': player_health <= 0
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def calculate_battlefield_damage(
        self, 
        weapon: Dict, 
        distance: float, 
        hit_part: str = 'chest'
    ) -> Dict:
        """
        战场伤害计算 - 无护甲影响的伤害计算
        """
        try:
            # 计算距离衰减
            distance_multiplier = self.calculate_weapon_decay(distance, weapon)
            
            # 获取部位倍率
            part_multiplier_map = {
                'head': weapon.get('headMultiplier', 2.1),
                'chest': weapon.get('chestMultiplier', 1.0),
                'abdomen': weapon.get('abdomenMultiplier', 1.0),
                'upper_arm': weapon.get('upperArmMultiplier', 1.0),
                'lower_arm': weapon.get('lowerArmMultiplier', 1.0),
                'thigh': weapon.get('thighMultiplier', 1.0),
                'calf': weapon.get('calfMultiplier', 1.0),
            }
            part_multiplier = part_multiplier_map.get(hit_part, 1.0)
            
            # 计算最终伤害
            base_damage = weapon.get('baseDamage', 0)
            final_damage = base_damage * distance_multiplier * part_multiplier
            
            return {
                'success': True,
                'weapon': weapon.get('name', ''),
                'distance': distance,
                'hitPart': hit_part,
                'baseDamage': base_damage,
                'distanceMultiplier': round(distance_multiplier * 1000) / 1000,
                'partMultiplier': part_multiplier,
                'finalDamage': round(final_damage * 100) / 100,
                'isKill': final_damage >= 100,
                'killThreshold': 100
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def calculate_weapon_decay(self, distance: float, weapon: Dict) -> float:
        """计算武器距离衰减倍率"""
        decay_distances = weapon.get('decayDistances', weapon.get('decay_distances', []))
        decay_multipliers = weapon.get('decayMultipliers', weapon.get('decay_factors', []))
        
        if not decay_distances:
            return 1.0
        
        # 确保衰减距离有序
        sorted_pairs = sorted(
            [(decay_distances[i], decay_multipliers[i] if i < len(decay_multipliers) else 1.0) 
             for i in range(len(decay_distances))],
            key=lambda x: x[0]
        )
        
        # 在第一个衰减距离前，无衰减
        if distance <= sorted_pairs[0][0]:
            return 1.0
        
        # 找到对应的衰减倍率
        for dist, mult in sorted_pairs:
            if distance <= dist:
                return mult
        
        # 超过所有衰减距离，使用最后一个衰减倍率
        return sorted_pairs[-1][1]
    
    # ==================== 维修计算 ====================
    
    def calculate_inside_repair(self, armor: Dict, repair_data: Dict) -> Dict:
        """
        局内维修计算 - 严格按照繁星攻略组Python代码实现
        """
        current_durability = repair_data.get('currentDurability', 0)
        remaining_durability = repair_data.get('remainingDurability', 0)
        
        if not armor or remaining_durability > current_durability:
            return {'success': False, 'error': '无效的维修参数'}
        
        initial_max = armor.get('initialMax', 100)
        repair_loss = armor.get('repairLoss', 0.1)
        
        # 计算比例
        ratio = 0
        if current_durability != 0:
            ratio = (current_durability - remaining_durability) / current_durability
        
        # 计算对数项
        log_term = 0
        if current_durability > 0 and initial_max > 0:
            log_term = math.log10(current_durability / initial_max)
        
        # 计算维修后上限
        repaired_max = current_durability - current_durability * ratio * (repair_loss - log_term)
        repaired_max_for_calc = round(repaired_max * 100) / 100
        
        # 计算耐久差
        delta = repaired_max_for_calc - remaining_durability
        
        # 计算所有四种维修包的消耗点数
        repair_packages = []
        package_types = [
            {'key': 'self_made', 'name': '自制维修包'},
            {'key': 'standard', 'name': '标准维修包'},
            {'key': 'precision', 'name': '精密维修包'},
            {'key': 'advanced', 'name': '高级维修组合'}
        ]
        
        for pkg_type in package_types:
            efficiency = self.get_inside_repair_efficiency(armor, pkg_type['key'])
            
            if efficiency is None:
                consumption = '暂无数据'
            elif efficiency == 0:
                consumption = '无穷大'
            elif delta <= 0:
                consumption = '无效值'
            else:
                points = delta / efficiency
                consumption = math.floor(points)
            
            repair_packages.append({
                'name': pkg_type['name'],
                'efficiency': efficiency,
                'consumption': consumption
            })
        
        return {
            'success': True,
            'mode': '局内维修',
            'armor': armor.get('name', ''),
            'currentMax': current_durability,
            'remainingDurability': remaining_durability,
            'repairedMax': round(repaired_max * 10) / 10,
            'repairLoss': repair_loss,
            'repairPackages': repair_packages
        }
    
    def calculate_outside_repair(self, armor: Dict, repair_data: Dict) -> Dict:
        """
        局外维修计算 - 严格按照繁星攻略组Python代码逻辑
        """
        repair_level = repair_data.get('repairLevel', 'intermediate')
        current_durability = repair_data.get('currentDurability', 0)
        remaining_durability = repair_data.get('remainingDurability', 0)
        
        if not armor or current_durability <= 0:
            return {'success': False, 'error': '无效的维修参数'}
        
        # 获取维修倍率
        repair_multiplier = 1.25 if repair_level == 'primary' else 1.0
        level_name = '初级维修' if repair_level == 'primary' else '中级维修'
        
        base_repair_loss = armor.get('repairLoss', 0.1)
        base_repair_price = armor.get('repairPrice', 50)
        
        adjusted_repair_loss = min(base_repair_loss * repair_multiplier, 1.0)
        adjusted_repair_price = base_repair_price * repair_multiplier
        
        initial_max = armor.get('initialMax', 100)
        
        # 处理当前上限（去尾法取整）
        current_upper_processed = math.floor(current_durability)
        remaining_durability_dec = remaining_durability if remaining_durability is not None else current_upper_processed
        
        # 维修可行性判定
        armor_type = armor.get('type', armor.get('category', ''))
        if armor_type and '头盔' in armor_type and current_upper_processed < 5:
            return {'success': False, 'error': f'当前头盔上限({current_upper_processed})小于5，不可维修'}
        if not ('头盔' in armor_type if armor_type else False) and current_upper_processed < 10:
            return {'success': False, 'error': f'当前护甲上限({current_upper_processed})小于10，不可维修'}
        
        try:
            # 计算公式
            term1 = (current_upper_processed - remaining_durability_dec) / current_upper_processed
            
            if current_upper_processed <= 0 or initial_max <= 0:
                raise ValueError("对数计算参数必须大于0")
            
            log_value = current_upper_processed / initial_max
            if log_value <= 0:
                raise ValueError("对数计算参数必须大于0")
            
            log_term = math.log10(log_value)
            term2 = adjusted_repair_loss - log_term
            
            repaired_upper = current_upper_processed - current_upper_processed * term1 * term2
            
            if math.isnan(repaired_upper) or math.isinf(repaired_upper):
                raise ValueError("计算结果无效")
            
            final_upper = max(1, math.floor(repaired_upper))
            
            # 计算维修花费
            remaining_int = math.floor(remaining_durability_dec)
            repair_cost = (final_upper - remaining_int + 1) * adjusted_repair_price
            
            if repair_cost < 0:
                repair_cost = 0
            else:
                repair_cost = round(repair_cost)
            
            # 计算磨损百分比
            wear_percentage = (1 - final_upper / initial_max) * 100
            
            # 市场出售判定
            non_tradable = [
                "金刚防弹衣", "特里克MAS2.0装甲", "泰坦防弹装甲",
                "DICH-9重型头盔", "GT5指挥官头盔", "H70夜视精英头盔"
            ]
            
            armor_name = armor.get('name', '')
            if armor_name in non_tradable:
                market_status = "不可在市场进行交易"
            else:
                threshold_85 = math.floor(initial_max * 0.85)
                threshold_70 = math.floor(initial_max * 0.70)
                
                if final_upper >= threshold_85:
                    market_status = "略有磨损，可在市场出售"
                elif final_upper >= threshold_70:
                    market_status = "久经沙场，可在市场出售"
                else:
                    market_status = "破损不堪，不可在市场出售"
            
            return {
                'success': True,
                'mode': '局外维修',
                'armor': armor_name,
                'repairLevel': level_name,
                'initialMax': initial_max,
                'currentDurability': current_upper_processed,
                'remainingDurability': remaining_durability_dec,
                'finalUpper': final_upper,
                'repairLoss': adjusted_repair_loss,
                'repairCost': repair_cost,
                'wearPercentage': round(wear_percentage * 10) / 10,
                'marketStatus': market_status
            }
            
        except Exception as e:
            return {'success': False, 'error': f'计算错误: {str(e)}'}
    
    def get_inside_repair_efficiency(self, armor: Dict, repair_type: str) -> Optional[float]:
        """获取局内维修包效率"""
        efficiencies = armor.get('repairEfficiencies', {})
        if not efficiencies:
            return None
        
        keys = list(efficiencies.keys())
        
        # 判断数据格式类型
        is_old_format = any(key in ['3', '6', '8', '9'] for key in keys)
        
        if is_old_format:
            # 旧格式：使用固定键名映射
            repair_type_to_key = {
                'self_made': '3',
                'standard': '6',
                'precision': '8',
                'advanced': '9'
            }
            key = repair_type_to_key.get(repair_type)
            if not key or key not in efficiencies:
                return None
            
            try:
                return float(efficiencies[key])
            except:
                return None
        else:
            # 新格式：键名本身就是效率值
            sorted_keys = sorted(keys, key=lambda x: float(x))
            
            repair_type_to_index = {
                'self_made': 0,
                'standard': 1,
                'precision': 2,
                'advanced': 3
            }
            
            index = repair_type_to_index.get(repair_type)
            if index is None or index >= len(sorted_keys):
                return None
            
            try:
                return float(sorted_keys[index])
            except:
                return None
    
    # ==================== 战备计算 ====================
    
    def calculate_readiness(
        self, 
        target_readiness: int, 
        equipment: Dict,
        weapons: Dict,
        options: Dict = None
    ) -> Dict:
        """
        战备计算器 - 计算最低成本卡战备配装
        """
        try:
            options = options or {}
            specified_chest = options.get('specifiedChest')
            specified_backpack = options.get('specifiedBackpack')
            
            # 生成所有可能的组合
            combinations = self.generate_equipment_combinations(
                target_readiness,
                equipment,
                weapons,
                specified_chest,
                specified_backpack
            )
            
            if not combinations:
                return {
                    'success': True,
                    'targetReadiness': target_readiness,
                    'bestCombination': None,
                    'topCombinations': [],
                    'totalCombinations': 0
                }
            
            # 按总成本升序排序，只保留前3个最优方案
            combinations.sort(key=lambda x: x['totalCost'])
            top3 = combinations[:3]
            
            return {
                'success': True,
                'targetReadiness': target_readiness,
                'bestCombination': top3[0],
                'topCombinations': top3,
                'totalCombinations': len(combinations)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_equipment_combinations(
        self,
        target_readiness: int,
        equipment: Dict,
        weapons: Dict,
        specified_chest: Optional[Dict] = None,
        specified_backpack: Optional[Dict] = None
    ) -> List[Dict]:
        """生成装备组合"""
        combinations = []
        none_option = {'name': '无', 'marketPrice': 0, 'readinessValue': 0}
        
        # 准备槽位数据
        slots = {
            'weapon1': [none_option],
            'pistol': [none_option],
            'helmet': [none_option],
            'armor': [none_option],
            'chest': [none_option],
            'backpack': [none_option]
        }
        
        # 填充武器槽
        for category, weapon_list in weapons.items():
            if category != '手枪':
                slots['weapon1'].extend(weapon_list)
        
        if '手枪' in weapons:
            slots['pistol'].extend(weapons['手枪'])
        
        # 填充装备槽
        if '头盔' in equipment:
            slots['helmet'].extend(equipment['头盔'])
        if '护甲' in equipment:
            slots['armor'].extend(equipment['护甲'])
        
        if specified_chest:
            slots['chest'] = [specified_chest]
        elif '胸挂' in equipment:
            slots['chest'].extend(equipment['胸挂'])
        
        if specified_backpack:
            slots['backpack'] = [specified_backpack]
        elif '背包' in equipment:
            slots['backpack'].extend(equipment['背包'])
        
        # 生成所有组合
        counter = 0
        for w1 in slots['weapon1']:
            for pistol in slots['pistol']:
                for helmet in slots['helmet']:
                    for armor in slots['armor']:
                        for chest in slots['chest']:
                            for backpack in slots['backpack']:
                                total_value = (
                                    w1.get('readinessValue', 0) +
                                    pistol.get('readinessValue', 0) +
                                    helmet.get('readinessValue', 0) +
                                    armor.get('readinessValue', 0) +
                                    chest.get('readinessValue', 0) +
                                    backpack.get('readinessValue', 0)
                                )
                                
                                if total_value >= target_readiness:
                                    total_cost = (
                                        w1.get('marketPrice', 0) +
                                        pistol.get('marketPrice', 0) +
                                        helmet.get('marketPrice', 0) +
                                        armor.get('marketPrice', 0) +
                                        chest.get('marketPrice', 0) +
                                        backpack.get('marketPrice', 0)
                                    )
                                    
                                    counter += 1
                                    combinations.append({
                                        'id': counter,
                                        'totalCost': total_cost,
                                        'totalReadiness': total_value,
                                        'equipment': {
                                            'weapon1': w1,
                                            'pistol': pistol,
                                            'helmet': helmet,
                                            'armor': armor,
                                            'chest': chest,
                                            'backpack': backpack
                                        }
                                    })
        
        return combinations
