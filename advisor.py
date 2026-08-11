"""
油脂精炼工艺模拟引擎 - 优化顾问 v2.0
每个建议附带精确的成本分项拆解，告诉用户"省了多少钱、从哪里省的"
"""

from typing import Dict, List
from core import OilType, UTILITY_COST


class OptimizationAdvisor:
    """精炼工艺优化顾问 — 精准成本核算版"""

    BENCHMARKS = {
        "degumming": {
            "residual_p_ppm": {"acid": 15, "super": 8, "enzymatic": 4, "water": 50},
            "oil_loss_pct": {"acid": 2.0, "super": 2.5, "enzymatic": 1.2, "water": 1.5},
            "phosphoric_pct": {"min": 0.05, "max": 0.15, "optimal": 0.10},
        },
        "neutralization": {
            "oil_loss_pct": 2.5, "excess_lye_optimal": 0.10, "residual_av": 0.08,
        },
        "bleaching": {
            "oil_loss_pct": 0.8, "earth_dosage_optimal": 1.0, "color_red_target": 1.0,
        },
        "deodorization": {
            "steam_per_ton": 60, "tfa_increase_pct": 0.3, "ve_loss_pct": 15, "residual_av": 0.05,
        },
    }

    OIL_PRICE = {
        OilType.SOYBEAN: 8500, OilType.RAPESEED: 10500, OilType.PEANUT: 18000,
        OilType.SUNFLOWER: 12000, OilType.CORN: 11000, OilType.COTTONSEED: 9000,
        OilType.PALM: 7500, OilType.RICE_BRAN: 9500,
    }

    # 辅料单价 (元/吨)
    CHEM_PRICE = {
        "磷酸85%": 6500, "液碱32%": 1200, "活性白土": 2800, "活性炭": 8000,
        "硅藻土": 3000, "柠檬酸": 7500,
    }

    def __init__(self, oil_type: OilType, results: dict, mass_ton: float):
        self.oil_type = oil_type
        self.results = results
        self.mass_ton = mass_ton
        self.price = self.OIL_PRICE.get(oil_type, 9000)
        self.daily_ton = mass_ton  # 假设日处理量=批量的70% (实际连续生产)
        self.annual_days = 300
        self.annual_ton = self.daily_ton * self.annual_days * 0.7
        self.findings: List[dict] = []

    def analyze(self) -> List[dict]:
        self.findings = []
        def _get_results(key):
            d = self.results.get(key, {})
            return d.get("计算结果", d.get("results", {}))
        degum = _get_results("脱胶")
        neut = _get_results("碱炼脱酸")
        bleach = _get_results("脱色")
        deod = _get_results("脱臭")
        wax = _get_results("脱蜡")

        for checker in [self._check_degumming, self._check_neutralization,
                        self._check_bleaching, self._check_deodorization]:
            try:
                if checker == self._check_degumming: checker(degum)
                elif checker == self._check_neutralization: checker(neut)
                elif checker == self._check_bleaching: checker(bleach)
                elif checker == self._check_deodorization: checker(deod)
            except Exception as e:
                self._add(1, "系统", f"分析异常: {e}", "", "", [])
        if wax:
            try: self._check_wax(wax)
            except: pass

        self.findings.sort(key=lambda f: f.get("total_saving", 0), reverse=True)
        # Remove error placeholders
        self.findings = [f for f in self.findings if f["severity"] != 1 or f["title"] != "分析异常"]
        return self.findings

    def _add(self, severity: int, stage: str, title: str, cause: str,
             suggestion: str, savings: List[dict], investment: float = 0):
        """添加一条优化建议，附带详细的成本拆解"""
        valid_savings = [s for s in savings if s and isinstance(s, dict) and s.get("amount", 0) > 0]
        total = sum(s["amount"] for s in valid_savings)
        self.findings.append({
            "severity": severity,
            "stage": stage,
            "title": title,
            "cause": cause,
            "suggestion": suggestion,
            "savings_breakdown": savings,
            "total_saving": round(total, 0),
            "total_saving_desc": f"¥{total/10000:.1f}万/年" if total >= 10000 else f"¥{total:.0f}/年",
            "investment": round(investment, 0),
            "payback_months": round(investment / (total / 12), 1) if total > 0 and investment > 0 else 0,
        })

    def _oil_saving(self, pct_saved: float, label: str) -> dict:
        """计算节省油的价值"""
        tons_saved = self.mass_ton * pct_saved / 100
        annual_tons = self.annual_ton * pct_saved / 100
        annual_yuan = annual_tons * self.price
        return {
            "category": "油损降低",
            "label": label,
            "amount": round(annual_yuan, 0),
            "detail": f"减少油损 {pct_saved:.2f}% ({annual_tons:.1f}吨/年) × ¥{self.price}/吨",
        }

    def _chem_saving(self, chem_name: str, kg_per_batch: float, new_kg: float) -> dict:
        """计算节省辅料的费用"""
        saved_kg = kg_per_batch - new_kg
        if saved_kg <= 0: return None
        price = self.CHEM_PRICE.get(chem_name, 5000)
        annual_yuan = saved_kg / 1000 * price * self.annual_days * 0.7
        return {
            "category": "辅料成本",
            "label": f"减少{chem_name}用量",
            "amount": round(annual_yuan, 0),
            "detail": f"从 {kg_per_batch:.0f}kg/批 降至 {new_kg:.0f}kg/批 × {self.annual_days*0.7:.0f}批/年",
        }

    def _steam_saving(self, kg_per_ton_saved: float) -> dict:
        """计算节省蒸汽的费用"""
        annual_yuan = self.annual_ton * kg_per_ton_saved / 1000 * UTILITY_COST["蒸汽(1MPa)"]
        return {
            "category": "能源成本",
            "label": "降低蒸汽消耗",
            "amount": round(annual_yuan, 0),
            "detail": f"吨油耗汽降低 {kg_per_ton_saved:.0f}kg × {self.annual_ton:.0f}吨/年 × ¥{UTILITY_COST['蒸汽(1MPa)']}/吨",
        }

    def _byproduct_gain(self, label: str, tons_per_year: float, price_per_ton: float) -> dict:
        """计算副产品增收"""
        return {
            "category": "副产品增收",
            "label": label,
            "amount": round(tons_per_year * price_per_ton, 0),
            "detail": f"增产 {tons_per_year:.1f}吨/年 × ¥{price_per_ton}/吨",
        }

    # ═══════════════════════════════════════
    #  各工段检查
    # ═══════════════════════════════════════

    def _check_degumming(self, d: dict):
        if not d: return
        degum_type = d.get("脱胶方式", "acid")
        bm_p = self.BENCHMARKS["degumming"]["residual_p_ppm"].get(degum_type, 30)
        bm_loss = self.BENCHMARKS["degumming"]["oil_loss_pct"].get(degum_type, 2.0)

        residual_p = float(str(d.get("残留磷_ppm", 0)).replace("ppm", "").strip())
        oil_loss = float(str(d.get("脱胶总油损%", 0)).replace("%", "").strip())
        pa_pct = float(str(d.get("磷酸添加量%", 0.10)).replace("%", "").strip())
        pa_kg = float(str(d.get("磷酸(85%)用量_kg", self.mass_ton*1000*0.001)).replace("kg", "").strip() or self.mass_ton*1000*0.001)

        # 1) 残留磷过高 → 后续工段白土消耗增加
        if residual_p > bm_p * 2:
            gap = residual_p - bm_p
            extra_pa_needed = min(0.10, gap * 0.0015)
            # 磷过高导致脱色白土多耗约 (residual_p/10 - bm_p/10)*0.15%
            extra_earth_pct = max(0, (residual_p - bm_p) / 30 * 0.15)
            savings = [
                self._chem_saving("活性白土",
                    self.mass_ton * 1000 * (1.5 + extra_earth_pct) / 100,
                    self.mass_ton * 1000 * 1.0 / 100),
            ]
            inv = self.mass_ton * 1000 * extra_pa_needed / 100 * self.CHEM_PRICE["磷酸85%"] / 1000 * self.annual_days * 0.7
            self._add(3, "脱胶",
                f"脱胶后残留磷 {residual_p:.0f}ppm — 超标 {gap:.0f}ppm，倒逼脱色工段多用白土 {extra_earth_pct:.2f}%",
                f"非水化磷脂(NHP)未充分转化 → 残留磷进入脱色 → 白土活性位点被磷占据 → 被迫增加白土用量",
                f"【根因解决】磷酸量从 {pa_pct:.2f}% 提至 {pa_pct+extra_pa_needed:.2f}%，加强NHP转化；或切换酶法脱胶一步到位降至 <5ppm",
                [s for s in savings if s],
                inv * 0.3)

        # 2) 油损过高
        if oil_loss > bm_loss * 1.3:
            excess_pct = oil_loss - bm_loss
            savings = [self._oil_saving(excess_pct * 0.7, "脱胶油损降至标杆")]
            self._add(3, "脱胶",
                f"脱胶油损 {oil_loss:.1f}% — 超过标杆 {bm_loss}% 约 {excess_pct:.1f}个百分点",
                "磷酸过量→乳化→胶脚含水增加→离心分离困难→中性油夹带多",
                f"【立即可做】1)磷酸降至 {max(0.05, pa_pct-0.03):.2f}% 2)分离温度提至75℃ 3)离心机进料减量10%",
                savings)

        # 3) 磷酸过量
        if pa_pct > 0.18:
            chem_s = self._chem_saving("磷酸85%", pa_kg, self.mass_ton*1000*0.12/100)
            savings = [chem_s] if chem_s else []
            savings.append(self._oil_saving(0.15, "减少磷酸过量导致的额外油损"))
            self._add(2, "脱胶",
                f"磷酸用量 {pa_pct:.2f}% 偏高 (推荐 {self.BENCHMARKS['degumming']['phosphoric_pct']['optimal']:.2f}%)",
                "过量磷酸: ①消耗更多碱→碱炼成本增加 ②增加废水磷负荷 ③残留磷加重脱色负担",
                f"降至 0.10-0.12%，每年省磷酸 {(pa_kg-self.mass_ton*1000*0.12/100)*self.annual_days*0.7/1000:.0f}吨",
                savings)

    def _check_neutralization(self, n: dict):
        if not n: return
        loss = float(str(n.get("碱炼总油损%", 0)).replace("%", "").strip())
        excess = float(str(n.get("超量碱%", 0.12)).replace("%", "").strip())
        naoh_kg = float(str(n.get("折合32%液碱_kg", self.mass_ton*1000*0.005)).replace("kg", "").strip() or self.mass_ton*1000*0.005)

        if loss > 3.5:
            gap = loss - 2.5
            savings = [
                self._oil_saving(gap * 0.5, "降低皂化油损"),
                self._oil_saving(gap * 0.2, "降低机械夹带油损"),
            ]
            chem_s = self._chem_saving("液碱32%", naoh_kg, naoh_kg * 0.75)
            if chem_s: savings.append(chem_s)

            self._add(3, "碱炼脱酸",
                f"碱炼油损 {loss:.1f}% — 超标 {gap:.1f}个百分点 (标杆: 2.5%)",
                f"超量碱 {excess:.2f}% 过高→中性油被皂化 + 皂脚含油率高 + 离心分离效果差",
                f"【核心措施】1)超量碱从 {excess:.2f}% 降至 0.08-0.10% 2)碱炼温度提至80-85℃降低乳化 3)每班清洗离心机碟片",
                savings)

    def _check_bleaching(self, b: dict):
        if not b: return
        actual = float(str(b.get("实际白土用量%", 1.5)).replace("%", "").strip())
        rec = float(str(b.get("推荐白土用量%", 1.2)).replace("%", "").strip())
        color_r = float(str(b.get("出油色泽_红", 1.5)).replace("R", "").strip())

        if actual > rec * 1.4 and actual > 1.2:
            excess_earth = actual - rec
            savings = [
                self._chem_saving("活性白土",
                    self.mass_ton * 1000 * actual / 100,
                    self.mass_ton * 1000 * rec / 100),
                self._oil_saving(excess_earth * 0.30 / 100, "减少白土夹带油损"),
            ]
            self._add(3, "脱色",
                f"白土用量 {actual:.1f}% 远超推荐值 {rec:.1f}% — 多耗 {excess_earth:.1f}个百分点",
                "根本原因不在脱色工段本身，而在前道脱胶未除尽的磷脂+碱炼残留的皂→占据白土活性位点→'被迫'加量",
                f"【治本】改进脱胶/碱炼工段后再看白土需求；【治标】检查脱色真空度、将白土分批加入提高利用率",
                [s for s in savings if s])

        if color_r > 2.5:
            self._add(2, "脱色",
                f"脱色后红值 R{color_r:.1f} 偏高，成品可能降级",
                "白土量不足或脱色温度/真空度未达标",
                f"将白土量调至 {min(2.5, actual+0.5):.1f}%；检查真空 <5kPa；延长脱色时间至35min",
                [])

    def _check_deodorization(self, d: dict):
        if not d: return
        steam = float(str(d.get("吨油耗汽_kg蒸汽每吨油", 150)).replace("kg", "").strip().split("kg")[0].strip() or 150)
        tfa = float(str(d.get("TFA_预估增加_%", 0.5)).replace("%", "").strip())
        ve_loss = float(str(d.get("VE_损失率%", 20)).replace("%", "").strip())
        temp = float(str(d.get("脱臭温度_C", 245)).replace("°C", "").strip())

        # 蒸汽过高
        if steam > 80:
            excess = steam - 60
            savings = [self._steam_saving(excess * 0.7)]
            savings.append({
                "category": "能源成本",
                "label": "减少碳排放",
                "amount": round(self.annual_ton * excess * 0.7 / 1000 * 0.25 * 60, 0),
                "detail": f"年减少蒸汽 {self.annual_ton*excess*0.7/1000:.0f}吨 ≈ 减排CO₂ {(self.annual_ton*excess*0.7/1000*0.25):.0f}吨",
            })
            inv = 0
            if excess > 40:
                inv = 800000  # 改造干式真空系统
                self._add(3, "脱臭",
                    f"吨油耗汽 {steam:.0f}kg/t — 超标 {excess:.0f}kg/t (标杆:60kg/t)，年多耗蒸汽 {(self.annual_ton*excess/1000):.0f}吨",
                    "①喷射真空泵效率低 ②热回收换热器结垢 ③脱臭塔保温不良",
                    f"【高回报】改造干式真空系统(投资¥{inv/10000:.0f}万)替换蒸汽喷射泵；【低成本】清洗热回收换热器、检查保温层",
                    savings, inv)
            else:
                self._add(2, "脱臭",
                    f"吨油耗汽 {steam:.0f}kg/t — 偏高 {excess:.0f}kg/t",
                    "热回收效率不足或汽提蒸汽过量",
                    "检查并清洗省煤器；将汽提蒸汽从1.5%降至1.2%",
                    savings)

        # TFA 过高
        if tfa > 0.5:
            savings = [
                self._byproduct_gain("保留VE价值(低温脱臭减少VE蒸馏损失)",
                    self.annual_ton * (ve_loss/100 - 0.12) * 0.8 / 1000 * 0.15, 500000),
            ]
            self._add(2, "脱臭",
                f"TFA 预测增量 {tfa:.2f}% — 超过'零反式'标准(0.3%)",
                f"脱臭温度{temp}°C过高→亚麻酸异构化→TFA生成量指数增长",
                f"【降本+提质】将脱臭温度从{temp}°C降至230°C + 真空提至1.5mbar + 延长停留时间至120min → TFA降至<0.3%",
                savings)

    def _check_wax(self, w: dict):
        if not w or w.get("脱蜡评价","").startswith("跳过"): return
        wax_removal = float(str(w.get("蜡脱除率_%", 80)).replace("%", "").strip())
        oil_loss = float(str(w.get("总油损_%", 1)).replace("%", "").strip())
        if wax_removal < 70:
            self._add(2, "脱蜡",
                f"蜡脱除率仅 {wax_removal:.0f}% — 成品冷试验可能不合格",
                "结晶温度不够低或降温速率过快，蜡晶体生长不充分",
                "降低结晶终温至4-5°C；降温速率降至1.5°C/h；延长养晶时间至10h",
                [])


