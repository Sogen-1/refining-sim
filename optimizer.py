"""
油脂精炼工艺模拟引擎 - 一键优化器
给定毛油指标，自动推荐最优工艺参数组合
"""

from core import OilType
from typing import Dict


# 基于油种的智能工艺推荐
SMART_DEFAULTS = {
    OilType.SOYBEAN: {
        "degum": "acid", "pa_pct": 0.10, "excess_lye": 0.10,
        "earth_pct": 1.0, "deodorization_temp_c": 240,
        "route": "chemical", "wax": False,
        "note": "大豆油含NHP约15%，推荐酸法脱胶；适度脱臭(240°C)平衡VE保留与TFA控制",
    },
    OilType.RAPESEED: {
        "degum": "acid", "pa_pct": 0.08, "excess_lye": 0.08,
        "earth_pct": 1.5, "deodorization_temp_c": 235,
        "route": "chemical", "wax": False,
        "note": "菜籽油含叶绿素，需较多白土；低温脱臭(235°C)减少TFA生成",
    },
    OilType.PEANUT: {
        "degum": "water", "pa_pct": 0.05, "excess_lye": 0.06,
        "earth_pct": 0.8, "deodorization_temp_c": 220,
        "route": "chemical", "wax": False,
        "note": "花生油磷脂低可用水化脱胶；低温脱臭保留花生香味",
    },
    OilType.SUNFLOWER: {
        "degum": "acid", "pa_pct": 0.08, "excess_lye": 0.08,
        "earth_pct": 1.5, "deodorization_temp_c": 230,
        "route": "chemical", "wax": True,
        "note": "葵花籽油含蜡(300-800ppm)，必须脱蜡；低温脱臭保留VE",
    },
    OilType.CORN: {
        "degum": "acid", "pa_pct": 0.08, "excess_lye": 0.08,
        "earth_pct": 1.2, "deodorization_temp_c": 235,
        "route": "chemical", "wax": True,
        "note": "玉米油含蜡(200-500ppm)+高VE，脱蜡后低温脱臭保留VE",
    },
    OilType.COTTONSEED: {
        "degum": "acid", "pa_pct": 0.12, "excess_lye": 0.12,
        "earth_pct": 2.5, "deodorization_temp_c": 240,
        "route": "chemical", "wax": False,
        "note": "棉籽油AV高+P高+棉酚色素，需强酸脱胶+高白土+化学精炼",
    },
    OilType.PALM: {
        "degum": "water", "pa_pct": 0.03, "excess_lye": 0.05,
        "earth_pct": 0.8, "deodorization_temp_c": 260,
        "route": "physical", "wax": False,
        "note": "棕榈油P极低(<20ppm),推荐物理精炼跳过碱炼;260°C高温脱酸",
    },
    OilType.RICE_BRAN: {
        "degum": "enzymatic", "pa_pct": 0.15, "excess_lye": 0.15,
        "earth_pct": 2.0, "deodorization_temp_c": 245,
        "route": "chemical", "wax": True,
        "note": "米糠油AV极高+P极高+含蜡+含VE,推荐酶法脱胶+化学精炼+脱蜡;DD油回收VE价值高",
    },
}


def get_smart_defaults(oil_type: OilType) -> dict:
    """根据油种返回推荐的默认工艺参数"""
    return SMART_DEFAULTS.get(oil_type, SMART_DEFAULTS[OilType.SOYBEAN])


