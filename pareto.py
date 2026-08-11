"""
帕累托多目标优化
Pareto Multi-Objective Optimization

探索精炼工艺参数空间中多个矛盾目标之间的最优权衡。

典型矛盾:
- 高温脱臭 → FFA脱除好 vs TFA生成多 + VE损失大
- 多磷酸 → 脱胶彻底 vs 油损增加 + 成本上升
- 多白土 → 色泽好 vs 油损增加
- 高超量碱 → AV低 vs 中性油皂化多

方法: 网格搜索 + 非支配排序, 找到帕累托前沿面
"""

from core import CrudeOil, ProcessConditions, OilType
from engine import run_refining
import math
from typing import List, Dict


def pareto_optimize(oil_type: OilType, mass_ton: float,
                    av: float, p_ppm: float, nhp: float = 0.15,
                    objective: str = "yield_vs_quality",
                    steps: int = 6) -> dict:
    """
    帕累托多目标优化

    objective 可选:
      - "yield_vs_quality": 得率 vs 成品AV (矛盾: 更低的AV需要更多碱→更多油损)
      - "yield_vs_nutrition": 得率 vs VE保留 (矛盾: 高温脱臭提高得率但损失VE)
      - "cost_vs_quality": 加工成本 vs 成品品质
      - "yield_vs_safety": 得率 vs TFA控制 (矛盾: 高温提高得率但增加TFA)
      - "all": 四维帕累托
    """

    solutions = []
    oil = CrudeOil(oil_type, "pareto", mass_ton * 1000,
                   acid_value=av, phosphorus_ppm=p_ppm, nhp_ratio=nhp)

    if objective == "yield_vs_quality":
        # 变动: 超量碱 0.05-0.20, 磷酸 0.05-0.18
        for excess_pct in _linspace(0.05, 0.20, steps):
            for pa_pct in _linspace(0.05, 0.18, steps // 2):
                result = _quick_run(oil, pa_pct, excess_pct)
                if result:
                    solutions.append({
                        "params": {"PA%": round(pa_pct, 2), "超量碱%": round(excess_pct, 2)},
                        "yield_pct": result["yield"],
                        "AV": result["av"],
                        "cost_per_ton": result["cost"],
                        "VE_pct": result["ve_retention"],
                        "TFA_pct": result["tfa"],
                    })

    elif objective == "yield_vs_nutrition":
        # 变动: 脱臭温度 210-260, 超量碱 0.06-0.16
        for temp in range(210, 265, (260 - 210) // (steps - 1)):
            for excess_pct in _linspace(0.06, 0.16, steps // 2):
                result = _quick_run(oil, 0.10, excess_pct, deodorization_temp=temp)
                if result:
                    solutions.append({
                        "params": {"脱臭温度°C": temp, "超量碱%": round(excess_pct, 2)},
                        "yield_pct": result["yield"],
                        "AV": result["av"],
                        "cost_per_ton": result["cost"],
                        "VE_pct": result["ve_retention"],
                        "TFA_pct": result["tfa"],
                    })

    elif objective == "cost_vs_quality":
        for excess_pct in _linspace(0.05, 0.20, steps):
            for pa_pct in _linspace(0.05, 0.18, steps // 2):
                for temp in [225, 235, 245]:
                    result = _quick_run(oil, pa_pct, excess_pct, deodorization_temp=temp)
                    if result:
                        solutions.append({
                            "params": {"PA%": round(pa_pct, 2), "超量碱%": round(excess_pct, 2), "脱臭°C": temp},
                            "yield_pct": result["yield"],
                            "AV": result["av"],
                            "cost_per_ton": result["cost"],
                            "VE_pct": result["ve_retention"],
                            "TFA_pct": result["tfa"],
                        })

    elif objective == "all":
        for excess_pct in _linspace(0.06, 0.18, steps):
            for pa_pct in _linspace(0.06, 0.16, max(3, steps // 2)):
                for temp in [225, 235, 245, 255]:
                    result = _quick_run(oil, pa_pct, excess_pct, deodorization_temp=temp)
                    if result:
                        solutions.append({
                            "params": {"PA%": round(pa_pct, 2), "超量碱%": round(excess_pct, 2), "脱臭°C": temp},
                            "yield_pct": result["yield"],
                            "AV": result["av"],
                            "cost_per_ton": result["cost"],
                            "VE_pct": result["ve_retention"],
                            "TFA_pct": result["tfa"],
                        })

    if not solutions:
        return {"error": "未找到可行解"}

    # 帕累托排序: 找出非支配解
    # 目标: 最大化 yield, 最小化 AV, 最小化 cost, 最大化 VE, 最小化 TFA
    pareto_front = _pareto_filter(solutions,
        objectives=["yield_pct", "AV", "cost_per_ton"],  # 默认三维
        directions=["max", "min", "min"])

    # 生成推荐点
    best_yield = max(solutions, key=lambda s: s["yield_pct"])
    best_quality = min(solutions, key=lambda s: s["AV"])
    best_balanced = _find_balanced(solutions)

    return {
        "objective": objective,
        "total_solutions": len(solutions),
        "pareto_optimal_count": len(pareto_front),
        "pareto_front": pareto_front[:15],  # 最多15个前沿点
        "extremes": {
            "最高得率": {"yield": round(best_yield["yield_pct"], 2), "AV": round(best_yield["AV"], 3),
                       "cost": round(best_yield["cost_per_ton"], 0), "params": best_yield["params"]},
            "最佳品质": {"yield": round(best_quality["yield_pct"], 2), "AV": round(best_quality["AV"], 3),
                       "cost": round(best_quality["cost_per_ton"], 0), "params": best_quality["params"]},
        },
        "recommended": {
            "yield": round(best_balanced["yield_pct"], 2),
            "AV": round(best_balanced["AV"], 3),
            "cost": round(best_balanced["cost_per_ton"], 0),
            "VE": round(best_balanced["VE_pct"], 1),
            "TFA": round(best_balanced["TFA_pct"], 2),
            "params": best_balanced["params"],
            "rationale": "综合平衡得率、品质和成本的最优折中方案"
        },
        "insight": _generate_insight(solutions, objective),
    }


def _quick_run(oil, pa_pct, excess_lye, deodorization_temp=None):
    """运行一次全流程并提取关键KPI (调用统一引擎)"""
    try:
        r = run_refining(oil, pa_pct=pa_pct, excess_lye=excess_lye,
                         deodorization_temp=deodorization_temp)
        final = r["final_oil"]
        deod = r["stages"][-1]["results"]
        ve_retention = 100 - float(str(deod.get("VE_损失率%", 20)).replace("%", ""))
        tfa = float(str(deod.get("TFA_预估增加_%", 0.5)).replace("%", ""))
        return {"yield": r["yield_pct"], "av": final.acid_value,
                "cost": r["total_loss_kg"] * 8.5 / (oil.mass_kg / 1000),
                "ve_retention": ve_retention, "tfa": tfa}
    except:
        return None


def _pareto_filter(solutions, objectives, directions):
    """非支配排序: 返回帕累托前沿"""
    front = []
    for i, si in enumerate(solutions):
        dominated = False
        for j, sj in enumerate(solutions):
            if i == j: continue
            # sj dominates si?
            better_in_all = True
            strictly_better = False
            for obj, dir in zip(objectives, directions):
                vi, vj = si[obj], sj[obj]
                if dir == "max":
                    if vj < vi: better_in_all = False; break
                    if vj > vi: strictly_better = True
                else:  # min
                    if vj > vi: better_in_all = False; break
                    if vj < vi: strictly_better = True
            if better_in_all and strictly_better:
                dominated = True; break
        if not dominated:
            front.append(si)
    return front


def _find_balanced(solutions):
    """找综合最优: 各目标归一化后加权评分"""
    if not solutions: return solutions[0]
    # Min-max normalize
    yields = [s["yield_pct"] for s in solutions]; avs = [s["AV"] for s in solutions]
    costs = [s["cost_per_ton"] for s in solutions]
    y_min, y_max = min(yields), max(yields)
    a_min, a_max = min(avs), max(avs)
    c_min, c_max = min(costs), max(costs)
    best_score = -1; best_sol = solutions[0]
    for s in solutions:
        yn = (s["yield_pct"] - y_min) / (y_max - y_min) if y_max > y_min else 0.5
        an = 1 - (s["AV"] - a_min) / (a_max - a_min) if a_max > a_min else 0.5
        cn = 1 - (s["cost_per_ton"] - c_min) / (c_max - c_min) if c_max > c_min else 0.5
        score = yn * 0.4 + an * 0.35 + cn * 0.25
        if score > best_score: best_score = score; best_sol = s
    return best_sol


def _generate_insight(solutions, objective):
    """从帕累托解集中提炼洞察"""
    yields = [s["yield_pct"] for s in solutions]
    avs = [s["AV"] for s in solutions]
    cs = [s["cost_per_ton"] for s in solutions]
    ves = [s.get("VE_pct", 80) for s in solutions]
    tfas = [s.get("TFA_pct", 0.5) for s in solutions]

    best_y = max(yields); best_q = min(avs)
    y_gap = max(yields) - min(yields)
    q_gap = max(avs) - min(avs)

    lines = [
        f"在{len(solutions)}组参数组合中, 得率范围 {min(yields):.1f}%-{best_y:.1f}% (差距{y_gap:.1f}个百分点)",
        f"成品AV范围 {min(avs):.3f}-{max(avs):.3f} (差距{q_gap:.3f})",
    ]
    if y_gap > 1.0:
        lines.append(f"⚠ 得率对参数敏感——优化空间约{y_gap:.1f}个百分点, 对应每吨油¥{y_gap*85:.0f}的价值差异")
    if len(set(int(s.get("TFA_pct", 0) * 100) for s in solutions)) > 3:
        lines.append(f"TFA生成量随脱臭温度显著变化, 控制温度是降TFA最有效的手段")
    if objective == "yield_vs_quality":
        lines.append(f"从最高得率到最佳品质, 需牺牲约{y_gap:.1f}%得率换取AV降低{q_gap:.3f}——对应的经济取舍需结合产品定位判断")
    return lines


def _linspace(start, end, n):
    if n <= 1: return [start]
    return [start + (end - start) * i / (n - 1) for i in range(n)]
