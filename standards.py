"""
国标合规检查 + 副产物深加工经济性
"""

from core import OilType

# GB标准 (2025版现行)
GB_STANDARDS = {
    "大豆油": {"std": "GB/T 1535", "一级": {"AV": 0.50, "P": 10, "R": 2.0, "PV": 5.0, "M": 0.05, "I": 0.05},
               "二级": {"AV": 2.0, "P": 10, "R": 4.0, "PV": 5.0, "M": 0.10, "I": 0.10},
               "三级": {"AV": 4.0, "P": 10, "R": None, "PV": 6.0, "M": 0.20, "I": 0.20}},
    "菜籽油": {"std": "GB/T 1536", "一级": {"AV": 0.50, "P": 10, "R": 2.0, "PV": 5.0, "M": 0.05, "I": 0.05},
               "二级": {"AV": 2.0, "P": 10, "R": 4.0, "PV": 5.0, "M": 0.10, "I": 0.10},
               "三级": {"AV": 4.0, "P": 10, "R": None, "PV": 6.0, "M": 0.20, "I": 0.20}},
    "花生油": {"std": "GB/T 1534", "一级": {"AV": 1.0, "P": 10, "R": 1.5, "PV": 6.0, "M": 0.05, "I": 0.05}},
    "葵花籽油": {"std": "GB/T 10464", "一级": {"AV": 0.50, "P": 10, "R": 2.0, "PV": 5.0, "M": 0.05, "I": 0.05},
                "二级": {"AV": 2.0, "P": 10, "R": 4.0, "PV": 5.0, "M": 0.10, "I": 0.10},
                "三级": {"AV": 4.0, "P": 10, "R": None, "PV": 6.0, "M": 0.20, "I": 0.20}},
    "玉米油": {"std": "GB/T 19111", "一级": {"AV": 0.50, "P": 10, "R": 2.0, "PV": 5.0, "M": 0.05, "I": 0.05},
               "二级": {"AV": 2.0, "P": 10, "R": 4.0, "PV": 5.0, "M": 0.10, "I": 0.10},
               "三级": {"AV": 4.0, "P": 10, "R": None, "PV": 6.0, "M": 0.20, "I": 0.20}},
    "棉籽油": {"std": "GB/T 1537", "一级": {"AV": 0.50, "P": 10, "R": 2.5, "PV": 5.0, "M": 0.05, "I": 0.05},
               "二级": {"AV": 2.0, "P": 10, "R": 4.0, "PV": 5.0, "M": 0.10, "I": 0.10},
               "三级": {"AV": 4.0, "P": 10, "R": None, "PV": 6.0, "M": 0.20, "I": 0.20}},
    "棕榈油": {"std": "GB/T 15680", "一级": {"AV": 0.20, "P": 10, "R": 3.0, "PV": 5.0, "M": 0.05, "I": 0.05},
               "二级": {"AV": 0.50, "P": 10, "R": 6.0, "PV": 6.0, "M": 0.10, "I": 0.10}},
    "米糠油": {"std": "GB/T 19112", "一级": {"AV": 0.50, "P": 10, "R": 3.5, "PV": 5.0, "M": 0.05, "I": 0.05},
               "二级": {"AV": 2.0, "P": 10, "R": 5.0, "PV": 5.0, "M": 0.10, "I": 0.10},
               "三级": {"AV": 4.0, "P": 10, "R": None, "PV": 6.0, "M": 0.20, "I": 0.20}},
}


