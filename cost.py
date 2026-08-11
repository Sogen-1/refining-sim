"""
油脂精炼工艺模拟引擎 - 成本估算模块
"""

from core import UTILITY_COST, OilType
from typing import Dict


# 各油种参考油价 (2026年 一级油出厂价 元/吨)
OIL_PRICE_REF = {
    OilType.SOYBEAN: 8500, OilType.RAPESEED: 10500, OilType.PEANUT: 18000,
    OilType.SUNFLOWER: 12000, OilType.CORN: 11000, OilType.COTTONSEED: 9000,
    OilType.PALM: 7500, OilType.RICE_BRAN: 9500,
}

# 副产品参考价 (元/吨)
BYPRODUCT_PRICE = {
    "磷脂胶": 800, "皂脚": 1500, "废白土": 0, "脱臭馏出物(DD油)": 5000,
    "蜡": 6000,
}


def estimate_cost(oil_type: OilType, mass_ton: float, stages: list, stages_data: dict) -> Dict:
    """估算全流程加工成本和收益"""
    oil_price = OIL_PRICE_REF.get(oil_type, 9000)

    # ── 原辅料成本 ──
    costs = {}

    # 磷酸
    degum = stages_data.get("脱胶", {}).get("results", {})
    pa_kg = float(str(degum.get("磷酸(85%)用量_kg", 0)).replace("kg", "").strip() or 0)
    costs["磷酸"] = pa_kg * UTILITY_COST["磷酸(85%)"] / 1000

    # 液碱
    neut = stages_data.get("碱炼脱酸", {}).get("results", {})
    naoh_kg = float(str(neut.get("折合32%液碱_kg", 0)).replace("kg", "").strip() or 0)
    costs["液碱(32%)"] = naoh_kg * UTILITY_COST["液碱(32%)"] / 1000

    # 白土
    bleach = stages_data.get("脱色", {}).get("results", {})
    earth_kg = float(str(bleach.get("白土加入量_kg", 0)).replace("kg", "").strip() or 0)
    carbon_kg = float(str(bleach.get("活性炭加入量_kg", 0)).replace("kg", "").strip() or 0)
    costs["活性白土"] = earth_kg * UTILITY_COST["活性白土"] / 1000
    costs["活性炭"] = carbon_kg * 8000 / 1000  # 活性炭约8000元/吨

    # 蒸汽
    deod = stages_data.get("脱臭", {}).get("results", {})
    steam_kg = float(str(deod.get("总蒸汽消耗_kg", 0)).replace("kg", "").strip() or 0)
    costs["蒸汽"] = steam_kg * UTILITY_COST["蒸汽(1MPa)"] / 1000

    # 电 (估算 15 kWh/t油)
    costs["电"] = mass_ton * 15 * UTILITY_COST["电"]

    # 水
    water_ton = float(str(degum.get("加水量_kg", mass_ton * 30)).replace("kg", "").strip() or mass_ton * 30) / 1000
    costs["工艺水"] = water_ton * UTILITY_COST["工艺水"]

    total_cost = sum(costs.values())
    cost_per_ton = total_cost / mass_ton

    # ── 副产品收入 ──
    revenues = {}
    gum_kg = float(str(degum.get("脱胶总油损_kg", 0)).replace("kg", "").strip() or 0)
    soap_kg = float(str(neut.get("总皂脚量_kg", 0)).replace("kg", "").strip() or 0)
    spent_earth_kg = float(str(bleach.get("废白土总量_湿基_kg", 0)).replace("kg", "").strip() or 0)

    revenues["磷脂胶"] = gum_kg * BYPRODUCT_PRICE["磷脂胶"] / 1000
    revenues["皂脚"] = soap_kg * BYPRODUCT_PRICE["皂脚"] / 1000
    # DD油 (VE+甾醇)
    dd_ve = float(str(deod.get("DD油中VE_kg", 0)).replace("kg", "").strip() or 0)
    dd_sterol = float(str(deod.get("DD油中甾醇_kg", 0)).replace("kg", "").strip() or 0)
    revenues["脱臭馏出物"] = (dd_ve + dd_sterol) * BYPRODUCT_PRICE["脱臭馏出物(DD油)"] / 1000

    total_revenue = sum(revenues.values())

    # ── 加工效益 ──
    product_yield_pct = 100 - sum([
        float(str(degum.get("脱胶总油损%", 0)).replace("%", "").strip() or 0),
        float(str(neut.get("碱炼总油损%", 0)).replace("%", "").strip() or 0),
        float(str(bleach.get("脱色总油损%", 0)).replace("%", "").strip() or 0),
        0.3,  # 脱臭约0.3%
    ])
    product_ton = mass_ton * product_yield_pct / 100
    product_value = product_ton * oil_price
    crude_cost = mass_ton * oil_price * 0.92  # 毛油约为成品油价的92%
    gross_margin = product_value - crude_cost - total_cost + total_revenue
    margin_per_ton = gross_margin / product_ton if product_ton > 0 else 0

    return {
        "加工成本": {k: round(v, 0) for k, v in costs.items()},
        "吨油加工成本_元每吨": round(cost_per_ton, 0),
        "总加工成本_元": round(total_cost, 0),
        "副产品收入": {k: round(v, 0) for k, v in revenues.items()},
        "副产品总收入_元": round(total_revenue, 0),
        "成品油量_吨": round(product_ton, 1),
        "成品油价值_元": round(product_value, 0),
        "毛油成本_元": round(crude_cost, 0),
        "加工毛利_元": round(gross_margin, 0),
        "吨油毛利_元每吨": round(margin_per_ton, 0),
    }
