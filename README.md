# 油脂精炼工艺模拟引擎 v3.1

## 概述

面向食用植物油精炼行业的工艺模拟与优化工具，覆盖化学精炼和物理精炼两条路线，提供从毛油到成品油的全流程物料平衡计算、能耗预测、成本核算及工艺参数优化建议。

## 技术依据

各工段计算模型基于以下文献与标准：

| 工段 | 主要参考文献 |
|------|------------|
| 脱胶 | Dijkstra, A.J. "Enzymatic Degumming" - *Eur. J. Lipid Sci. Technol.*; Bailey's Industrial Oil and Fat Products (7th Ed., Vol. 5) |
| 碱炼脱酸 | Erickson, D.R. *Practical Handbook of Soybean Processing and Utilization*; GB/T 5530 |
| 脱色 | Zschau, W. "Bleaching of Edible Fats and Oils" - *Eur. J. Lipid Sci. Technol.*; Sarier, N. "Optimization of Bleaching Earth Activity" |
| 脱臭 | De Greyt, W. "Deodorization" - Bailey's (7th Ed.); Pudel, F. "Mitigation of 3-MCPD and glycidyl esters during refining" |
| 脱蜡 | Bailey's (7th Ed., Vol. 5) - Winterization chapter |
| 碳足迹 | 生态环境部《企业温室气体排放核算方法与报告指南》; EU CBAM Regulation 2023/956 |

**注意：** 各工段经验系数（油损率、分离效率、白土吸油率等）基于公开文献及行业经验值，**未使用具体工厂的实测数据进行校准**。实际应用中应以本厂历史数据对标后调整 `calibration.py` 中的系数。

## 模型局限性

1. **稳态假设**：模型基于稳态连续生产工况，不适用于开停车、设备故障等瞬态过程。
2. **普适性**：经验系数取自大豆油/菜籽油文献数据，用于特种油种（如核桃油、橄榄油）时偏差可能增大。
3. **设备差异**：离心机分离效率、脱臭塔塔板数、热回收配置等设备特性未建模，以综合经验系数代替。
4. **经济性**：成本核算中的辅料单价、能源价格为2026年参考值，实际以采购合同为准。
5. **卡脖子分析**：国产替代方案的性能参数为公开资料整理，具体设备选型需与供应商确认。

## 目录结构

```
refining_sim/
├── core.py           数据模型（油种、工艺条件、行业基准值）
├── degumming.py      脱胶工段（水化/酸法/超级/酶法）
├── neutralization.py 碱炼脱酸工段
├── bleaching.py      脱色工段
├── deodorization.py  脱臭工段
├── winterization.py  脱蜡工段
├── pipeline.py       全流程串联 + CLI
├── advisor.py        工艺优化顾问
├── cost.py           成本核算
├── chokepoint.py     供应链优化分析
├── advanced.py        蒙特卡洛/碳足迹/雷达评分
├── optimizer.py       智能参数推荐
├── calibration.py     ⚙️ 校准系数（接入实测数据的关键文件）
├── app.py            Flask Web API
├── app.js            前端逻辑
├── index.html        前端界面
└── 启动.bat          一键启动
```

## 使用方法

### Web界面
双击 `启动.bat`，浏览器访问 `http://127.0.0.1:5090`

### 命令行
```bash
python pipeline.py --oil 大豆油 --mass 100 --av 2.0 --p 800
```

### API
```bash
curl -X POST http://127.0.0.1:5090/api/run \
  -H "Content-Type: application/json" \
  -d '{"oil":"大豆油","mass":100,"av":2.0,"p":800}'
```

## 校准流程

用本厂实测数据校准模型（使偏差 <5%）：

1. 取一批完整的精炼生产数据（毛油→脱胶→碱炼→脱色→脱臭的全套化验单 + 实际消耗）
2. 用同样的毛油指标在本引擎中运行
3. 对比模拟值与实测值的偏差
4. 打开 `calibration.py`，调整对应工段的系数
5. 重复步骤2-4直到偏差 <5%

## 免责声明

本工具仅供工艺分析与参考之用，不构成任何形式的工艺包或工程设计。实际生产参数应以工厂操作规程、设备手册及化验结果为准。作者不对因使用本工具而产生的任何直接或间接损失承担责任。

---

技术支持：姜振宇 | 15961418818
