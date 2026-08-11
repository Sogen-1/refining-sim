"""
油脂精炼工艺模拟引擎 - 脱蜡工段
Refining Process Simulation - Winterization (Dewaxing)

脱蜡用于去除葵花籽油、玉米油、米糠油等含蜡油脂中的蜡质，
防止成品油在低温下产生浑浊。

工艺原理: 将油缓慢冷却至5-8°C，蜡质结晶析出，再通过过滤分离。
"""

from core import CrudeOil, ProcessConditions, OilType
from typing import Dict
import math


class WinterizationSimulator:
    """
    脱蜡工段模拟器

    适用油种: 葵花籽油(蜡含量300-800ppm)、玉米油(200-500ppm)、
              米糠油(400-1200ppm)、棉籽油(少量蜡)
    """

    # 各油种典型蜡含量 (ppm)
    TYPICAL_WAX = {
        OilType.SUNFLOWER: 500, OilType.CORN: 350,
        OilType.RICE_BRAN: 800, OilType.COTTONSEED: 100,
        OilType.SOYBEAN: 20, OilType.RAPESEED: 30,
        OilType.PEANUT: 15, OilType.PALM: 0, OilType.SESAME: 50,
    }

    # 蜡在油中的溶解度曲线 (简化为温度线性关系)
    # 溶解度 ≈ A * exp(B/T) 简化为分段线性

    def __init__(self, oil: CrudeOil, conditions: ProcessConditions):
        self.oil = oil
        self.cond = conditions
        self._results: Dict = {}

    def get_wax_content(self) -> float:
        """获取油中蜡含量 (ppm)，优先用实测值"""
        if self.oil.wax_content_ppm > 0:
            return self.oil.wax_content_ppm
        return self.TYPICAL_WAX.get(self.oil.oil_type, 50)

    def calc_crystallization(self) -> Dict:
        """计算结晶条件与蜡脱除率"""
        wax_initial = self.get_wax_content()
        temp = getattr(self.cond, 'winterization_temp_c', None) or 6.0
        time_h = getattr(self.cond, 'winterization_time_h', None) or 8.0
        cooling_rate = getattr(self.cond, 'cooling_rate_c_per_h', None) or 2.0

        # 蜡结晶效率模型
        # 温度越低、时间越长、降温越慢(晶核生长充分)，脱除率越高
        temp_factor = max(0.3, (15 - temp) / 15)  # 15°C为参考温度
        time_factor = min(1.0, time_h / 8.0)
        cooling_factor = max(0.5, 2.0 / cooling_rate)

        removal_efficiency = temp_factor * time_factor * cooling_factor * 0.92
        removal_efficiency = min(0.98, max(0.30, removal_efficiency))

        wax_residual = wax_initial * (1 - removal_efficiency)

        # 结晶罐数量估算 (基于停留时间)
        oil_flow = self.oil.mass_kg / (time_h * 1000)  # t/h
        crystallizer_volume = oil_flow * time_h * 1.2 / 0.92  # m3 (0.92 = 油密度)
        num_crystallizers = max(1, math.ceil(crystallizer_volume / 25))

        result = {
            "蜡含量初值_ppm": round(wax_initial, 0),
            "结晶温度_°C": temp,
            "结晶时间_h": time_h,
            "降温速率_°C每h": cooling_rate,
            "蜡脱除率_%": round(removal_efficiency * 100, 1),
            "残留蜡_ppm": round(wax_residual, 1),
            "冷试验_5h_0°C": "合格 (澄清透明)" if wax_residual < 20 else (
                "边缘 (轻微浑浊)" if wax_residual < 50 else "不合格 (明显浑浊)"
            ),
            "建议结晶罐数": num_crystallizers,
        }

        if wax_initial < 30:
            result["脱蜡评价"] = "蜡含量低，无需单独脱蜡"
        elif removal_efficiency < 0.5:
            result["脱蜡评价"] = "脱蜡效率偏低，建议降低结晶温度或延长结晶时间"
        else:
            result["脱蜡评价"] = "脱蜡条件合理"

        self._results.update(result)
        return result

    def calc_wax_filter_loss(self) -> Dict:
        """计算脱蜡过滤油损"""
        wax_initial = self.get_wax_content()
        removal = float(str(self._results.get("蜡脱除率_%", 80)).replace("%", "")) / 100
        wax_removed = wax_initial * removal

        # 蜡饼含油率 (蜡晶体中夹带的中性油，约为蜡质量的50-100%)
        oil_in_wax_cake = wax_removed * 0.7 * self.oil.mass_kg / 1_000_000

        # 助滤剂(硅藻土)用量
        filter_aid_pct = max(0, (wax_initial - 100) * 0.0005)  # 高蜡油需助滤剂
        filter_aid_kg = self.oil.mass_kg * filter_aid_pct / 100

        # 过滤总损失
        total_loss = oil_in_wax_cake + filter_aid_kg * 0.3
        total_loss_pct = total_loss / self.oil.mass_kg * 100

        result = {
            "脱除蜡质量_kg": round(wax_removed * self.oil.mass_kg / 1_000_000, 2),
            "蜡饼夹带油_kg": round(oil_in_wax_cake, 2),
            "助滤剂用量_kg": round(filter_aid_kg, 1),
            "总油损_kg": round(total_loss, 2),
            "总油损_%": round(total_loss_pct, 2),
        }

        self._results.update(result)
        return result

    def run(self) -> Dict:
        wax = self.get_wax_content()
        print(f"{'='*60}")
        print(f"  脱蜡工段 - {self.oil.oil_type.cn_name} (蜡含量: {wax:.0f}ppm)")
        print(f"{'='*60}")

        if wax < 30:
            print("\n  ⓘ 蜡含量低, 无需脱蜡, 跳过\n")
            return {"进油": self.oil, "脱蜡油": self.oil, "计算结果": {"脱蜡评价": "跳过 - 蜡含量<30ppm"}}

        print("\n[1/2] 结晶条件与蜡脱除率...")
        cryst = self.calc_crystallization()
        print(f"  脱除率: {cryst['蜡脱除率_%']:.1f}% | 残留: {cryst['残留蜡_ppm']:.0f}ppm")

        print("\n[2/2] 过滤油损...")
        loss = self.calc_wax_filter_loss()
        print(f"  油损: {loss['总油损_%']:.2f}%")

        # 生成脱蜡油
        dewaxed = CrudeOil(
            oil_type=self.oil.oil_type,
            batch_name=f"{self.oil.batch_name}_脱蜡",
            mass_kg=self.oil.mass_kg - loss["总油损_kg"],
            acid_value=self.oil.acid_value,
            phosphorus_ppm=self.oil.phosphorus_ppm,
            color_red=self.oil.color_red * 0.95,
            color_yellow=self.oil.color_yellow * 0.95,
            peroxide_value=self.oil.peroxide_value,
            tocopherol_ppm=self.oil.tocopherol_ppm * 0.99,
            sterol_ppm=self.oil.sterol_ppm * 0.99,
            wax_content_ppm=cryst["残留蜡_ppm"],
        )

        return {"进油": self.oil, "脱蜡油": dewaxed, "计算结果": dict(self._results)}
