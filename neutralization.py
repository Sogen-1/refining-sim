"""
油脂精炼工艺模拟引擎 - 碱炼脱酸工段
Refining Process Simulation - Neutralization (Caustic Refining)

碱炼是化学精炼的核心工段，用NaOH中和毛油中的游离脂肪酸(FFA)，
同时进一步去除残留磷脂、色素和杂质。

计算依据:
    GB/T 5530 动植物油脂 酸值和酸度测定
    Bailey's Industrial Oil and Fat Products (7th Ed)
    Erickson, D.R. "Practical Handbook of Soybean Processing and Utilization"
    油脂精炼工艺学 (王兴国, 江南大学)
"""

from core import CrudeOil, ProcessConditions, OilType
from calibration import NEUTRALIZATION_CAL
from typing import Dict, Tuple


class NeutralizationSimulator:
    """
    碱炼脱酸工段模拟器

    根据脱胶油指标和碱炼工艺条件，计算:
    1. 理论碱量 + 超量碱
    2. 皂脚生成量
    3. 中性油损失(皂化+夹带)
    4. 碱炼油指标预测
    """

    # 化学常数
    KOH_MW = 56.1      # 氢氧化钾分子量
    NaOH_MW = 40.0     # 氢氧化钠分子量
    OLEIC_ACID_MW = 282.47  # 油酸分子量(代表性脂肪酸)

    def __init__(self, oil: CrudeOil, conditions: ProcessConditions):
        self.oil = oil
        self.cond = conditions
        self._results: Dict = {}

    # ==================================================================
    # 碱量计算
    # ==================================================================

    def calc_naoh_required(self) -> Dict:
        """
        计算氢氧化钠(烧碱)用量

        碱量分为两部分:
        1. 理论碱量: 中和FFA所需
        2. 超量碱: 补偿非均相反应的损失 + 中和残留磷酸

        理论碱量(kg/t油) = AV × 0.713
            (推导: 1g KOH中和1g油中FFA, NaOH/KOH = 40/56.1 = 0.713)

        对于脱胶后仍含磷酸的油:
            NaOH中和H3PO4: H3PO4 + 3NaOH -> Na3PO4 + 3H2O
            1kg P(100%)需要 3×40/31 = 3.87kg NaOH(100%)
        """
        oil_mass_ton = self.oil.mass_kg / 1000  # 转为吨

        # --- 理论碱量 ---
        # NaOH(kg/t油) = AV × 0.713
        theoretical_naoh_kg_per_ton = self.oil.acid_value * (self.NaOH_MW / self.KOH_MW)  # 0.713
        theoretical_total = theoretical_naoh_kg_per_ton * oil_mass_ton

        # --- 中和残留磷酸需要的碱 ---
        # 1kg P -> 3.87kg NaOH(100%)
        p_residual = self.oil.phosphorus_ppm  # ppm = mg/kg
        naoh_for_p = p_residual * 3.87 / 1000  # kg NaOH / 吨油
        naoh_for_p_total = naoh_for_p * oil_mass_ton

        # --- 超量碱 ---
        # 通常为油重的0.05%-0.25%
        excess_pct = self.cond.excess_lye_pct or 0.12
        excess_naoh_total = self.oil.mass_kg * excess_pct / 100

        # --- 总碱量 ---
        total_naoh_100 = theoretical_total + naoh_for_p_total + excess_naoh_total

        # 工业液碱转为32%或按用户指定的波美度
        lye_be = self.cond.lye_conc_be
        lye_conc_pct = self._be_to_pct(lye_be)
        lye_32_equivalent = total_naoh_100 / 0.32

        result = {
            "油重_吨": round(oil_mass_ton, 2),
            "酸价_AV": self.oil.acid_value,
            "理论碱量_kg_100pctNaOH": round(theoretical_total, 2),
            "中和磷酸耗碱_kg": round(naoh_for_p_total, 2),
            "超量碱_kg": round(excess_naoh_total, 2),
            "总碱量_kg_100pctNaOH": round(total_naoh_100, 2),
            "折合32%液碱_kg": round(lye_32_equivalent, 2),
            f"折合{lye_be}°Bé液碱_kg": round(total_naoh_100 / (lye_conc_pct / 100), 2),
            "超量碱%": round(excess_pct, 3),
            "碱液浓度_%": round(lye_conc_pct, 1),
        }

        # 评价超量碱是否合理
        if excess_pct < 0.03:
            result["碱量评价"] = "超量碱过低,可能导致中和不完全"
        elif excess_pct > 0.30:
            result["碱量评价"] = "超量碱过高,增加中性油皂化损失"
        else:
            result["碱量评价"] = "碱量在合理范围"

        self._results.update(result)
        return result

    @staticmethod
    def _be_to_pct(be: float) -> float:
        """波美度转质量百分比 (NaOH溶液)"""
        # 近似公式: % = 1.06 × °Bé + 0.5
        return 1.06 * be + 0.5

    # ==================================================================
    # 皂脚生成量
    # ==================================================================

    def calc_soapstock(self) -> Dict:
        """
        计算皂脚生成量

        皂脚组成:
        1. 脂肪酸钠皂 (FFA + NaOH → RCOONa + H2O)
           1kg FFA → 约1.08kg 钠皂
        2. 中性油(被皂化) - 超量碱越多,皂化越多
        3. 中性油(被夹带) - 分离不彻底
        4. 磷脂 + 胶质
        5. 水分
        6. 残留碱 + 盐

        经验公式: 皂脚量 = (1.5~2.5) × FFA量
        """
        oil_mass = self.oil.mass_kg
        ffa_pct = self.oil.ffa_pct  # 小数
        ffa_mass = oil_mass * ffa_pct

        # 钠皂生成量 (FFA→皂, 增重约8%)
        soap_mass = ffa_mass * 1.08

        # 中性油皂化损失: 使用校准系数
        excess_pct = self.cond.excess_lye_pct or 0.12
        cal = NEUTRALIZATION_CAL
        saponified_oil = oil_mass * excess_pct * cal["saponification_ratio"]

        # 中性油机械夹带: 使用校准系数
        entrained_oil = oil_mass * cal["entrainment_ratio"]

        # 磷脂残余(脱胶后残留的少量磷脂)
        residual_phospholipid = oil_mass * self.oil.phospholipid_pct / 100 * 0.05

        # 水分 + 盐 - 使用校准系数
        water_salt = soap_mass * cal["soap_water_ratio"]

        total_soapstock = (soap_mass + saponified_oil + entrained_oil +
                          residual_phospholipid + water_salt)

        total_loss_pct = total_soapstock / oil_mass * 100

        # 中性油总损失
        neutral_loss = saponified_oil + entrained_oil

        result = {
            "FFA含量_kg": round(ffa_mass, 2),
            "FFA%": round(ffa_pct * 100, 4),
            "钠皂生成量_kg": round(soap_mass, 2),
            "中性油皂化损失_kg": round(saponified_oil, 2),
            "中性油夹带损失_kg": round(entrained_oil, 2),
            "中性油总损失_kg": round(neutral_loss, 2),
            "总皂脚量_kg": round(total_soapstock, 2),
            "碱炼总油损%": round(total_loss_pct, 2),
            "碱炼后油重_kg": round(oil_mass - total_soapstock, 2),
        }

        # 评价
        if total_loss_pct > 3.5:
            result["皂脚评价"] = "油损偏高,检查超量碱和离心机参数"
        elif total_loss_pct < 0.8:
            result["皂脚评价"] = "油损偏低,可能碱炼不彻底"
        else:
            result["皂脚评价"] = "油损在合理范围"

        self._results.update(result)
        return result

    # ==================================================================
    # 碱炼油指标预测
    # ==================================================================

    def predict_refined_oil_quality(self) -> Dict:
        """
        预测碱炼油指标

        碱炼后的变化:
        - 酸价: 降至0.05-0.15 (取决于超量碱和洗涤)
        - 磷: 进一步降低90-95%
        - 色泽: 显著改善(皂吸附色素)
        - 过氧化值: 轻微降低(碱炼温度下部分过氧化物分解)
        """
        # 酸价预测
        excess = self.cond.excess_lye_pct or 0.12
        if excess < 0.05:
            predicted_av = 0.15 + 0.05  # 中和不充分
        elif excess > 0.20:
            predicted_av = 0.03  # 充分中和
        else:
            predicted_av = 0.06

        # 磷残留
        p_before = self.oil.phosphorus_ppm
        p_after = p_before * 0.08  # 碱炼去除92%残留磷

        # 色泽改善(红值降低50-70%)
        color_red = self.oil.color_red * 0.35

        result = {
            "碱炼后酸价_AV": round(predicted_av, 2),
            "碱炼后磷_ppm": round(p_after, 1),
            "碱炼后色泽_红": round(color_red, 1),
            "酸价降低率%": round((1 - predicted_av/self.oil.acid_value) * 100, 1),
            "磷脱除率%": round(92, 1),
        }

        self._results.update(result)
        return result

    # ==================================================================
    # 运行
    # ==================================================================

    def run(self) -> Dict:
        print(f"{'='*60}")
        print(f"  碱炼脱酸工段 - {self.oil.oil_type.cn_name}")
        print(f"  进油酸价: {self.oil.acid_value:.1f} | 含磷: {self.oil.phosphorus_ppm:.0f}ppm")
        print(f"{'='*60}")

        print("\n[1/3] 碱量计算...")
        naoh = self.calc_naoh_required()
        print(f"  总碱量(100%): {naoh['总碱量_kg_100pctNaOH']:.1f} kg")
        print(f"  {naoh['碱量评价']}")

        print("\n[2/3] 皂脚生成量...")
        soap = self.calc_soapstock()
        print(f"  皂脚总量: {soap['总皂脚量_kg']:.1f} kg")
        print(f"  {soap['皂脚评价']}")

        print("\n[3/3] 碱炼油指标预测...")
        quality = self.predict_refined_oil_quality()
        print(f"  碱炼后AV: {quality['碱炼后酸价_AV']:.2f}")
        print(f"  碱炼后P: {quality['碱炼后磷_ppm']:.1f} ppm")

        # 生成碱炼油
        refined_oil = CrudeOil(
            oil_type=self.oil.oil_type,
            batch_name=f"{self.oil.batch_name}_碱炼",
            mass_kg=soap["碱炼后油重_kg"],
            acid_value=quality["碱炼后酸价_AV"],
            phosphorus_ppm=quality["碱炼后磷_ppm"],
            nhp_ratio=0.05,  # 碱炼后NHP极少
            moisture_pct=0.05,
            impurities_pct=0.01,
            color_red=quality["碱炼后色泽_红"],
            color_yellow=self.oil.color_yellow * 0.40,
            peroxide_value=self.oil.peroxide_value * 0.85,
            tocopherol_ppm=self.oil.tocopherol_ppm * 0.95,
            sterol_ppm=self.oil.sterol_ppm * 0.92,
        )

        print(f"\n{'='*60}")
        print(f"  碱炼完成 | 进: {self.oil.mass_kg:.0f}kg → 出: {refined_oil.mass_kg:.0f}kg")
        print(f"  油损: {soap['碱炼总油损%']:.2f}% | AV: {quality['碱炼后酸价_AV']:.2f}")
        print(f"{'='*60}\n")

        return {
            "进油": self.oil,
            "碱炼油": refined_oil,
            "计算结果": dict(self._results),
        }


# ==================================================================
# 便捷函数
# ==================================================================

def quick_neutralize(oil_type_name: str, mass_ton: float = 100.0,
                     av: float = 4.0, p_ppm: float = 50.0,
                     excess_lye: float = 0.12) -> Dict:
    oil_map = {
        "大豆油": OilType.SOYBEAN, "菜籽油": OilType.RAPESEED,
        "花生油": OilType.PEANUT, "葵花籽油": OilType.SUNFLOWER,
        "玉米油": OilType.CORN, "棉籽油": OilType.COTTONSEED,
        "棕榈油": OilType.PALM, "米糠油": OilType.RICE_BRAN,
    }
    oil_type = oil_map.get(oil_type_name, OilType.SOYBEAN)
    oil = CrudeOil(
        oil_type=oil_type, batch_name=f"{oil_type_name}_毛油",
        mass_kg=mass_ton * 1000, acid_value=av, phosphorus_ppm=p_ppm,
    )
    cond = ProcessConditions(excess_lye_pct=excess_lye)
    sim = NeutralizationSimulator(oil, cond)
    return sim.run()