def analyze_results(oil_type: OilType, results: dict, mass_ton: float) -> dict:
    advisor = OptimizationAdvisor(oil_type, results, mass_ton)
    findings = advisor.analyze()

    total_saving = sum(f["total_saving"] for f in findings)
    critical = sum(1 for f in findings if f["severity"] == 3)

    # Group savings by category
    categories = {}
    for f in findings:
        for s in f.get("savings_breakdown", []):
            cat = s.get("category", "其他")
            categories[cat] = categories.get(cat, 0) + s.get("amount", 0)

    # Cost structure: where is money currently being lost
    loss_by_stage = {}
    total_lost = 0
    for stage_name, stage_data in results.items():
        r = stage_data.get("results", {})
        for k, v in r.items():
            if "总油损" in str(k) and ("%" in str(k) or "pct" in str(k)):
                try:
                    pct = float(str(v).replace("%", "").strip())
                    lost_ton = mass_ton * pct / 100
                    lost_yuan = lost_ton * advisor.price * advisor.annual_days * 0.7 / advisor.mass_ton * mass_ton
                    loss_by_stage[stage_name] = round(lost_yuan, 0)
                    total_lost += lost_yuan
                except: pass

    return {
        "total_issues": len(findings),
        "critical": critical,
        "warnings": len(findings) - critical,
        "findings": findings,
        "total_saving": round(total_saving, 0),
        "saving_desc": f"¥{total_saving/10000:.1f}万/年" if total_saving >= 10000 else f"¥{total_saving:.0f}/年",
        "saving_categories": {k: round(v, 0) for k, v in sorted(categories.items(), key=lambda x: -x[1])},
        "summary": (
            f"共发现 {len(findings)} 个优化机会 ({critical}个严重)。"
            f"全部实施后预计每年净节省 ¥{total_saving/10000:.1f}万元。"
        ) if findings else "✅ 各工段运行指标均在行业标杆范围内。",
    }
