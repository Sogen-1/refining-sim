"""
油脂精炼工艺模拟引擎 - 全流程串联与命令行界面
Refining Process Simulation - Full Pipeline Runner

用法:
    python pipeline.py --oil 大豆油 --mass 100 --av 2.0 --p 800
    python pipeline.py --oil 米糠油 --mass 50 --av 15 --p 1200 --degum enzymatic
    python pipeline.py --interactive  # 交互模式
"""

import sys, io, argparse, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core import CrudeOil, ProcessConditions, OilType, CRUDE_OIL_TYPICAL, UTILITY_COST
from degumming import DegummingSimulator
from neutralization import NeutralizationSimulator
from bleaching import BleachingSimulator
from deodorization import DeodorizationSimulator


class RefiningPipeline:
    """全流程精炼模拟"""

    def __init__(self, crude_oil: CrudeOil, config: dict = None):
        self.crude_oil = crude_oil
        self.config = config or {}
        self.stages = {}
        self.cost_summary = {}

    def run(self, stages: list = None):
        """
        执行指定工段

        stages: ['degumming', 'neutralization', 'bleaching', 'deodorization']
        默认全部
        """
        if stages is None:
            stages = ['degumming', 'neutralization', 'bleaching', 'deodorization']

        current_oil = self.crude_oil
        total_loss_kg = 0
        total_cost = 0

        print("\n" + "="*70)
        print(f"  🏭 油脂精炼全流程模拟")
        print(f"  原料: {current_oil.oil_type.cn_name} | "
              f"批量: {current_oil.mass_kg/1000:.1f}T | "
              f"AV: {current_oil.acid_value:.1f} | "
              f"P: {current_oil.phosphorus_ppm:.0f}ppm")
        print("="*70)

        for stage in stages:
            print(f"\n{'─'*70}")
            print(f"  ▶ {stage.upper()}")
            print(f"{'─'*70}")

            if stage == 'degumming':
                cond = ProcessConditions(**self.config.get('degumming', {}))
                sim = DegummingSimulator(current_oil, cond)
                result = sim.run()
                current_oil = result['脱胶油']
                self.stages[stage] = result

            elif stage == 'neutralization':
                cond = ProcessConditions(**self.config.get('neutralization', {}))
                sim = NeutralizationSimulator(current_oil, cond)
                result = sim.run()
                current_oil = result['碱炼油']
                self.stages[stage] = result

            elif stage == 'bleaching':
                cond = ProcessConditions(**self.config.get('bleaching', {}))
                sim = BleachingSimulator(current_oil, cond)
                result = sim.run()
                current_oil = result['脱色油']
                self.stages[stage] = result

            elif stage == 'deodorization':
                cond = ProcessConditions(**self.config.get('deodorization', {}))
                sim = DeodorizationSimulator(current_oil, cond)
                result = sim.run()
                current_oil = result['成品油']
                self.stages[stage] = result

        # 汇总
        total_loss = self.crude_oil.mass_kg - current_oil.mass_kg
        yield_pct = current_oil.mass_kg / self.crude_oil.mass_kg * 100

        print(f"\n{'='*70}")
        print(f"  📊 全流程汇总")
        print(f"{'='*70}")
        print(f"  毛油投入:    {self.crude_oil.mass_kg/1000:>8.2f} 吨")
        print(f"  成品油产出:  {current_oil.mass_kg/1000:>8.2f} 吨")
        print(f"  总油损:      {total_loss/1000:>8.2f} 吨 ({total_loss/self.crude_oil.mass_kg*100:.1f}%)")
        print(f"  精炼得率:    {yield_pct:>8.1f}%")
        print(f"{'='*70}\n")

        return {
            "成品油": current_oil,
            "得率%": round(yield_pct, 1),
            "各工段": self.stages,
        }


def main():
    parser = argparse.ArgumentParser(description='油脂精炼工艺模拟引擎 v0.1')
    parser.add_argument('--oil', type=str, default='大豆油', help='油种 (大豆油/菜籽油/米糠油/棉籽油/花生油/棕榈油)')
    parser.add_argument('--mass', type=float, default=100, help='批处理量 (吨)')
    parser.add_argument('--av', type=float, default=None, help='酸价 (mgKOH/g)')
    parser.add_argument('--p', type=float, default=None, help='磷含量 (ppm)')
    parser.add_argument('--degum', type=str, default='acid', help='脱胶方式 (water/acid/super/enzymatic)')
    parser.add_argument('--excess', type=float, default=0.12, help='超量碱 (%)')
    parser.add_argument('--json', action='store_true', help='JSON格式输出')

    args = parser.parse_args()

    # Resolve oil type
    oil_map = {
        "大豆油": OilType.SOYBEAN, "豆油": OilType.SOYBEAN,
        "菜籽油": OilType.RAPESEED, "菜油": OilType.RAPESEED,
        "花生油": OilType.PEANUT, "葵花籽油": OilType.SUNFLOWER,
        "玉米油": OilType.CORN, "棉籽油": OilType.COTTONSEED,
        "棕榈油": OilType.PALM, "米糠油": OilType.RICE_BRAN,
    }
    oil_type = oil_map.get(args.oil, OilType.SOYBEAN)
    typical = CRUDE_OIL_TYPICAL.get(oil_type, {"AV": 2.0, "P": 200, "NHP": 0.10})

    oil = CrudeOil(
        oil_type=oil_type,
        batch_name=args.oil,
        mass_kg=args.mass * 1000,
        acid_value=args.av or typical["AV"],
        phosphorus_ppm=args.p or typical["P"],
        nhp_ratio=typical["NHP"],
        wax_content_ppm=typical.get("Wax", 0),
    )

    config = {
        "degumming": {"degumming_type": args.degum, "phosphoric_acid_pct": 0.10},
        "neutralization": {"excess_lye_pct": args.excess},
        "bleaching": {},
        "deodorization": {},
    }

    pipeline = RefiningPipeline(oil, config)
    result = pipeline.run()  # Run all 4 stages

    if args.json:
        # Output simplified JSON
        out = {
            "原料": {"油种": oil.oil_type.cn_name, "批量_吨": oil.mass_kg/1000,
                    "酸价": oil.acid_value, "磷_ppm": oil.phosphorus_ppm},
            "脱胶": result["各工段"]["degumming"]["计算结果"],
            "碱炼": result["各工段"]["neutralization"]["计算结果"],
            "得率": result["得率%"],
        }
        print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
