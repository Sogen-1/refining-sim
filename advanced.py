"""
高级分析模块: 蒙特卡洛 + 碳足迹 + 雷达评分(含优化路径)
"""

import random, math
from typing import Dict, List
from core import OilType, CrudeOil, ProcessConditions
from degumming import DegummingSimulator
from neutralization import NeutralizationSimulator
from bleaching import BleachingSimulator
from deodorization import DeodorizationSimulator

# ═══════════════════ 蒙特卡洛 ═══════════════════

def monte_carlo_sim(oil_type, mass_ton, av_mean, av_std, p_mean, p_std,
                    nhp_mean, nhp_std, degum_type="acid", excess_lye=0.12, n_runs=100):
    yields = []; avs = []; p_finals = []; colors = []; ves = []
    for _ in range(n_runs):
        av = max(0.1, random.gauss(av_mean, av_std))
        p = max(5, random.gauss(p_mean, p_std))
        nhp = max(0.01, min(0.40, random.gauss(nhp_mean, nhp_std)))
        oil = CrudeOil(oil_type, "MC", mass_ton*1000, acid_value=av, phosphorus_ppm=p, nhp_ratio=nhp)
        try:
            r1 = DegummingSimulator(oil, ProcessConditions(degumming_type=degum_type, phosphoric_acid_pct=0.10)).run()
            r2 = NeutralizationSimulator(r1['脱胶油'], ProcessConditions(excess_lye_pct=excess_lye)).run()
            r3 = BleachingSimulator(r2['碱炼油'], ProcessConditions()).run()
            r4 = DeodorizationSimulator(r3['脱色油'], ProcessConditions()).run()
            final = r4['成品油']
            yields.append(final.mass_kg / oil.mass_kg * 100)
            avs.append(final.acid_value); p_finals.append(final.phosphorus_ppm)
            colors.append(final.color_red); ves.append(final.tocopherol_ppm)
        except: continue
    if not yields: return {"error": "模拟失败"}
    yields.sort(); n = len(yields)
    def pct(arr, p): return arr[int(n * p / 100)]
    return {
        "runs": n,
        "yield": {"p10": round(pct(yields, 10), 2), "p50": round(pct(yields, 50), 2),
                  "p90": round(pct(yields, 90), 2), "min": round(min(yields), 2),
                  "max": round(max(yields), 2), "mean": round(sum(yields)/n, 2),
                  "std": round(math.sqrt(sum((x-sum(yields)/n)**2 for x in yields)/n), 2)},
        "av": {"p10": round(pct(avs, 10), 3), "p50": round(pct(avs, 50), 3),
               "p90": round(pct(avs, 90), 3),
               "fail_rate": round(sum(1 for a in avs if a > 0.10) / n * 100, 1)},
        "risk_summary": f"原料AV波动±{av_std:.1f}、P波动±{p_std:.0f}ppm条件下，得率P10-P90区间为{pct(yields,10):.1f}%-{pct(yields,90):.1f}%。成品AV超标风险约{sum(1 for a in avs if a > 0.10)/n*100:.1f}%。"
    }

# ═══════════════════ 碳足迹 ═══════════════════

EMISSION_FACTORS = {
    "电_kgCO2/kWh": 0.581, "蒸汽_kgCO2/ton": 290, "天然气_kgCO2/m3": 2.16,
    "磷酸_kgCO2/kg": 2.8, "液碱_kgCO2/kg": 1.1, "白土_kgCO2/kg": 0.3, "水_kgCO2/ton": 0.3,
}

