"""
油脂精炼工艺模拟引擎 - 核心数据模型
Refining Process Simulation Engine - Core Data Models

Author: Jiang Zhenyu
Version: 0.1.0
Date: 2026-07-20
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Tuple


class OilType(Enum):
    """油种类型"""
    SOYBEAN = ("大豆油", "soybean")
    RAPESEED = ("菜籽油", "rapeseed")
    PEANUT = ("花生油", "peanut")
    SUNFLOWER = ("葵花籽油", "sunflower")
    CORN = ("玉米油", "corn")
    COTTONSEED = ("棉籽油", "cottonseed")
    PALM = ("棕榈油", "palm")
    RICE_BRAN = ("米糠油", "rice_bran")
    SESAME = ("芝麻油", "sesame")
    BLEND = ("调和油", "blend")

    def __init__(self, cn_name: str, en_name: str):
        self.cn_name = cn_name
        self.en_name = en_name


class PhospholipidType(Enum):
    """磷脂类型"""
    HYDRATABLE = "水化磷脂 (HP)"
    NON_HYDRATABLE = "非水化磷脂 (NHP)"


@dataclass
class CrudeOil:
    """毛油表征模型 - 表征进入精炼车间的毛油品质"""

    oil_type: OilType
    batch_name: str = ""
    mass_kg: float = 1000.0  # 批次质量 (kg)

    # ---- 基础化学指标 ----
    acid_value: float = 4.0         # 酸价 AV (mg KOH/g oil)
    phosphorus_ppm: float = 200.0   # 总磷含量 (mg/kg = ppm)
    nhp_ratio: float = 0.15         # 非水化磷脂占比 (大豆油通常0.05-0.20)
    moisture_pct: float = 0.15      # 水分 (%)
    impurities_pct: float = 0.10    # 杂质 (%)
    color_red: float = 5.0          # 色泽-红 (罗维朋 1英寸槽)
    color_yellow: float = 50.0      # 色泽-黄
    peroxide_value: float = 5.0     # 过氧化值 PV (meq/kg)
    wax_content_ppm: float = 0.0    # 蜡含量 (mg/kg, 葵花籽油/玉米油较高)
    tocopherol_ppm: float = 800.0   # 生育酚含量 (mg/kg)
    sterol_ppm: float = 2500.0      # 植物甾醇含量 (mg/kg)

    @property
    def hp_phosphorus(self) -> float:
        """水化磷脂对应的磷含量"""
        return self.phosphorus_ppm * (1 - self.nhp_ratio)

    @property
    def nhp_phosphorus(self) -> float:
        """非水化磷脂对应的磷含量"""
        return self.phosphorus_ppm * self.nhp_ratio

    @property
    def ffa_pct(self) -> float:
        """游离脂肪酸含量 (% as oleic acid)"""
        return self.acid_value * 0.503 / 100

    @property
    def phospholipid_pct(self) -> float:
        """总磷脂含量 (%)——磷含量(%) × 换算系数31"""
        return self.phosphorus_ppm / 10000 * 31

    def summary(self) -> Dict[str, float]:
        return {
            "酸价 AV (mgKOH/g)": self.acid_value,
            "FFA (%)": round(self.ffa_pct, 4),
            "总磷 (ppm)": self.phosphorus_ppm,
            "水化磷脂磷 (ppm)": round(self.hp_phosphorus, 1),
            "非水化磷脂磷 (ppm)": round(self.nhp_phosphorus, 1),
            "总磷脂 (%)": round(self.phospholipid_pct, 4),
            "水分 (%)": self.moisture_pct,
            "杂质 (%)": self.impurities_pct,
            "色泽 (红/黄)": f"{self.color_red}/{self.color_yellow}",
            "过氧化值 (meq/kg)": self.peroxide_value,
            "生育酚 (ppm)": self.tocopherol_ppm,
            "植物甾醇 (ppm)": self.sterol_ppm,
        }


@dataclass
class ProcessConditions:
    """工艺条件"""
    temperature_c: float = 70.0     # 操作温度 (℃)
    stirring_rpm: int = 80          # 搅拌速度 (rpm)
    residence_time_min: int = 30    # 停留时间 (min)
    acid_conc_pct: float = 85.0     # 磷酸浓度 (%)

    # ---- 脱胶专用 ----
    phosphoric_acid_pct: float = 0.10   # 磷酸添加量 (% of oil)
    water_addition_pct: float = 3.0     # 水化加水量 (% of oil)
    degumming_type: str = "water"       # 脱胶方式: water / acid / enzymatic

    # ---- 碱炼脱酸专用 ----
    lye_conc_be: float = 18.0      # 碱液浓度 (°Bé)
    excess_lye_pct: float = 0.15   # 超量碱 (% of oil)
    wash_water_pct: float = 10.0   # 洗涤水量 (% of oil)

    # ---- 脱色专用 ----
    bleaching_earth_pct: float = 1.5   # 白土添加量 (% of oil)
    activated_carbon_pct: float = 0.2  # 活性炭添加量 (% of oil)
    bleaching_temp_c: float = 105.0    # 脱色温度 (℃)
    bleaching_time_min: int = 30       # 脱色时间 (min)
    vacuum_kpa: float = 2.0           # 真空度 (kPa)

    # ---- 脱臭专用 ----
    deodorization_temp_c: float = 245.0    # 脱臭温度 (℃)
    deodorization_time_min: int = 90       # 脱臭时间 (min)
    stripping_steam_pct: float = 1.5       # 汽提蒸汽 (% of oil)
    deodorization_vacuum_mbar: float = 2.0 # 脱臭真空 (mbar)


# ---- 行业参考值 ----

# 各油种毛油典型指标
CRUDE_OIL_TYPICAL = {
    OilType.SOYBEAN:    {"AV": 0.5,  "P": 800,  "NHP": 0.15, "Wax": 0},
    OilType.RAPESEED:   {"AV": 2.0,  "P": 300,  "NHP": 0.10, "Wax": 0},
    OilType.PEANUT:     {"AV": 1.0,  "P": 100,  "NHP": 0.08, "Wax": 0},
    OilType.SUNFLOWER:  {"AV": 2.0,  "P": 200,  "NHP": 0.10, "Wax": 500},
    OilType.CORN:       {"AV": 3.0,  "P": 250,  "NHP": 0.10, "Wax": 300},
    OilType.COTTONSEED: {"AV": 8.0,  "P": 600,  "NHP": 0.12, "Wax": 0},
    OilType.PALM:       {"AV": 5.0,  "P": 15,   "NHP": 0.05, "Wax": 0},
    OilType.RICE_BRAN:  {"AV": 15.0, "P": 1200, "NHP": 0.10, "Wax": 800},
}

# 脱胶工艺指标
DEGUMMING_TARGETS = {
    "水化脱胶":   {"P_max": 50,  "油损": 0.8},
    "酸法脱胶":   {"P_max": 30,  "油损": 1.2},
    "超级脱胶":   {"P_max": 10,  "油损": 1.5},
    "酶法脱胶":   {"P_max": 5,   "油损": 0.6},
    "全脱胶":     {"P_max": 2,   "油损": 2.0},
}

# 精炼各工段典型油损
REFINING_LOSS_TYPICAL = {
    "脱胶":    0.8,   # %
    "碱炼脱酸": 1.5,   # %
    "脱色":    0.5,   # %
    "脱臭":    0.3,   # %
    "脱蜡":    0.5,   # %
}

# 公用工程单价 (2026年参考)
UTILITY_COST = {
    "电":       0.75,   # 元/kWh
    "蒸汽(1MPa)": 220,  # 元/吨
    "天然气":    4.2,    # 元/m³
    "工艺水":     3.5,   # 元/吨
    "磷酸(85%)":  6500, # 元/吨
    "液碱(32%)":  1200, # 元/吨
    "活性白土":   2800, # 元/吨
    "柠檬酸":    7500,  # 元/吨
}
