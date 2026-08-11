"""
供应链优化与国产替代经济性分析
Supply Chain Optimization & Domestic Alternatives

分析当前依赖进口的关键物料和设备，评估国产替代方案的经济效益。
"""

from core import OilType
from typing import Dict, List


# ═══════════════════════════════════════════════
#  卡脖子技术清单 — 每项的进口/替代数据
# ═══════════════════════════════════════════════

CHOKE_POINTS = {
    "磷脂酶制剂": {
        "foreign_supplier": "进口磷脂酶制剂",
        "domestic_alternative": "国产磷脂酶 (已实现产业化)",
        "current_status": "进口占比 >90%",
        "import_price_per_kg": 8000,
        "domestic_price_per_kg": 2500,
        "usage_kg_per_batch_100t": 0.15,
        "annual_cost_import": 0,
        "annual_cost_domestic": 0,
        "saving_desc": "",
    },
    "碟式离心机": {
        "foreign_supplier": "进口碟式离心机",
        "domestic_alternative": "国产离心机 (大型化已突破)",
        "current_status": "大型机型(>200t/d)进口占比 >85%",
        "import_price_per_unit": 3500000,
        "domestic_price_per_unit": 1200000,
        "units_per_line": 3,
        "import_uptime_pct": 95,
        "domestic_uptime_pct": 88,
        "import_oil_loss_extra_pct": 0,
        "domestic_oil_loss_extra_pct": 0.3,
        "maintenance_import_per_year": 150000,
        "maintenance_domestic_per_year": 60000,
        "saving_desc": "",
    },
    "流程模拟软件": {
        "foreign_supplier": "进口流程模拟软件",
        "domestic_alternative": "国产流程模拟软件 (已通过国家级验收)",
        "current_status": "油脂行业进口占比 ~100%",
        "import_price_per_year": 450000,
        "domestic_price_per_year": 80000,
        "training_cost_import": 200000,
        "training_cost_domestic": 30000,
        "saving_desc": "",
    },
    "VE/甾醇回收工艺": {
        "foreign_supplier": "进口VE回收工艺包",
        "domestic_alternative": "国产DD油VE提取技术 (已实现中试)",
        "current_status": "高效回收工艺以进口为主,DD油多廉价出售",
        "dd_oil_price_raw": 5000,
        "dd_oil_ve_value": 25000,
        "dd_oil_ton_per_100t": 0.03,
        "investment_for_plant": 5000000,
        "saving_desc": "",
    },
    "OPO结构脂酶": {
        "foreign_supplier": "进口固定化脂肪酶",
        "domestic_alternative": "国产固定化脂肪酶 (已突破产业化)",
        "current_status": "进口占比 >95%",
        "import_price_per_kg": 50000,
        "domestic_price_per_kg": 15000,
        "usage_kg_per_ton_opo": 0.5,
        "annual_opo_production_ton": 500,
        "saving_desc": "",
    },
}