def calculate_carbon_footprint(mass_ton, stages_data):
    emissions = {}
    product_ton = mass_ton * 0.92
    elec_kwh = mass_ton * 15
    emissions["电(Scope2)"] = round(elec_kwh * EMISSION_FACTORS["电_kgCO2/kWh"], 1)
    deod = stages_data.get("脱臭", {}).get("计算结果", {})
    steam_kg = float(str(deod.get("总蒸汽消耗_kg", mass_ton * 120)).replace("kg", "").strip() or mass_ton * 120)
    emissions["蒸汽(Scope2)"] = round(steam_kg * EMISSION_FACTORS["蒸汽_kgCO2/ton"] / 1000, 1)
    degum = stages_data.get("脱胶", {}).get("计算结果", {})
    pa_kg = float(str(degum.get("磷酸(85%)用量_kg", mass_ton * 1)).replace("kg", "").strip() or mass_ton * 1)
    emissions["磷酸(Scope3上游)"] = round(pa_kg * EMISSION_FACTORS["磷酸_kgCO2/kg"], 1)
    neut = stages_data.get("碱炼脱酸", {}).get("计算结果", {})
    naoh_kg = float(str(neut.get("折合32%液碱_kg", mass_ton * 5)).replace("kg", "").strip() or mass_ton * 5)
    emissions["液碱(Scope3上游)"] = round(naoh_kg * 0.32 * EMISSION_FACTORS["液碱_kgCO2/kg"], 1)
    bleach = stages_data.get("脱色", {}).get("计算结果", {})
    earth_kg = float(str(bleach.get("白土加入量_kg", mass_ton * 15)).replace("kg", "").strip() or mass_ton * 15)
    emissions["白土(Scope3上游)"] = round(earth_kg * EMISSION_FACTORS["白土_kgCO2/kg"], 1)
    total = sum(emissions.values()); co2_per_ton = total / product_ton if product_ton > 0 else 0
    cbam_cost = total / 1000 * 630  # 欧盟碳价€80 ≈ ¥630
    tips = []; steam_per_ton = steam_kg / mass_ton * 1000 if mass_ton > 0 else 120
    if steam_per_ton > 80: tips.append("蒸汽单耗偏高(>"+str(int(steam_per_ton))+"kg/t)→建议检查热回收系统")
    if elec_kwh / mass_ton > 18: tips.append("电耗偏高→检查电机变频运行比例")
    tips.append("Scope2排放可通过采购绿电/绿证部分抵消")
    return {
        "排放明细": {k: round(v, 1) for k, v in emissions.items()},
        "合计_kgCO2每批": round(total, 0),
        "吨油碳足迹_kgCO2每吨": round(co2_per_ton, 1),
        "EU_CBAM估算成本_元每批": round(cbam_cost, 0),
        "碳足迹评级": "A+ (<50kg/t)" if co2_per_ton < 50 else ("A (50-80)" if co2_per_ton < 80 else ("B (80-120)" if co2_per_ton < 120 else "C (>120)")),
        "减排建议": "; ".join(tips),
    }

# ═══════════════════ 雷达评分(含详细优化路径) ═══════════════════

