"""
油脂精炼工艺模拟引擎 - 脱色工段
Refining Process Simulation - Bleaching

脱色是精炼第三道工序，利用活性白土/活性炭的吸附作用去除:
- 色素(叶绿素、类胡萝卜素)
- 残留皂(碱炼后残留的微量皂)
- 残留磷脂
- 过氧化物和次级氧化产物
- 微量金属(Fe, Cu)

计算依据:
    GB/T 5535 动植物油脂 不皂化物测定
    Bailey's Industrial Oil and Fat Products (7th Ed)
    Sarier, N. "Optimization of Bleaching Earth Activity"
    Zschau, W. "Bleaching of Edible Fats and Oils"
"""

from core import CrudeOil, ProcessConditions, OilType
from calibration import BLEACHING_CAL
from typing import Dict, Tuple
import math


class BleachingSimulator:
    """
    脱色工段模拟器

    输入: 碱炼油(或脱胶后直接脱色的物理精炼油)
    输出: 脱色油指标 + 白土用量 + 废白土量

    关键工艺参数:
    - 白土添加量: 0.5%-3.0% (取决于油种和色泽要求)
    - 活性炭: 0.1%-0.5% (通常与白土混用，增强脱色+除臭)
    - 温度: 90-120°C
    - 真空度: 2-10 kPa
    - 接触时间: 20-40 min
    """

    # 各油种推荐白土用量 (%)
    TYPICAL_EARTH_DOSAGE = {
        OilType.SOYBEAN:    1.2,   # 大豆油
        OilType.RAPESEED:   1.5,   # 菜籽油(含叶绿素，需更多白土)
        OilType.PEANUT:     1.0,   # 花生油(颜色浅)
        OilType.SUNFLOWER:  1.8,   # 葵花籽油
        OilType.CORN:       1.5,   # 玉米油
        OilType.COTTONSEED: 2.5,   # 棉籽油(棉酚色素难脱)
        OilType.PALM:       1.0,   # 棕榈油
        OilType.RICE_BRAN:  2.0,   # 米糠油(色泽深)
    }

    # 白土吸油率 (每1kg白土夹带的中性油, kg)
    OIL_RETENTION_PER_KG_EARTH = BLEACHING_CAL["oil_retention"]

    def __init__(self, oil: CrudeOil, conditions: ProcessConditions):
        self.oil = oil
        self.cond = conditions
        self._results: Dict = {}

    # ==================================================================
    # 白土用量优化
    # ==================================================================

    def calc_earth_dosage(self) -> Dict:
        """
        计算最优白土用量

        白土用量的影响因素:
        1. 目标色泽: 越浅需要越多白土
        2. 进油色泽: 进油颜色越深,需要越多
        3. 油种特性: 叶绿素含量高的油(菜籽油)需要更多
        4. 残皂/残磷: 皂和磷会占据白土活性位点,增加用量

        采用 Freundlich 吸附等温式:
            q = K * C^(1/n)
        其中 q = 色素吸附量, C = 平衡色素浓度
        """
        oil_type = self.oil.oil_type
        base_dosage = self.TYPICAL_EARTH_DOSAGE.get(oil_type, 1.5)

        # 色泽修正: 红值越高,需要越多白土
        color_factor = (self.oil.color_red / 5.0) ** 0.5  # 红值5.0为基准

        # 残磷修正: 残磷>5ppm,每增加5ppm,白土增加10%
        if self.oil.phosphorus_ppm > 5:
            p_factor = 1.0 + (self.oil.phosphorus_ppm - 5) * 0.02
        else:
            p_factor = 1.0

        # 残皂修正(碱炼后): AV>0.1表示有残皂
        if self.oil.acid_value > 0.1:
            soap_factor = 1.0 + (self.oil.acid_value - 0.1) * 2.0
        else:
            soap_factor = 1.0

        # 综合推荐
        recommended = base_dosage * color_factor * p_factor * soap_factor
        recommended = round(max(0.3, min(4.0, recommended)), 1)

        # 活性炭(辅助脱色+除臭,通常为白土量的10-20%)
        carbon_pct = 0
        if oil_type in (OilType.RAPESEED, OilType.RICE_BRAN, OilType.COTTONSEED):
            carbon_pct = recommended * 0.15  # 含叶绿素高的油种建议加活性炭

        actual = self.cond.bleaching_earth_pct or recommended
        actual_carbon = self.cond.activated_carbon_pct or carbon_pct

        earth_mass = self.oil.mass_kg * actual / 100
        carbon_mass = self.oil.mass_kg * actual_carbon / 100

        result = {
            "推荐白土用量%": recommended,
            "实际白土用量%": round(actual, 1),
            "白土加入量_kg": round(earth_mass, 1),
            "活性炭用量%": round(actual_carbon, 2),
            "活性炭加入量_kg": round(carbon_mass, 1),
            "色泽修正系数": round(color_factor, 2),
            "残磷修正系数": round(p_factor, 2),
        }

        if actual < recommended * 0.7:
            result["白土评价"] = "白土用量偏低,可能脱色不达标"
        elif actual > recommended * 1.5:
            result["白土评价"] = "白土用量偏高,油损增加,建议检查前道工艺"
        else:
            result["白土评价"] = "白土用量合理"

        self._results.update(result)
        return result

    # ==================================================================
    # 色泽预测
    # ==================================================================

    def predict_color_reduction(self) -> Dict:
        """
        预测脱色后色泽

        采用经验模型:
        - 白土对红色素的吸附效率高于黄色素
        - 红值通常降低 70-85%
        - 黄值降低 50-70%
        - 叶绿素(菜籽油/橄榄油)脱除率 60-90%
        """
        earth_pct = self._results.get("实际白土用量%", 1.5)

        # 脱色效率与白土量的关系(非线性,边际递减)
        # 使用 Langmuir 型饱和曲线
        def reduction_factor(dosage, max_reduction):
            k = 0.8  # 吸附系数
            return max_reduction * (1 - math.exp(-k * dosage / 1.0))

        red_before = self.oil.color_red
        yellow_before = self.oil.color_yellow

        red_max = 0.88   # 红值最大脱除率
        yellow_max = 0.70  # 黄值最大脱除率

        red_removal = reduction_factor(earth_pct, red_max)
        yellow_removal = reduction_factor(earth_pct, yellow_max)

        red_after = red_before * (1 - red_removal)
        yellow_after = yellow_before * (1 - yellow_removal)

        result = {
            "进油色泽_红": round(red_before, 1),
            "进油色泽_黄": round(yellow_before, 1),
            "出油色泽_红": round(red_after, 1),
            "出油色泽_黄": round(yellow_after, 1),
            "红值脱除率%": round(red_removal * 100, 1),
            "黄值脱除率%": round(yellow_removal * 100, 1),
        }

        # 色泽评价
        if red_after <= 1.0:
            result["色泽评价"] = "一等油色泽"
        elif red_after <= 2.0:
            result["色泽评价"] = "合格食用油色泽"
        elif red_after <= 3.5:
            result["色泽评价"] = "可接受(深色油)"
        else:
            result["色泽评价"] = "色泽偏深,建议增加白土或检查脱色条件"

        self._results.update(result)
        return result

    # ==================================================================
    # 油损与废白土
    # ==================================================================

    def calc_bleaching_loss(self) -> Dict:
        """
        计算脱色工段油损

        油损组成:
        1. 废白土夹带油: 每kg白土夹带0.30-0.40kg油
        2. 过滤损失: 滤饼/滤布残留
        3. 挥发损失: 高温真空下微量FFA/水分挥发
        """
        earth_mass = self._results.get("白土加入量_kg", 0)
        carbon_mass = self._results.get("活性炭加入量_kg", 0)
        total_adsorbent = earth_mass + carbon_mass

        # 废白土夹带油
        oil_in_spent_earth = total_adsorbent * self.OIL_RETENTION_PER_KG_EARTH

        # 过滤+挥发损失(约0.1-0.2%)
        filter_volatile_loss = self.oil.mass_kg * 0.0015

        total_loss = oil_in_spent_earth + filter_volatile_loss
        total_loss_pct = total_loss / self.oil.mass_kg * 100

        # 废白土总量(湿基,含油)
        spent_earth_total = total_adsorbent + oil_in_spent_earth

        result = {
            "白土+活性炭总量_kg": round(total_adsorbent, 1),
            "废白土夹带油_kg": round(oil_in_spent_earth, 1),
            "过滤挥发损失_kg": round(filter_volatile_loss, 1),
            "脱色总油损_kg": round(total_loss, 2),
            "脱色总油损%": round(total_loss_pct, 2),
            "废白土总量_湿基_kg": round(spent_earth_total, 1),
            "脱色后油重_kg": round(self.oil.mass_kg - total_loss, 2),
        }

        if total_loss_pct > 2.5:
            result["油损评价"] = "油损偏高,考虑降低白土用量或优化过滤"
        else:
            result["油损评价"] = "油损在合理范围"

        self._results.update(result)
        return result

    # ==================================================================
    # 运行
    # ==================================================================

    def run(self) -> Dict:
        print(f"{'='*60}")
        print(f"  脱色工段 - {self.oil.oil_type.cn_name}")
        print(f"  进油色泽: R{self.oil.color_red:.1f}/Y{self.oil.color_yellow:.1f} | "
              f"残磷: {self.oil.phosphorus_ppm:.1f}ppm")
        print(f"{'='*60}")

        print("\n[1/3] 白土用量优化...")
        earth = self.calc_earth_dosage()
        print(f"  推荐白土: {earth['推荐白土用量%']}% → {earth['白土评价']}")

        print("\n[2/3] 色泽预测...")
        color = self.predict_color_reduction()
        print(f"  脱色后: R{color['出油色泽_红']:.1f}/Y{color['出油色泽_黄']:.1f} → {color['色泽评价']}")

        print("\n[3/3] 油损与废白土...")
        loss = self.calc_bleaching_loss()
        print(f"  脱色油损: {loss['脱色总油损%']:.2f}% | 废白土: {loss['废白土总量_湿基_kg']:.0f}kg")

        # 生成脱色油
        bleached_oil = CrudeOil(
            oil_type=self.oil.oil_type,
            batch_name=f"{self.oil.batch_name}_脱色",
            mass_kg=loss["脱色后油重_kg"],
            acid_value=self.oil.acid_value * 0.85,  # 白土吸附部分FFA
            phosphorus_ppm=self.oil.phosphorus_ppm * 0.4,  # 残留磷降低60%
            nhp_ratio=self.oil.nhp_ratio * 0.5,
            moisture_pct=0.03,
            impurities_pct=0.005,
            color_red=color["出油色泽_红"],
            color_yellow=color["出油色泽_黄"],
            peroxide_value=self.oil.peroxide_value * 0.3,  # 过氧化物显著降低
            tocopherol_ppm=self.oil.tocopherol_ppm * 0.95,  # 微量损失
            sterol_ppm=self.oil.sterol_ppm * 0.95,
        )

        print(f"\n{'='*60}")
        print(f"  脱色完成 | 油损: {loss['脱色总油损%']:.2f}% | "
              f"色泽: R{color['出油色泽_红']:.1f}/Y{color['出油色泽_黄']:.1f}")
        print(f"{'='*60}\n")

        return {"进油": self.oil, "脱色油": bleached_oil, "计算结果": dict(self._results)}
