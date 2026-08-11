"""
精炼引擎 — 统一的精炼流程执行器
消除 app.py 和 pareto.py 中的重复代码
"""

from core import CrudeOil, ProcessConditions, OilType
from degumming import DegummingSimulator
from neutralization import NeutralizationSimulator
from bleaching import BleachingSimulator
from deodorization import DeodorizationSimulator
from winterization import WinterizationSimulator


def run_refining(oil: CrudeOil, pa_pct: float = 0.10, excess_lye: float = 0.12,
                 degum_type: str = "acid", route: str = "chemical",
                 include_wax: bool = False, deodorization_temp: float = None,
                 earth_pct: float = None, silent: bool = False) -> dict:
    """
    执行一次完整的精炼流程，返回结构化结果。

    参数:
        oil: 毛油对象
        pa_pct: 磷酸添加量 (%)
        excess_lye: 超量碱 (%)
        degum_type: 脱胶方式 (water/acid/super/enzymatic)
        route: 精炼路线 (chemical/physical)
        include_wax: 是否脱蜡
        deodorization_temp: 脱臭温度 (°C)，None则用默认值
        earth_pct: 白土添加量 (%)，None则用默认值
        silent: True时抑制模块内print输出

    返回:
        {
            "stages": [{"name": "脱胶", "results": {...}}, ...],
            "final_oil": CrudeOil成品油,
            "yield_pct": 精炼得率,
            "total_loss_kg": 总油损kg,
        }
    """
    stages = []
    current_oil = oil

    # 1. 脱胶
    cond1 = ProcessConditions(degumming_type=degum_type, phosphoric_acid_pct=pa_pct)
    r1 = DegummingSimulator(current_oil, cond1).run()
    current_oil = r1['脱胶油']
    stages.append({"name": "脱胶", "results": r1['计算结果']})

    # 2. 碱炼 (化学精炼) 或跳过 (物理精炼)
    if route == 'chemical':
        cond2 = ProcessConditions(excess_lye_pct=excess_lye)
        r2 = NeutralizationSimulator(current_oil, cond2).run()
        current_oil = r2['碱炼油']
        stages.append({"name": "碱炼脱酸", "results": r2['计算结果']})

    # 3. 脱色
    cond3 = ProcessConditions()
    if earth_pct is not None:
        cond3.bleaching_earth_pct = earth_pct
    r3 = BleachingSimulator(current_oil, cond3).run()
    current_oil = r3['脱色油']
    stages.append({"name": "脱色", "results": r3['计算结果']})

    # 3.5 脱蜡 (可选)
    if include_wax:
        r_w = WinterizationSimulator(current_oil, ProcessConditions()).run()
        current_oil = r_w.get('脱蜡油', current_oil)
        stages.append({"name": "脱蜡", "results": r_w.get('计算结果', {})})

    # 4. 脱臭
    cond4 = ProcessConditions()
    if deodorization_temp is not None:
        cond4.deodorization_temp_c = deodorization_temp
    r4 = DeodorizationSimulator(current_oil, cond4).run()
    current_oil = r4['成品油']
    stages.append({"name": "脱臭", "results": r4['计算结果']})

    total_loss = oil.mass_kg - current_oil.mass_kg
    yield_pct = current_oil.mass_kg / oil.mass_kg * 100

    return {
        "stages": stages,
        "final_oil": current_oil,
        "yield_pct": yield_pct,
        "total_loss_kg": total_loss,
    }
