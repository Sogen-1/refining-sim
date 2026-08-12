"""
油脂精炼工艺模拟引擎 - 脱臭工段
Refining Process Simulation - Deodorization

脱臭是精炼最后一道关键工段，利用高温高真空条件下的蒸汽汽提原理:
- 脱除游离脂肪酸(FFA降至<0.05%)
- 脱除气味物质(醛、酮、烃)
- 热脱色(类胡萝卜素高温分解)
- 脱除残留农药和轻质多环芳烃

副作用(必须控制):
- 反式脂肪酸(TFA)生成
- 生育酚(VE)和甾醇的蒸馏损失
- 缩水甘油酯(GEs)和3-氯丙醇酯(3-MCPDE)生成
- 能量消耗巨大(占精炼总能耗50%以上)

计算依据:
    GB/T 22500 动植物油脂 聚乙烯类聚合物的测定
    De Greyt, W. "Deodorization" - Bailey's (7th Ed)
    Zulkurnain, M. "Optimization of palm oil deodorization"
    Pudel, F. "Mitigation of 3-MCPD and glycidyl esters during refining"
"""

from core import CrudeOil, ProcessConditions, OilType
from calibration import DEODORIZATION_CAL
from typing import Dict, Tuple
import math


class DeodorizationSimulator:
    """
    脱臭工段模拟器

    输入: 脱色油
    输出: 成品精炼油 + 能耗分析 + 有害物预测
    """

    # 各油种脱臭温度推荐 (°C)
    TYPICAL_TEMP = {
        OilType.SOYBEAN:    235,
        OilType.RAPESEED:   230,
        OilType.PEANUT:     220,
        OilType.SUNFLOWER:  225,
        OilType.CORN:       235,
        OilType.COTTONSEED: 235,
        OilType.PALM:       255,
        OilType.RICE_BRAN:  240,
    }

    def __init__(self, oil: CrudeOil, conditions: ProcessConditions):
        self.oil = oil
        self.cond = conditions
        self._results: Dict = {}

    # ==================================================================
    # FFA 脱除模型
    # ==================================================================

    def calc_ffa_stripping(self) -> Dict:
        """
        计算汽提脱酸效果

        FFA汽提遵循一级动力学:
            ln(FFA_initial / FFA_final) = k × (S/O) × (P_vap / P_total)

        其中:
            S/O = 汽提蒸汽量/油量
            P_vap = FFA在操作温度下的蒸汽压
            P_total = 系统绝对压力
            k = 传质系数

        实际经验: 在245°C, 2 mbar, 1.5%汽提蒸汽下,
        FFA可降至0.03-0.05% (以油酸计), 相当于AV 0.06-0.10
        """
        temp = self.TYPICAL_TEMP.get(self.oil.oil_type, 235)
        if self.cond.deodorization_temp_c != 245: temp = self.cond.deodorization_temp_c
        vacuum = self.cond.deodorization_vacuum_mbar or 2.0
        steam_pct = self.cond.stripping_steam_pct or 1.5
        residence = self.cond.deodorization_time_min or 90

        # FFA蒸气压估算 (Antoine式近似)
        # 油酸在245°C时蒸气压约 0.5-1.0 mbar
        ffa_vapor_pressure = 10 ** (8.5 - 2500 / (temp + 230))  # 近似, mbar

        # 汽提效率
        stripping_factor = (steam_pct / 100) * (ffa_vapor_pressure / vacuum) * 50
        stripping_factor *= (residence / 60)  # 时间修正

        # FFA降低倍数
        ffa_initial_pct = self.oil.ffa_pct * 100  # 转为%
        reduction_ratio = math.exp(-stripping_factor * 0.5)

        ffa_final_pct = max(0.01, ffa_initial_pct * reduction_ratio)
        av_final = ffa_final_pct / 0.503  # FFA% → AV

        result = {
            "进油AV": round(self.oil.acid_value, 2),
            "进油FFA%": round(ffa_initial_pct, 3),
            "脱臭温度_C": temp,
            "系统真空_mbar": vacuum,
            "汽提蒸汽量%": round(steam_pct, 2),
            "脱臭时间_min": residence,
            "FFA蒸汽压估算_mbar": round(ffa_vapor_pressure, 3),
            "脱臭后AV": round(av_final, 2),
            "脱臭后FFA%": round(ffa_final_pct, 3),
            "FFA脱除率%": round((1 - ffa_final_pct / ffa_initial_pct) * 100, 1),
        }

        if av_final <= 0.08:
            result["FFA评价"] = "一级油标准 (AV<=0.08)"
        elif av_final <= 0.20:
            result["FFA评价"] = "合格 (AV<=0.20)"
        else:
            result["FFA评价"] = "酸价偏高，需提高温度或增加汽提蒸汽"

        self._results.update(result)
        return result

    # ==================================================================
    # 蒸汽消耗
    # ==================================================================

    def calc_steam_consumption(self) -> Dict:
        """
        计算脱臭工段蒸汽消耗

        分为:
        1. 汽提蒸汽: 直接注入油中用于汽提
        2. 喷射蒸汽: 真空系统用(大气喷射泵/蒸汽喷射泵)
        3. 加热蒸汽: 油升温所需(通过导热油间接加热)

        汽提蒸汽量: 油重的 0.5%-2.0%
        喷射蒸汽量: 约为汽提蒸汽的 3-6倍
        加热蒸汽量: 取决于油温升和热回收效率
        """
        oil_mass = self.oil.mass_kg
        steam_pct = self.cond.stripping_steam_pct or 1.5

        # 汽提蒸汽
        stripping_steam = oil_mass * steam_pct / 100

        # 真空喷射蒸汽 (四级蒸汽喷射泵)
        # 约 3-6 kg steam / kg stripping steam
        ejector_ratio = DEODORIZATION_CAL["ejector_ratio"]
        ejector_steam = stripping_steam * ejector_ratio

        # 加热蒸汽 (间接)
        # 油从脱色温度(~105°C)升至脱臭温度(~245°C), ΔT≈140°C
        temp_in = 105
        temp_out = self.cond.deodorization_temp_c or 245
        delta_t = temp_out - temp_in
        cp_oil = 2.1  # kJ/(kg·K) 油脂比热
        heat_needed = oil_mass * cp_oil * delta_t  # kJ

        # 假定热回收率 70% (现代脱臭塔标配)
        heat_recovery = DEODORIZATION_CAL["heat_recovery"]
        heat_after_recovery = heat_needed * (1 - heat_recovery)

        # 1吨蒸汽(1MPa饱和)提供约2000 MJ = 2,000,000 kJ 潜热
        # 但实际上导热油间接加热
        heating_steam = heat_after_recovery / 2000000 * 1000  # kg

        total_steam = stripping_steam + ejector_steam + heating_steam
        steam_per_ton_oil = total_steam / (oil_mass / 1000)

        result = {
            "汽提蒸汽_kg": round(stripping_steam, 1),
            "喷射真空蒸汽_kg": round(ejector_steam, 1),
            "间接加热蒸汽_kg": round(heating_steam, 1),
            "总蒸汽消耗_kg": round(total_steam, 1),
            "吨油耗汽_kg蒸汽每吨油": round(steam_per_ton_oil, 1),
            "热回收率%": round(heat_recovery * 100, 0),
        }

        # 业界标杆: 吨油耗汽 < 80 kg
        if steam_per_ton_oil < 60:
            result["蒸汽评价"] = "优秀 (低于60 kg/t, 接近国际标杆)"
        elif steam_per_ton_oil < 100:
            result["蒸汽评价"] = "良好"
        elif steam_per_ton_oil < 150:
            result["蒸汽评价"] = "一般, 建议检查热回收系统"
        else:
            result["蒸汽评价"] = "偏高, 需优化真空系统或热回收"

        self._results.update(result)
        return result

    # ==================================================================
    # TFA / 有害物预测
    # ==================================================================

    def predict_contaminants(self) -> Dict:
        """
        预测脱臭过程中生成的有害物

        1. 反式脂肪酸 (TFA):
           - 温度依赖性: >240°C时呈指数增长
           - 亚麻酸(C18:3)最容易异构化 → 其次亚油酸(C18:2)
           - 经验: 245°C/2h → TFA增加 1-3%
           - 现代低温脱臭(220-230°C)可将TFA控制在 <0.5%

        2. 缩水甘油酯 (GEs):
           - 前体: DAG(甘油二酯)在>230°C时环化
           - 真空度越好,生成量越低

        3. 3-氯丙醇酯 (3-MCPDE):
           - 前体: 氯离子 + 酰基甘油在高温下反应
           - 脱臭前充分水洗除氯是主要控制手段
        """
        temp = self.TYPICAL_TEMP.get(self.oil.oil_type, 235)
        if self.cond.deodorization_temp_c != 245: temp = self.cond.deodorization_temp_c
        residence = self.cond.deodorization_time_min or 90

        # TFA 估算 (大豆油/菜籽油) - 基于实际脱臭温度
        # 经验公式: TFA_formation(%) ≈ k0 * exp(Ea/RT) * t
        # 简化为温度阈值模型
        if temp < 220:
            tfa_increase_pct = 0.1
        elif temp < 235:
            tfa_increase_pct = 0.1 + (temp - 220) * 0.02
        elif temp < 250:
            tfa_increase_pct = 0.4 + (temp - 235) * 0.06
        else:
            tfa_increase_pct = 1.3 + (temp - 250) * 0.12

        tfa_increase_pct *= (residence / 60)  # 时间线性关系

        # GE 估算
        ge_risk = "低" if temp < 230 else ("中" if temp < 245 else "高")

        # 3-MCPDE 估算
        mcpd_risk = "低" if self.oil.phosphorus_ppm < 3 else "中"

        result = {
            "脱臭温度_C": temp,
            "脱臭时间_min": residence,
            "TFA_预估增加_%": round(tfa_increase_pct, 2),
            "TFA_预估总量_ppm": round(tfa_increase_pct * 10000, 0),
            "GE风险等级": ge_risk,
            "3-MCPDE风险等级": mcpd_risk,
        }

        # 评价
        if tfa_increase_pct < 0.3:
            result["TFA评价"] = "优秀 (增量<0.3%, 稳定达到'零反式'标准)"
        elif tfa_increase_pct < 1.0:
            result["TFA评价"] = "可接受 (增量<1.0%)"
        else:
            result["TFA评价"] = "TFA增量偏高, 建议降低脱臭温度或缩短时间"

        self._results.update(result)
        return result

    # ==================================================================
    # VE/甾醇损失
    # ==================================================================

    def predict_nutrient_loss(self) -> Dict:
        """
        预测脱臭过程中营养成分的损失

        生育酚(VE):
        - 蒸馏损失: 汽提蒸汽会带走部分VE
        - 热降解: 高温下VE氧化分解
        - 典型损失: 10-35% (取决于温度和时间)

        植物甾醇:
        - 甾醇沸点高, 蒸馏损失相对较少
        - 但与FFA形成的甾醇酯可被汽提带走
        - 典型损失: 5-15%
        - 脱臭馏出物(DD油)是VE和甾醇的主要来源
        """
        temp = self.cond.deodorization_temp_c or 245
        residence = self.cond.deodorization_time_min or 90
        steam_pct = self.cond.stripping_steam_pct or 1.5

        # VE 损失模型
        ve_loss_base = 0.12  # 基础损失(230°C, 1.5%蒸汽)
        ve_temp_factor = (temp - 220) / 30 * 0.15  # 温度每增30°C, VE损失增15%
        ve_steam_factor = (steam_pct - 1.0) * 0.05  # 蒸汽越多, VE损失越多
        ve_time_factor = (residence - 60) / 60 * 0.05  # 额外时间的损失

        ve_loss_pct = min(0.45, ve_loss_base + ve_temp_factor + ve_steam_factor + ve_time_factor)

        # 甾醇损失
        sterol_loss_base = 0.06
        sterol_temp_factor = (temp - 220) / 30 * 0.04
        sterol_loss_pct = min(0.20, sterol_loss_base + sterol_temp_factor)

        ve_before = self.oil.tocopherol_ppm
        ve_after = ve_before * (1 - ve_loss_pct)
        sterol_before = self.oil.sterol_ppm
        sterol_after = sterol_before * (1 - sterol_loss_pct)

        # DD油(脱臭馏出物)中VE和甾醇量
        dd_oil_ve = ve_before * ve_loss_pct * self.oil.mass_kg / 1000000
        dd_oil_sterol = sterol_before * sterol_loss_pct * self.oil.mass_kg / 1000000

        result = {
            "VE_损失率%": round(ve_loss_pct * 100, 1),
            "VE_脱臭前_ppm": round(ve_before, 0),
            "VE_脱臭后_ppm": round(ve_after, 0),
            "甾醇_损失率%": round(sterol_loss_pct * 100, 1),
            "甾醇_脱臭前_ppm": round(sterol_before, 0),
            "甾醇_脱臭后_ppm": round(sterol_after, 0),
            "DD油中VE_kg": round(dd_oil_ve, 3),
            "DD油中甾醇_kg": round(dd_oil_sterol, 2),
        }

        if ve_loss_pct < 0.15:
            result["营养评价"] = "优秀 (VE保留率>85%, 低温脱臭优势明显)"
        elif ve_loss_pct < 0.25:
            result["营养评价"] = "良好"
        else:
            result["营养评价"] = "VE损失偏高, 考虑降低脱臭温度"

        self._results.update(result)
        return result

    # ==================================================================
    # 运行
    # ==================================================================

    def run(self) -> Dict:
        temp = self.TYPICAL_TEMP.get(self.oil.oil_type, 235)
        if self.cond.deodorization_temp_c != 245: temp = self.cond.deodorization_temp_c
        print(f"{'='*60}")
        print(f"  脱臭工段 - {self.oil.oil_type.cn_name} @ {temp}°C")
        print(f"  进油: AV={self.oil.acid_value:.2f} | "
              f"VE={self.oil.tocopherol_ppm:.0f}ppm | "
              f"甾醇={self.oil.sterol_ppm:.0f}ppm")
        print(f"{'='*60}")

        print("\n[1/4] FFA汽提脱除...")
        ffa = self.calc_ffa_stripping()
        print(f"  脱臭后AV: {ffa['脱臭后AV']:.2f} → {ffa['FFA评价']}")

        print("\n[2/4] 蒸汽消耗计算...")
        steam = self.calc_steam_consumption()
        print(f"  吨油耗汽: {steam['吨油耗汽_kg蒸汽每吨油']:.0f} kg/t → {steam['蒸汽评价']}")

        print("\n[3/4] TFA/有害物预测...")
        cont = self.predict_contaminants()
        print(f"  TFA增量: {cont['TFA_预估增加_%']:.2f}% | GE: {cont['GE风险等级']} | 3-MCPDE: {cont['3-MCPDE风险等级']}")

        print("\n[4/4] 营养损失预测...")
        nut = self.predict_nutrient_loss()
        ve_retain = (1 - nut['VE_损失率%']/100) * 100
        st_retain = (1 - nut['甾醇_损失率%']/100) * 100
        print(f"  VE保留: {ve_retain:.0f}% | 甾醇保留: {st_retain:.0f}% → {nut['营养评价']}")

        # 生成成品油
        oil_loss = self.oil.mass_kg * 0.003  # 脱臭油损约0.3%
        refined_oil = CrudeOil(
            oil_type=self.oil.oil_type,
            batch_name=f"{self.oil.batch_name}_成品油",
            mass_kg=self.oil.mass_kg - oil_loss,
            acid_value=ffa["脱臭后AV"],
            phosphorus_ppm=1.0,
            nhp_ratio=0.01,
            moisture_pct=0.01,
            impurities_pct=0.001,
            color_red=self.oil.color_red * 0.6,
            color_yellow=self.oil.color_yellow * 0.60,
            peroxide_value=0.5,
            tocopherol_ppm=nut["VE_脱臭后_ppm"],
            sterol_ppm=nut["甾醇_脱臭后_ppm"],
        )

        print(f"\n{'='*60}")
        print(f"  脱臭完成 | 成品AV: {ffa['脱臭后AV']:.2f} | "
              f"吨耗汽: {steam['吨油耗汽_kg蒸汽每吨油']:.0f} kg")
        print(f"{'='*60}\n")

        return {"进油": self.oil, "成品油": refined_oil, "计算结果": dict(self._results)}
