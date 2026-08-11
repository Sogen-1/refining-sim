"""
油脂精炼工艺模拟引擎 - 脱胶工段
Refining Process Simulation - Degumming

脱胶是精炼第一道工序，去除毛油中的磷脂、蛋白质和黏液质。
根据脱胶深度的不同，可分为：
- 水化脱胶 (Water Degumming): 去除水化磷脂 HP
- 酸法脱胶 (Acid Degumming): 去除部分非水化磷脂 NHP
- 超级脱胶 (Super Degumming): 深度脱胶
- 酶法脱胶 (Enzymatic Degumming): 磷脂酶水解，脱除最彻底

计算依据:
    GB/T 8873 粮油名词术语 油脂工业
    Bailey's Industrial Oil and Fat Products (7th Ed)
    Dijkstra, A.J. "Enzymatic Degumming" - European Journal of Lipid Science & Technology
    油脂制取工艺学 (江南大学)
"""

from core import CrudeOil, ProcessConditions, OilType, CRUDE_OIL_TYPICAL
from calibration import DEGUMMING_CAL
from typing import Dict, Tuple


class DegummingSimulator:
    """
    脱胶工段模拟器

    根据毛油指标和工艺条件，计算:
    1. 磷酸/水/柠檬酸添加量
    2. 磷脂脱除效率
    3. 油损(胶质+中性油夹带)
    4. 脱胶油指标预测
    """

    # ---- 工艺常数 ----
    P_TO_PHOSPHOLIPID = 31.0       # 磷→磷脂换算系数
    PHOSPHORIC_ACID_MW = 98.0      # H3PO4 分子量
    # 理论上1份P需要约3.2份85%磷酸，实际操作取3.5-4.5

    def __init__(self, oil: CrudeOil, conditions: ProcessConditions):
        self.oil = oil
        self.cond = conditions
        self._results: Dict = {}

    # ==================================================================
    # 药品用量计算
    # ==================================================================

    def calc_phosphoric_acid(self) -> Tuple[float, str]:
        """
        计算磷酸添加量

        磷酸的作用:
        1. 将非水化磷脂(NHP)的Ca/Mg盐转化为游离态
        2. 螯合金属离子(Fe, Cu)
        3. 降低界面张力，促进胶质凝聚

        添加量: 通常为油重的 0.05%-0.20%
        高磷毛油(米糠油/棉籽油)需要更多
        """
        oil_mass = self.oil.mass_kg
        nhp_p = self.oil.nhp_phosphorus  # ppm

        # 理论需要量: 每1ppm NHP-P 需要约 0.001% 磷酸
        # 实际经验公式
        base_pct = 0.05  # 基础添加量 0.05%
        nhp_factor = nhp_p * 0.0003  # NHP贡献
        recommended_pct = base_pct + nhp_factor

        # 夹在上下限之间
        recommended_pct = max(0.03, min(0.25, recommended_pct))

        # 如果用户没设置，用推荐值
        actual_pct = self.cond.phosphoric_acid_pct or recommended_pct
        acid_85_mass = oil_mass * actual_pct / 100
        acid_100_mass = acid_85_mass * self.cond.acid_conc_pct / 100

        self._results["磷酸添加量%"] = round(actual_pct, 3)
        self._results["磷酸(85%)用量_kg"] = round(acid_85_mass, 2)
        self._results["磷酸(100%)用量_kg"] = round(acid_100_mass, 2)
        self._results["磷酸推荐添加量%"] = round(recommended_pct, 3)

        # 判断磷酸用量是否合理
        if actual_pct < recommended_pct * 0.7:
            return acid_100_mass, "⚠️ 磷酸用量偏低，可能导致NHP脱除不彻底"
        elif actual_pct > recommended_pct * 1.5:
            return acid_100_mass, "⚠️ 磷酸用量偏高，增加油损且残留磷可能影响后续脱色"
        return acid_100_mass, "✅ 磷酸用量合理"

    def calc_water_addition(self) -> float:
        """
        计算水化加水量

        加水量取决于:
        1. 磷脂含量: 磷脂吸水膨胀，需要足够水
        2. 油温: 温度越高，磷脂吸水能力下降，需水略多
        3. 操作方式: 连续式比间歇式用水更精准

        经验值: 通常为油重的 1%-4%
        磷脂含量每增加0.1%，加水量增加约0.5%
        """
        phospholipid_pct = self.oil.phospholipid_pct

        # 基础加水量 = 磷脂含量 × 水化系数
        base_water = phospholipid_pct * 8  # 每1份磷脂需要约8份水

        # 温度修正
        temp_factor = 1.0 + (self.cond.temperature_c - 65) * 0.005

        adjusted_water = base_water * temp_factor

        # 实际范围限制
        recommended = max(1.0, min(4.0, adjusted_water))

        actual = self.cond.water_addition_pct or recommended
        water_mass = self.oil.mass_kg * actual / 100

        self._results["水化加水量%"] = round(actual, 2)
        self._results["加水量_kg"] = round(water_mass, 2)
        self._results["推荐加水量%"] = round(recommended, 2)

        return water_mass

    # ==================================================================
    # 磷脂脱除效率
    # ==================================================================

    def calc_phosphorus_removal(self) -> Dict:
        """
        计算磷脂脱除效率和脱胶油磷含量

        关键原理:
        - 水化脱胶只能去除水化磷脂(HP)，效率约90-98%
        - 酸法脱胶可将部分NHP转化为HP再去除
        - 酶法脱胶(PLA/PLC)可达<5ppm残留磷

        计算公式:
        P_residual = P_nhp_remaining + P_hp_unremoved
        """
        initial_p = self.oil.phosphorus_ppm
        hp_p = self.oil.hp_phosphorus
        nhp_p = self.oil.nhp_phosphorus

        degum_type = self.cond.degumming_type

        # 不同脱胶方式的效率参数 (已乘校准系数)
        cal = DEGUMMING_CAL
        efficiency_map = {
            "water":      {"hp_removal": 0.92 * cal["hp_removal_factor"], "nhp_removal": 0.05 * cal["nhp_removal_factor"]},
            "acid":       {"hp_removal": 0.96 * cal["hp_removal_factor"], "nhp_removal": 0.70 * cal["nhp_removal_factor"]},
            "super":      {"hp_removal": 0.98 * cal["hp_removal_factor"], "nhp_removal": 0.90 * cal["nhp_removal_factor"]},
            "enzymatic":  {"hp_removal": 0.99 * cal["hp_removal_factor"], "nhp_removal": 0.97 * cal["nhp_removal_factor"]},
        }

        eff = efficiency_map.get(degum_type, efficiency_map["water"])

        # 酸法脱胶时，磷酸用量影响NHP脱除效率
        if degum_type == "acid":
            pa_pct = self.cond.phosphoric_acid_pct or 0.10
            # 磷酸越多，NHP去除越多(但边际效益递减)
            nhp_boost = min(0.15, (pa_pct - 0.05) * 1.5)
            eff["nhp_removal"] = min(0.95, eff["nhp_removal"] + nhp_boost)

        hp_remaining = hp_p * (1 - eff["hp_removal"])
        nhp_remaining = nhp_p * (1 - eff["nhp_removal"])
        residual_p = hp_remaining + nhp_remaining

        # 脱除的磷脂质量
        removed_p_mg_kg = initial_p - residual_p
        removed_phospholipid_kg = removed_p_mg_kg / 10000 * self.P_TO_PHOSPHOLIPID / 100 * self.oil.mass_kg

        result = {
            "脱胶方式": degum_type,
            "初始磷含量_ppm": round(initial_p, 1),
            "HP脱除率": round(eff["hp_removal"] * 100, 1),
            "NHP脱除率": round(eff["nhp_removal"] * 100, 1),
            "残留磷_ppm": round(residual_p, 1),
            "脱除磷脂质量_kg": round(removed_phospholipid_kg, 2),
            "脱胶油磷含量_ppm": round(residual_p, 1),
        }

        # 评价
        if residual_p <= 5:
            result["质量评价"] = "✅ 物理精炼级 (<5ppm)"
        elif residual_p <= 10:
            result["质量评价"] = "✅ 超级脱胶级 (<10ppm)"
        elif residual_p <= 30:
            result["质量评价"] = "✅ 化学精炼可接受 (<30ppm)"
        elif residual_p <= 50:
            result["质量评价"] = "⚠️ 边界值，建议加强脱胶"
        else:
            result["质量评价"] = "❌ 磷含量过高，需改善脱胶工艺"

        self._results.update(result)
        return result

    # ==================================================================
    # 油损计算
    # ==================================================================

    def calc_oil_loss(self) -> Dict:
        """
        计算脱胶工段的油损

        油损由两部分组成:
        1. 胶质(磷脂+黏液质) - 这是正常损耗
        2. 中性油夹带 - 胶质沉淀时包裹的中性油

        水化脱胶油损: 0.5%-1.0%
        酸法脱胶油损: 0.8%-1.8%
        酶法脱胶油损: 0.3%-0.8%
        """
        # 胶质本身质量
        phospholipid_mass = self.oil.phospholipid_pct / 100 * self.oil.mass_kg

        # 胶质吸水膨胀 - 使用校准系数
        water_in_gum = phospholipid_mass * DEGUMMING_CAL["gum_water_ratio"]

        # 中性油夹带 - 使用校准后的系数
        degum_type = self.cond.degumming_type
        entrainment_ratios = {
            "water": 0.50, "acid": 0.70, "super": 0.85, "enzymatic": 0.35
        }
        base_ratio = entrainment_ratios.get(degum_type, 0.60)
        entrainment_ratio = base_ratio * DEGUMMING_CAL["neutral_oil_entrainment"]
        neutral_oil_loss = phospholipid_mass * entrainment_ratio

        # 总油损
        total_gum_mass = phospholipid_mass + water_in_gum + neutral_oil_loss
        total_loss_pct = total_gum_mass / self.oil.mass_kg * 100

        result = {
            "磷脂胶质质量_kg": round(phospholipid_mass, 2),
            "胶脚含水量_kg": round(water_in_gum, 2),
            "中性油夹带_kg": round(neutral_oil_loss, 2),
            "脱胶总油损_kg": round(total_gum_mass, 2),
            "脱胶总油损%": round(total_loss_pct, 2),
            "脱胶后油重_kg": round(self.oil.mass_kg - total_gum_mass, 2),
        }

        # 评价
        if degum_type == "enzymatic" and total_loss_pct > 0.8:
            result["油损评价"] = "⚠️ 酶法脱胶油损偏高，检查离心机操作参数"
        elif degum_type in ("acid", "super") and total_loss_pct > 2.0:
            result["油损评价"] = "⚠️ 油损偏高，建议降低磷酸用量或优化分离温度"
        elif total_loss_pct < 0.3:
            result["油损评价"] = "⚠️ 油损异常偏低，可能脱胶不彻底"
        else:
            result["油损评价"] = "✅ 油损在合理范围内"

        self._results.update(result)
        return result

    # ==================================================================
    # 运行全流程
    # ==================================================================

    def run(self) -> Dict:
        """执行脱胶工段完整计算"""
        print(f"{'='*60}")
        print(f"  脱胶工段模拟 - {self.oil.oil_type.cn_name} - {self.cond.degumming_type}")
        print(f"{'='*60}")

        # 1. 药品计算
        print("\n[1/4] 磷酸用量计算...")
        pa_mass, pa_msg = self.calc_phosphoric_acid()
        print(f"  {pa_msg}")

        print("\n[2/4] 水化加水量计算...")
        water_mass = self.calc_water_addition()
        print(f"  推荐加水量: {self._results.get('推荐加水量%', 'N/A')}%")

        # 2. 磷脱除预测
        print("\n[3/4] 磷脂脱除效率预测...")
        p_result = self.calc_phosphorus_removal()
        print(f"  残留磷: {p_result['残留磷_ppm']} ppm → {p_result['质量评价']}")

        # 3. 油损
        print("\n[4/4] 油损计算...")
        loss_result = self.calc_oil_loss()
        print(f"  脱胶油损: {loss_result['脱胶总油损%']}% → {loss_result['油损评价']}")

        # 4. 生成脱胶油对象
        degummed_oil = CrudeOil(
            oil_type=self.oil.oil_type,
            batch_name=f"{self.oil.batch_name}_脱胶",
            mass_kg=loss_result["脱胶后油重_kg"],
            acid_value=self.oil.acid_value * 0.98,  # 磷酸中和微量FFA
            phosphorus_ppm=p_result["残留磷_ppm"],
            nhp_ratio=self.oil.nhp_ratio * 0.2 if self.cond.degumming_type in ("super", "enzymatic") else self.oil.nhp_ratio,
            moisture_pct=self.oil.moisture_pct * 0.5,  # 干燥后水分降低
            impurities_pct=self.oil.impurities_pct * 0.1,
            color_red=self.oil.color_red * 0.85,  # 磷/蛋白去除后色泽改善
            color_yellow=self.oil.color_yellow * 0.85,
            peroxide_value=self.oil.peroxide_value,
            tocopherol_ppm=self.oil.tocopherol_ppm * 0.98,  # 微量损失
            sterol_ppm=self.oil.sterol_ppm * 0.98,
        )

        # 5. 汇总
        print(f"\n{'='*60}")
        print(f"  脱胶完成 | 进: {self.oil.mass_kg:.0f}kg → 出: {degummed_oil.mass_kg:.0f}kg")
        print(f"  油损: {loss_result['脱胶总油损%']}% | 残留磷: {p_result['残留磷_ppm']}ppm")
        print(f"{'='*60}\n")

        return {
            "毛油": self.oil,
            "脱胶油": degummed_oil,
            "计算结果": dict(self._results),
            "磷酸计算信息": pa_msg,
        }


