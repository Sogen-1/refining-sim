"""
污染物预测模型: 3-MCPD酯/缩水甘油酯(GE)/苯并芘(PAHs)/农药残留/塑化剂
Contaminant Prediction for Food Safety Compliance

参考: EFSA Journal; GB 2762-2025 食品安全国家标准; JECFA 93rd Report
"""

from core import OilType


def predict_ge_formation(temp_c: float, time_min: int, dag_pct: float = 2.0, chlorine_ppm: float = 1.0) -> dict:
    """
    缩水甘油酯(GEs)生成预测
    机理: 甘油二酯(DAG)在>230°C时环化生成GEs
    关键因素: 温度 > 时间 > DAG含量 > 氯离子

    GB 2762-2025 限量: 婴幼儿食品用油 ≤ 0.5 mg/kg; 普通植物油 ≤ 1.0 mg/kg (以缩水甘油计)
    """
    if temp_c < 200:
        ge_ppm = 0.05
        risk = "极低"
    elif temp_c < 230:
        ge_ppm = 0.05 + (temp_c - 200) * 0.01
        risk = "低"
    elif temp_c < 245:
        ge_ppm = 0.35 + (temp_c - 230) * 0.04
        risk = "中"
    elif temp_c < 260:
        ge_ppm = 0.95 + (temp_c - 245) * 0.08
        risk = "高"
    else:
        ge_ppm = 2.15 + (temp_c - 260) * 0.15
        risk = "极高"

    ge_ppm *= (dag_pct / 2.0) * (time_min / 90) * (1 + chlorine_ppm * 0.3)

    compliant_infant = ge_ppm <= 0.5
    compliant_general = ge_ppm <= 1.0

    mitigation = []
    if not compliant_general:
        mitigation.append(f"必须降脱臭温至<240°C (当前{temp_c}°C)")
        mitigation.append("脱臭前充分水洗除氯(目标<0.5ppm)")
    elif not compliant_infant:
        mitigation.append(f"生产婴配用油需降脱臭温至<230°C")

    return {
        "GE_预估含量_mg_per_kg": round(ge_ppm, 2),
        "风险等级": risk,
        "婴配食品合规": "✅ 达标" if compliant_infant else "❌ 超标",
        "普通食品合规": "✅ 达标" if compliant_general else "❌ 超标",
        "参考标准": "GB 2762-2025",
        "减缓措施": mitigation if mitigation else ["当前工艺条件下GE达标"],
    }


def predict_3mcpd_formation(temp_c: float, time_min: int, chlorine_ppm: float = 1.0,
                            precursor_dag: float = 2.0, water_wash: bool = True) -> dict:
    """
    3-氯丙醇酯(3-MCPDE)生成预测
    机理: 氯离子 + 酰基甘油在高温下反应
    GB 2762-2025: 植物油 ≤ 1.25 mg/kg (以3-MCPD计)

    关键控制: 脱胶/碱炼后充分水洗除氯 + 降低脱臭温度
    """
    if water_wash:
        chlorine_ppm *= 0.3

    base_formation = 0.05
    temp_factor = max(0, (temp_c - 200) / 60)
    time_factor = time_min / 90
    cl_factor = chlorine_ppm / 2.0
    dag_factor = precursor_dag / 2.0

    mcpd_ppm = base_formation + 0.3 * temp_factor * time_factor * cl_factor * dag_factor

    compliant = mcpd_ppm <= 1.25

    return {
        "3MCPDE_预估含量_mg_per_kg": round(mcpd_ppm, 2),
        "合规判定": "✅ ≤1.25mg/kg" if compliant else f"❌ 超标 {mcpd_ppm-1.25:.1f}mg/kg",
        "参考标准": "GB 2762-2025",
        "关键控制点": "脱胶/碱炼后充分水洗除氯 → 脱臭温度<240°C → 监测原料氯含量",
        "若氯含量降至0.3ppm": round(base_formation + 0.3 * temp_factor * time_factor * 0.15 * dag_factor, 2),
    }