def analyze_chokepoints(oil_type: OilType, mass_ton: float, degum_type: str,
                        route: str, stages_data: dict) -> dict:
    """
    供应链优化分析 — 对比进口与国产方案的经济性

    覆盖: 酶制剂、离心机、工业软件、VE回收、OPO结构脂酶
    返回: 每项的进口成本、国产替代成本、节省金额、优化建议
    """
    results = []

    # ── 1. 酶制剂 ──
    enzyme = dict(CHOKE_POINTS["磷脂酶制剂"])
    batch_kg = enzyme["usage_kg_per_batch_100t"] * mass_ton / 100
    annual_batches = 300 * 0.7  # 年开工率
    enzyme["annual_cost_import"] = round(batch_kg * enzyme["import_price_per_kg"] * annual_batches, 0)
    enzyme["annual_cost_domestic"] = round(batch_kg * enzyme["domestic_price_per_kg"] * annual_batches, 0)
    enzyme["annual_saving"] = round(enzyme["annual_cost_import"] - enzyme["annual_cost_domestic"], 0)
    enzyme["payback_years"] = 0  # 无额外投资,直接替换
    enzyme["recommendation"] = (
        "可切换国产,年省显著" if enzyme["annual_saving"] > 50000 else
        "持续关注国产进展" if degum_type == "enzymatic" else "当前非酶法工艺,暂不涉及"
    )
    if degum_type == "enzymatic":
        enzyme["saving_desc"] = f"酶法脱胶切换国产磷脂酶: 年省 ¥{enzyme['annual_saving']/10000:.1f}万"
        results.append(enzyme)

    # ── 2. 离心机 ──
    centrifuge = dict(CHOKE_POINTS["碟式离心机"])
    units = centrifuge["units_per_line"]
    # 进口成本
    import_depreciation = centrifuge["import_price_per_unit"] * units / 15  # 15年折旧
    import_maintenance = centrifuge["maintenance_import_per_year"] * units
    # 国产成本
    domestic_depreciation = centrifuge["domestic_price_per_unit"] * units / 12  # 12年折旧
    domestic_maintenance = centrifuge["maintenance_domestic_per_year"] * units
    # 国产额外油损
    extra_oil_loss_ton = mass_ton * centrifuge["domestic_oil_loss_extra_pct"] / 100
    oil_value_lost = extra_oil_loss_ton * 8500 * annual_batches  # 按豆油价

    centrifuge["import_annual_cost"] = round(import_depreciation + import_maintenance, 0)
    centrifuge["domestic_annual_cost"] = round(domestic_depreciation + domestic_maintenance + oil_value_lost, 0)
    centrifuge["annual_saving"] = round(centrifuge["import_annual_cost"] - centrifuge["domestic_annual_cost"], 0)
    centrifuge["domestic_extra_oil_loss_warning"] = (
        f"国产离心机多损失 {extra_oil_loss_ton:.2f}吨油/批 (¥{oil_value_lost/10000:.1f}万/年)" if extra_oil_loss_ton > 0 else ""
    )
    centrifuge["recommendation"] = (
        "建议混合配置: 关键工位进口+辅助工位国产" if centrifuge["annual_saving"] < 0 else
        "可评估国产替代" if centrifuge["annual_saving"] > 100000 else
        "暂维持现有方案"
    )
    centrifuge["saving_desc"] = (
        f"国产离心机替代: {'年省' if centrifuge['annual_saving']>0 else '年增成本'} "
        f"¥{abs(centrifuge['annual_saving'])/10000:.1f}万"
        + (f", 但额外油损 {centrifuge['domestic_oil_loss_extra_pct']}%" if centrifuge['annual_saving']<0 else "")
    )
    results.append(centrifuge)

    # ── 3. 工业软件 ──
    software = dict(CHOKE_POINTS["流程模拟软件"])
    software["annual_saving"] = (
        software["import_price_per_year"] - software["domestic_price_per_year"]
        + software["training_cost_import"] - software["training_cost_domestic"]
    )
    software["recommendation"] = "建议切换 — 国产流程模拟软件已成熟,可大幅降低许可费"
    software["saving_desc"] = f"国产流程模拟软件替代进口方案: 年省 ¥{software['annual_saving']/10000:.1f}万"
    results.append(software)

    # ── 4. VE/甾醇回收 ──
    deod_raw = stages_data.get("脱臭", {})
    deod = deod_raw.get("计算结果", deod_raw.get("results", {}))
    try:
        dd_ve = float(str(deod.get("DD油中VE_kg", "0.015")).replace("kg", "").strip() or 0.015)
    except: dd_ve = 0.015
    try:
        dd_sterol = float(str(deod.get("DD油中甾醇_kg", "0.015")).replace("kg", "").strip() or 0.015)
    except: dd_sterol = 0.015
    dd_total_ton = (dd_ve + dd_sterol) / 1000 * annual_batches

    ve_recovery = dict(CHOKE_POINTS["VE/甾醇回收工艺"])
    raw_value = dd_total_ton * ve_recovery["dd_oil_price_raw"]
    upgraded_value = dd_total_ton * ve_recovery["dd_oil_ve_value"] * 0.6  # 回收率60%
    ve_recovery["annual_saving"] = round(upgraded_value - raw_value, 0)
    ve_recovery["investment"] = ve_recovery["investment_for_plant"]
    ve_recovery["payback_years"] = round(
        ve_recovery["investment"] / ve_recovery["annual_saving"], 1
    ) if ve_recovery["annual_saving"] > 0 else 999
    ve_recovery["recommendation"] = (
        f"投资回收期约{ve_recovery['payback_years']}年,建议评估" if ve_recovery['payback_years'] < 3 else
        "可关注,视DD油产量而定" if dd_total_ton > 5 else
        "当前DD油产量偏低,暂不推荐投资"
    )
    ve_recovery["saving_desc"] = (
        f"VE/甾醇提纯回收: DD油增值 ¥{ve_recovery['annual_saving']/10000:.1f}万/年"
    )
    results.append(ve_recovery)

    # ── 5. OPO结构脂酶 ──
    opo = dict(CHOKE_POINTS["OPO结构脂酶"])
    opo["annual_cost_import"] = opo["usage_kg_per_ton_opo"] * opo["annual_opo_production_ton"] * opo["import_price_per_kg"]
    opo["annual_cost_domestic"] = opo["usage_kg_per_ton_opo"] * opo["annual_opo_production_ton"] * opo["domestic_price_per_kg"]
    opo["annual_saving"] = round(opo["annual_cost_import"] - opo["annual_cost_domestic"], 0)
    opo["recommendation"] = "优先评估 — 国产固定化脂肪酶已成熟,可显著降低OPO生产成本"
    opo["saving_desc"] = f"OPO固定化脂肪酶国产替代: 年省 ¥{opo['annual_saving']/10000:.1f}万"
    results.append(opo)

    # ── 汇总 ──
    total_saving = sum(r.get("annual_saving", 0) for r in results)
    high_priority = len([r for r in results if r.get("annual_saving", 0) > 500000])

    return {
        "items": results,
        "total_annual_saving": round(total_saving, 0),
        "total_saving_desc": f"全部优化项采纳后, 预计年节省 ¥{total_saving/10000:.1f}万",
        "high_priority_count": high_priority,
        "summary": (
            f"覆盖 {len(results)} 项供应链优化机会。"
            f"其中 {high_priority} 项年节省超50万,建议优先评估。"
            f"全部采纳后预计年节省 ¥{total_saving/10000:.1f}万。"
        ),
    }