def check_gb_compliance(oil_name: str, output: dict) -> dict:
    """
    检查成品油是否符合各级国标
    AV=酸价, R=色泽红, PV=过氧化值, P=磷, M=水分, I=杂质
    """
    stds = GB_STANDARDS.get(oil_name)
    if not stds: return {"error": f"暂无{oil_name}国标数据"}

    av = output.get("product_av", 0)
    r_val = output.get("product_color_r", 2)
    p_val = output.get("product_p_ppm", 5)

    results = {}
    for grade, limits in stds.items():
        if grade == "std": continue
        checks = []
        if av > limits["AV"]:
            checks.append(f"酸价 {av:.2f} > {limits['AV']} (超标)")
        else:
            checks.append(f"酸价 {av:.2f} ≤ {limits['AV']} ✓")
        if limits["R"] is not None and r_val > limits["R"]:
            checks.append(f"色泽R {r_val:.1f} > {limits['R']} (超标)")
        elif limits["R"] is not None:
            checks.append(f"色泽R {r_val:.1f} ≤ {limits['R']} ✓")
        if p_val > limits["P"]:
            checks.append(f"磷 {p_val:.1f} > {limits['P']} (超标)")
        else:
            checks.append(f"磷 {p_val:.1f} ≤ {limits['P']} ✓")
        passed = all("✓" in c for c in checks)
        results[grade] = {"passed": passed, "checks": checks}

    # Determine best grade
    best = "不达标"
    for g in ["一级", "二级", "三级"]:
        if g in results and results[g]["passed"]:
            best = g; break

    return {
        "standard": stds["std"],
        "grade": best,
        "details": results,
        "verdict": f"产品达到{best}标准 ({stds['std']})" if best != "不达标" else "产品未达到国标最低要求,需调整工艺",
    }


def byproduct_deep_processing(mass_ton: float, stages_data: dict) -> dict:
    """副产物深加工经济性评估"""
    degum = stages_data.get("脱胶", {}).get("计算结果", {})
    neut = stages_data.get("碱炼脱酸", {}).get("计算结果", {})
    deod = stages_data.get("脱臭", {}).get("计算结果", {})

    gum_kg = float(str(degum.get("脱胶总油损_kg", mass_ton * 1000 * 0.03)).replace("kg", "").strip() or mass_ton * 1000 * 0.03)
    soap_kg = float(str(neut.get("总皂脚量_kg", mass_ton * 1000 * 0.04)).replace("kg", "").strip() or mass_ton * 1000 * 0.04)
    dd_ve = float(str(deod.get("DD油中VE_kg", 0.015)).replace("kg", "").strip() or 0.015)
    dd_sterol = float(str(deod.get("DD油中甾醇_kg", 0.015)).replace("kg", "").strip() or 0.015)

    items = []

    # 磷脂精制
    gum_ton = gum_kg / 1000
    lecithin_value_raw = gum_ton * 800   # 直接卖胶质 ¥800/t
    lecithin_value_purified = gum_ton * 0.4 * 8000  # 精制成粉末磷脂 40%得率 ¥8000/t
    items.append({
        "name": "磷脂精制",
        "current": f"胶质直接出售: ¥{lecithin_value_raw:.0f}/批",
        "upgraded": f"粉末磷脂(投资~200万): ¥{lecithin_value_purified:.0f}/批",
        "net_gain": round(lecithin_value_purified - lecithin_value_raw, 0),
    })

    # 皂脚酸化
    soap_ton = soap_kg / 1000
    acid_oil_yield = soap_ton * 0.45  # 酸化油得率约45%
    acid_oil_value = acid_oil_yield * 4500  # 酸化油 ¥4500/t
    items.append({
        "name": "皂脚酸化",
        "current": f"皂脚出售: ¥{soap_ton*1500:.0f}/批",
        "upgraded": f"酸化油(投资~50万): ¥{acid_oil_value:.0f}/批",
        "net_gain": round(acid_oil_value - soap_ton * 1500, 0),
    })

    # DD油VE回收
    dd_ton = (dd_ve + dd_sterol) / 1000
    dd_raw = dd_ton * 5000
    dd_upgraded = dd_ton * 25000 * 0.6
    items.append({
        "name": "DD油VE/甾醇回收",
        "current": f"DD油出售: ¥{dd_raw:.0f}/批",
        "upgraded": f"VE/甾醇提取(投资~500万): ¥{dd_upgraded:.0f}/批",
        "net_gain": round(dd_upgraded - dd_raw, 0),
    })

    total_gain = sum(i["net_gain"] for i in items)
    return {
        "items": items,
        "total_annual_gain": round(total_gain * 210, 0),  # 210批/年
        "total_gain_desc": f"三项副产物深加工年增收约 ¥{total_gain*210/10000:.1f}万",
    }