def predict_pahs_removal(earth_pct: float, activated_carbon_pct: float = 0, oil_type=None) -> dict:
    """
    苯并芘(BaP)及多环芳烃(PAHs)在脱色工段的吸附去除预测

    机理: 活性白土 + 活性炭通过π-π堆积和疏水作用吸附PAHs
    GB 2762-2025: 植物油 BaP ≤ 10 μg/kg; PAH4 总量 ≤ 50 μg/kg

    关键: 活性炭对PAHs的吸附效率是白土的5-10倍
    """
    earth_removal = earth_pct * 12  # 每1%白土去除约12% BaP
    carbon_removal = activated_carbon_pct * 45  # 每0.1%活性炭去除约45% BaP
    total_removal = min(95, earth_removal + carbon_removal)

    # 初始BaP范围 (μg/kg)
    typical_initial = {"大豆油": 2.0, "菜籽油": 3.0, "花生油": 5.0, "葵花籽油": 5.0,
                       "玉米油": 3.0, "棉籽油": 8.0, "棕榈油": 1.0, "米糠油": 6.0}
    init_bap = typical_initial.get(str(oil_type), 3.0) if oil_type else 3.0
    residual_bap = init_bap * (1 - total_removal / 100)

    return {
        "苯并芘初始_μg_per_kg": round(init_bap, 1),
        "BaP脱除率_%": round(total_removal, 1),
        "苯并芘残留_μg_per_kg": round(residual_bap, 1),
        "合规判定(≤10μg/kg)": "✅" if residual_bap <= 10 else "❌",
        "脱除机理": "白土/活性炭π-π吸附;活性炭效率=白土的5-10倍",
        "优化建议": (f"当前白土{earth_pct}%+活性炭{activated_carbon_pct}%, BaP脱除{total_removal:.0f}%。"
                     + ("已达上限" if total_removal > 90 else
                        f"可增加活性炭至{min(0.5, activated_carbon_pct+0.1):.1f}%提升至{min(95, total_removal+15):.0f}%"))
    }


def predict_pesticide_removal(degum_type: str = "acid", earth_pct: float = 1.2,
                              deodorization_temp: float = 245) -> dict:
    """
    农药残留/塑化剂在精炼过程中的去除率预测

    各工段对不同污染物的去除贡献:
    - 脱胶(水化/酸法): 极性农药 30-50%, 塑化剂 10-20%
    - 碱炼: 酸性农药 40-70%, 部分塑化剂水解 20-30%
    - 脱色: 非极性农药 50-80%, 塑化剂 60-80%
    - 脱臭: 挥发性农药 80-99%, 部分塑化剂 30-50%
    """
    degum_eff = {"water": 0.25, "acid": 0.40, "super": 0.50, "enzymatic": 0.55}
    degum_removal = degum_eff.get(degum_type, 0.40)

    removal = {
        "有机磷农药": {
            "脱胶去除率": f"{degum_removal*100:.0f}%",
            "碱炼去除率": "60% (碱解)",
            "脱色去除率": f"{min(85, earth_pct*35):.0f}%",
            "脱臭去除率": f"{min(99, (deodorization_temp-200)*2):.0f}% (挥发)",
            "综合残留": f"<{max(0.01, (1-degum_removal)*0.4*(1-earth_pct*0.35)*0.01)*100:.1f}%",
        },
        "拟除虫菊酯": {
            "脱胶去除率": "20%", "碱炼去除率": "40%",
            "脱色去除率": f"{min(70, earth_pct*25):.0f}%",
            "脱臭去除率": f"{min(95, (deodorization_temp-200)*1.5):.0f}%",
        },
        "塑化剂(PAEs)": {
            "脱胶去除率": "15%", "碱炼去除率": "25% (碱解)",
            "脱色去除率": f"{min(75, earth_pct*30):.0f}% (吸附)",
            "脱臭去除率": f"{min(50, (deodorization_temp-200)):.0f}% (挥发)",
            "注意": "原料中的塑化剂主要来自塑料包装接触,应从源头控制",
        },
    }
    return {"各工段去除率": removal,
            "综合评估": "精炼过程对大多数农药残留有显著去除效果。塑化剂控制以源头管理为主。"}