# ==================================================================
# 便捷函数
# ==================================================================

def quick_degum(oil_type_name: str, mass_ton: float = 100.0,
                av: float = None, p_ppm: float = None,
                degum_type: str = "acid") -> Dict:
    """
    快速脱胶计算

    用法:
        result = quick_degum("大豆油", mass_ton=100, av=2.0, p_ppm=800)
        print(result["脱胶油"].phosphorus_ppm)  # 残留磷
    """
    # 解析油种
    oil_map = {
        "大豆油": OilType.SOYBEAN, "豆油": OilType.SOYBEAN,
        "菜籽油": OilType.RAPESEED, "菜油": OilType.RAPESEED,
        "花生油": OilType.PEANUT,
        "葵花籽油": OilType.SUNFLOWER,
        "玉米油": OilType.CORN,
        "棉籽油": OilType.COTTONSEED,
        "棕榈油": OilType.PALM,
        "米糠油": OilType.RICE_BRAN,
        "芝麻油": OilType.SESAME,
    }
    oil_type = oil_map.get(oil_type_name, OilType.SOYBEAN)

    # 用典型值
    typical = CRUDE_OIL_TYPICAL.get(oil_type, {"AV": 2.0, "P": 200, "NHP": 0.10})
    if av is None: av = typical["AV"]
    if p_ppm is None: p_ppm = typical["P"]

    oil = CrudeOil(
        oil_type=oil_type,
        batch_name=oil_type_name,
        mass_kg=mass_ton * 1000,
        acid_value=av,
        phosphorus_ppm=p_ppm,
        nhp_ratio=typical["NHP"],
    )
    cond = ProcessConditions(degumming_type=degum_type)
    sim = DegummingSimulator(oil, cond)
    return sim.run()