def radar_scoring(oil_type, results, mass_ton):
    o = {}
    for s_name, s_data in results.items():
        o[s_name] = s_data.get("计算结果", s_data.get("results", {}))

    degum_loss = float(str(o.get("脱胶", {}).get("脱胶总油损%", 2)).replace("%", ""))
    neut_loss = float(str(o.get("碱炼脱酸", {}).get("碱炼总油损%", 0)).replace("%", "") or 2.5)
    total_loss = degum_loss + neut_loss + 1.5
    economy = max(0, min(100, 100 - (total_loss - 3) * 15))

    deod_av = float(str(o.get("脱臭", {}).get("脱臭后AV", 0.05)))
    quality = max(0, min(100, 100 - deod_av * 800))

    ve_loss = float(str(o.get("脱臭", {}).get("VE_损失率%", 20)).replace("%", ""))
    nutrition = max(0, min(100, 100 - (ve_loss - 10) * 3))

    tfa = float(str(o.get("脱臭", {}).get("TFA_预估增加_%", 0.5)).replace("%", ""))
    safety = max(0, min(100, 100 - tfa * 150))

    deod_steam = float(str(o.get("脱臭", {}).get("吨油耗汽_kg蒸汽每吨油", 120)).split("kg")[0].strip() or 120)
    eco = max(0, min(100, 100 - (deod_steam - 50) * 1.2))

    scores = {"经济性": economy, "品质": quality, "营养保留": nutrition, "食品安全": safety, "环保": eco}
    total_score = round((economy + quality + nutrition + safety + eco) / 5, 1)

    # 每维详细优化路径
    plans = {}
    if economy < 70:
        plans["经济性"] = f"当前得分{economy:.0f}/100。总油损约{total_loss:.1f}%偏高。优化路径：①脱胶工段——检查磷酸用量是否过高、提高分离温度至75-80℃；②碱炼工段——将超量碱从当前值降低0.02-0.04个百分点；③脱色工段——改进前道工艺后白土用量可降低。预期油损可压缩至{min(5,total_loss-1):.1f}%，得分提升至{min(100,economy+15):.0f}+。"
    elif economy < 85:
        plans["经济性"] = f"当前得分{economy:.0f}/100。油损处于行业中等水平，仍有0.5-1个百分点的优化空间。关注脱胶离心机运行参数和碱炼皂脚含油率两项关键指标。"
    else:
        plans["经济性"] = f"当前得分{economy:.0f}/100。得率表现优秀。保持现有操作参数，定期监测离心机分离效率即可。"

    if quality < 70:
        plans["品质"] = f"当前得分{quality:.0f}/100。成品AV={deod_av:.2f}偏高。应检查脱臭塔真空度和汽提蒸汽量是否达标；若原料AV波动大，建议在碱炼段增加超量碱0.02-0.03个百分点。"
    elif quality < 85:
        plans["品质"] = f"当前得分{quality:.0f}/100。成品AV={deod_av:.2f}，符合国标一级但距最优有差距。稳定脱臭真空在2mbar以下、保持汽提蒸汽≥1.2%。"
    else:
        plans["品质"] = f"当前得分{quality:.0f}/100。成品酸价和色泽均在优级范围。保持当前脱臭温度和真空度参数。"

    if nutrition < 70:
        plans["营养保留"] = f"当前得分{nutrition:.0f}/100。VE损失率{ve_loss:.0f}%偏高。核心原因：脱臭温度过高→VE蒸馏损失加速。建议将脱臭温度从当前值降至225-235℃，配合提高真空度至1.5mbar。每一度降温可保留约0.5%VE。"
    elif nutrition < 85:
        plans["营养保留"] = f"当前得分{nutrition:.0f}/100。VE损失率{ve_loss:.0f}%。可在脱臭温度上微调5-10℃，或缩短高温段停留时间，保留更多生育酚。"
    else:
        plans["营养保留"] = f"当前得分{nutrition:.0f}/100。VE保留率优异，低温脱臭工艺执行良好。DD油中VE回收价值可能有限，但可作为品质卖点。"

    if safety < 70:
        plans["食品安全"] = f"当前得分{safety:.0f}/100。TFA预估增量{tfa:.2f}%超出'零反式'标准。必须降低脱臭温度至230℃以下，同时延长停留时间补偿脱酸效果。高温(>240℃)下TFA生成呈指数增长，每降10℃可减少约40%TFA生成量。"
    elif safety < 85:
        plans["食品安全"] = f"当前得分{safety:.0f}/100。TFA增量{tfa:.2f}%略超最优标准。考虑脱臭温度降5-10℃，或提升真空度以减少热负荷。监测3-MCPDE和GE前体含量。"
    else:
        plans["食品安全"] = f"当前得分{safety:.0f}/100。TFA控制在安全阈值内。持续监控脱臭温度和停留时间，确保批次间一致。"

    if eco < 70:
        plans["环保"] = f"当前得分{eco:.0f}/100。吨油耗汽{deod_steam:.0f}kg，远高于行业标杆60kg/t。优化路径：①清洗热回收换热器(可能提升回收率10-15%)；②评估干式真空系统替代蒸汽喷射泵(投资回收期约2-3年)；③检查管道保温及疏水阀。年可减少蒸汽消耗{(deod_steam-60)*mass_ton*300/1000:.0f}吨。"
    elif eco < 85:
        plans["环保"] = f"当前得分{eco:.0f}/100。吨油耗汽{deod_steam:.0f}kg，有优化空间。定期清洗换热器、检查保温、优化汽提蒸汽量。"
    else:
        plans["环保"] = f"当前得分{eco:.0f}/100。能耗表现优秀，吨油耗汽已接近标杆水平。定期维保保持效率即可。"

    grade = "S (顶级)" if total_score >= 85 else ("A (优秀)" if total_score >= 70 else ("B (良好)" if total_score >= 55 else "C (需改进)"))

    return {"scores": scores, "total_score": total_score, "grade": grade, "plans": plans}