def suggest_optimizations(current_params: dict, advisor_findings: list) -> dict:
    """
    基于当前参数和顾问发现的问题，生成优化后的参数建议

    返回: {参数名: (当前值, 建议值, 变更理由)}
    """
    suggestions = {}

    # 从顾问发现中提取建议
    for f in advisor_findings:
        stage = f["stage"]
        sug = f.get("suggestion", "")

        if stage == "脱胶":
            # 提取磷酸建议
            if "磷酸" in sug:
                import re
                pa_matches = re.findall(r'(\d+\.\d+)%', sug)
                current_pa = current_params.get("pa_pct", 0.10)
                if pa_matches:
                    target_pa = float(pa_matches[0])
                    suggestions["pa_pct"] = (current_pa, target_pa,
                        "降低磷酸用量减少油损+磷残留")

        elif stage == "碱炼脱酸":
            if "超量碱" in sug:
                import re
                ex_matches = re.findall(r'(\d+\.\d+)%', sug)
                current_ex = current_params.get("excess_lye", 0.12)
                if ex_matches:
                    suggestions["excess_lye"] = (current_ex, float(ex_matches[0]),
                        "降低超量碱减少中性油皂化损失")

        elif stage == "脱色":
            if "白土" in sug:
                # Earth dosage
                suggestions["earth_optimize"] = (True,
                    "改进前道脱胶/碱炼后白土用量自动降低")

        elif stage == "脱臭":
            if "降温" in sug or "230" in sug:
                current_temp = current_params.get("deodorization_temp_c", 245)
                suggestions["deodorization_temp_c"] = (current_temp, 230,
                    "降温至230°C: 减少TFA生成 + 保留更多VE + 降低蒸汽消耗")

    return suggestions


def build_optimized_params(current: dict, oil_type: OilType) -> dict:
    """
    构建优化后的参数集：用智能默认值替换当前不合理参数
    """
    smart = get_smart_defaults(oil_type)
    optimized = dict(current)

    # 如果脱胶方式明显不合理，建议更优选择
    if current.get("degum") == "water" and oil_type in (OilType.SOYBEAN, OilType.RICE_BRAN):
        optimized["_degum_suggestion"] = smart["degum"]
    else:
        optimized["_degum_suggestion"] = current.get("degum", smart["degum"])

    # PA% 优化
    current_pa = current.get("pa_pct", smart["pa_pct"])
    optimal_pa = smart["pa_pct"]
    optimized["pa_pct"] = round((current_pa + optimal_pa) / 2, 2) if abs(current_pa - optimal_pa) > 0.03 else current_pa

    # 超量碱优化
    current_ex = current.get("excess_lye", smart["excess_lye"])
    optimal_ex = smart["excess_lye"]
    optimized["excess_lye"] = round(min(current_ex, optimal_ex + 0.02), 2)

    # 脱臭温度优化
    current_temp = current.get("deodorization_temp_c", smart["deodorization_temp_c"])
    optimal_temp = smart["deodorization_temp_c"]
    optimized["deodorization_temp_c"] = min(current_temp, optimal_temp + 10)

    # 脱蜡
    optimized["wax"] = smart["wax"]

    # 精炼路线
    optimized["route"] = smart["route"]

    return optimized


def compare_params(current: dict, optimized: dict) -> list:
    """比较当前参数和优化参数，返回差异列表"""
    diffs = []
    keys = [
        ("degum", "脱胶方式"),
        ("pa_pct", "磷酸添加量(%)"),
        ("excess_lye", "超量碱(%)"),
        ("earth_pct", "白土用量(%)"),
        ("deodorization_temp_c", "脱臭温度(°C)"),
        ("route", "精炼路线"),
        ("wax", "脱蜡"),
    ]
    for key, label in keys:
        cur = current.get(key)
        opt = optimized.get(key)
        if cur != opt:
            diffs.append({
                "param": label,
                "current": cur,
                "optimized": opt,
                "impact": _estimate_impact(key, cur, opt),
            })
    return diffs


def _estimate_impact(key: str, current, optimized) -> str:
    """估算参数变更的影响"""
    if key == "pa_pct":
        delta = (current or 0.10) - (optimized or 0.10)
        if delta > 0.02: return f"预计减少油损 {delta*15:.1f}%"
    if key == "excess_lye":
        delta = (current or 0.12) - (optimized or 0.10)
        if delta > 0.02: return f"预计减少油损 {delta*20:.1f}%"
    if key == "deodorization_temp_c":
        delta = (current or 245) - (optimized or 230)
        if delta > 10: return f"减少TFA ~{delta*0.03:.1f}%, 保留VE ~{delta*0.3:.0f}%"
    if key == "route":
        return "跳过碱炼,油损减少2-3%,辅料成本大幅降低"
    return "—"
