"""
全局配置 — 集中管理所有可调参数
修改此文件即可全局生效，无需逐个模块修改
"""

# ── 服务器 ──
HOST = "0.0.0.0"  # 监听所有网卡，局域网内其他设备可访问
PORT = 5090
DEBUG = False

# ── 校准系数 (接入实测数据时调整此处) ──
CALIBRATION = {
    "degumming": {"hp_removal_factor": 1.02, "nhp_removal_factor": 1.30,
                  "neutral_oil_entrainment": 0.25, "gum_water_ratio": 0.35},
    "neutralization": {"saponification_ratio": 0.18, "entrainment_ratio": 0.0012, "soap_water_ratio": 0.35},
    "bleaching": {"oil_retention": 0.30, "filter_loss_factor": 1.0},
    "deodorization": {"stripping_efficiency": 1.0, "heat_recovery": 0.75, "ejector_ratio": 3.5},
    "winterization": {"wax_cake_oil_ratio": 0.50},
}

# ── 经济参数 (2026年参考) ──
ECONOMICS = {
    "oil_price": {"soybean": 8500, "rapeseed": 10500, "peanut": 18000, "sunflower": 12000,
                  "corn": 11000, "cottonseed": 9000, "palm": 7500, "rice_bran": 9500},
    "utility": {"电_元每kWh": 0.75, "蒸汽_元每吨": 220, "天然气_元每m3": 4.2,
                "工艺水_元每吨": 3.5, "磷酸85%_元每吨": 6500, "液碱32%_元每吨": 1200,
                "活性白土_元每吨": 2800, "柠檬酸_元每吨": 7500},
    "annual_days": 300,
    "annual_utilization": 0.70,
}

# ── 碳足迹因子 ──
CARBON = {"电_kgCO2_per_kWh": 0.581, "蒸汽_kgCO2_per_ton": 290, "天然气_kgCO2_per_m3": 2.16,
          "磷酸_kgCO2_per_kg": 2.8, "液碱_kgCO2_per_kg": 1.1, "白土_kgCO2_per_kg": 0.3}

# ── 蒙特卡洛 ──
MONTE_CARLO = {"default_runs": 50, "av_std_default": 0.3, "p_std_default": 50}

# ── 抑制模块内print(避免控制台刷屏), 生产环境设为True ──
SUPPRESS_PRINT = True
