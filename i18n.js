var LANG='zh';
var T={
zh:{
  title:"油脂精炼工艺模拟引擎",run:"运行全流程模拟",optimize:"一键智能优化",pareto:"帕累托多目标优化",save:"保存当前方案",export:"导出Excel",reset:"恢复默认",calib:"校准模式",loading:"正在运行模拟...",connecting:"连接服务器...",done:"完成!",
  stages:["脱胶工段计算中...","碱炼脱酸计算中...","脱色工段计算中...","脱臭工段计算中...","生成优化建议...","加载高级分析..."],
  yieldL:"精炼得率",lossL:"总油损",avL:"成品酸价 AV",colorL:"成品色泽 (罗维朋)",emptyMsg:"设置工艺参数后点击运行",noSaved:"暂无保存的方案",clearAll:"清空全部",severe:"严重",warning:"需关注",
  rootCause:"根因分析",improve:"改进措施",savingBreakdown:"节费拆解",invest:"预计投资",payback:"回收期",
  matFlow:"物料流向图",crudeOil:"T 毛油",product_oil:"T 成品",lossNote:"油损占比合计",yieldNote:"精炼得率",
  advTitle:"工艺优化建议",costTitle:"成本核算",processFee:"吨油加工费",marginPerTon:"吨油毛利",totalCost:"总加工成本",byproductInc:"副产品收入",grossMargin:"加工毛利",
  stageDetail:"详细参数",
  radarTitle:"五维综合评分", carbonTitle:"碳足迹", supplyTitle:"供应链优化", gbTitle:"国标合规", byproductTitle:"副产物深加工",
  contaminantsTitle:"食品安全",waterTitle:"水足迹",byproductParams:"副产物深加工工艺参数",processSheet:"标准工艺单",
  foodSafety:"食品安全",freshWater:"新鲜水",wastewaterCOD:"废水COD",
  benchmarkTitle:"行业对标排名",regulatoryTitle:"法规红线",
  oilLabel:"油种选择",massLabel:"批量(吨)",avLabel:"酸价 AV",pLabel:"总磷(ppm)",nhpLabel:"非水化磷脂占比",degumLabel:"脱胶方式",routeLabel:"精炼路线",paLabel:"磷酸添加量(%)",exLabel:"超量碱(%)",waxLabel:"脱蜡",
  oils:{大豆油:"大豆油",菜籽油:"菜籽油",花生油:"花生油",葵花籽油:"葵花籽油",玉米油:"玉米油",棉籽油:"棉籽油",棕榈油:"棕榈油",米糠油:"米糠油"},
  degums:{acid:"酸法脱胶",water:"水化脱胶",super:"超级脱胶",enzymatic:"酶法脱胶"},
  routes:{chemical:"化学精炼(碱炼)",physical:"物理精炼(跳过碱炼)"},wax:{false:"否",true:"是"},
  recommended:"推荐方案",bestYield:"最高得率",bestQuality:"最佳品质",rationale:"综合平衡得率、品质和成本的最优折中方案",
  byproductEcon:"副产物经济性",project:"项目",currentPlan:"当前方案",upgradedPlan:"深加工方案",batchGain:"批增收",
  dcsSheet:"可直接交付DCS工程师",constraints:"约束条件",
  noteFmt:"💡 {0}",footer:"模型基于公开文献经验系数，未经工厂实测数据校准 | 技术支持：姜振宇 15961418818"
},
en:{
  title:"Edible Oil Refining Simulator",run:"Run Simulation",optimize:"Auto Optimize",pareto:"Pareto Optimization",save:"Save",export:"Export CSV",reset:"Reset",calib:"Calibration",loading:"Running...",connecting:"Connecting...",done:"Done!",
  stages:["Degumming...","Neutralizing...","Bleaching...","Deodorizing...","Generating advice...","Loading analytics..."],
  yieldL:"Refining Yield",lossL:"Total Oil Loss",avL:"Product AV",colorL:"Product Color (Lovibond)",emptyMsg:"Set parameters and run simulation",noSaved:"No saved scenarios",clearAll:"Clear All",severe:"Critical",warning:"Warning",
  rootCause:"Root Cause",improve:"Improvement",savingBreakdown:"Savings Breakdown",invest:"Investment",payback:"Payback (months)",
  matFlow:"Material Flow",crudeOil:"T Crude",product_oil:"T Product",lossNote:"Total Loss Ratio",yieldNote:"Refining Yield",
  advTitle:"Optimization Advisor",costTitle:"Cost Breakdown",processFee:"Processing Cost/t",marginPerTon:"Margin/t",totalCost:"Total Cost",byproductInc:"Byproduct Revenue",grossMargin:"Gross Margin",
  stageDetail:"Detailed Parameters",
  radarTitle:"5-Dimensional Scorecard", carbonTitle:"Carbon Footprint", supplyTitle:"Supply Chain Optimization", gbTitle:"GB Standards Compliance", byproductTitle:"Byproduct Upgrading",
  contaminantsTitle:"Food Safety",waterTitle:"Water Footprint",byproductParams:"Byproduct Process Parameters",processSheet:"Process Sheet",
  foodSafety:"Food Safety",freshWater:"Fresh Water",wastewaterCOD:"Wastewater COD",
  benchmarkTitle:"Industry Benchmark",regulatoryTitle:"Regulatory Alerts",
  oilLabel:"Oil Type",massLabel:"Batch (ton)",avLabel:"Acid Value",pLabel:"Phosphorus (ppm)",nhpLabel:"NHP Ratio",degumLabel:"Degumming",routeLabel:"Refining Route",paLabel:"Phosphoric Acid (%)",exLabel:"Excess Lye (%)",waxLabel:"Winterization",
  oils:{大豆油:"Soybean Oil",菜籽油:"Rapeseed Oil",花生油:"Peanut Oil",葵花籽油:"Sunflower Oil",玉米油:"Corn Oil",棉籽油:"Cottonseed Oil",棕榈油:"Palm Oil",米糠油:"Rice Bran Oil"},
  degums:{acid:"Acid Degumming",water:"Water Degumming",super:"Super Degumming",enzymatic:"Enzymatic Degumming"},
  routes:{chemical:"Chemical Refining",physical:"Physical Refining"},wax:{false:"No",true:"Yes"},
  recommended:"Recommended Solution",bestYield:"Max Yield",bestQuality:"Best Quality",rationale:"Optimal balance of yield, quality and cost",
  byproductEcon:"Byproduct Economics",project:"Item",currentPlan:"Current Plan",upgradedPlan:"Upgraded Plan",batchGain:"Gain/Batch",
  dcsSheet:"Ready for DCS Engineer",constraints:"Constraints",
  noteFmt:"💡 {0}",footer:"Model based on published coefficients, not calibrated with plant data | Support: Jiang Zhenyu 15961418818"
},
ru:{
  title:"Симулятор рафинации масел",run:"Запустить расчет",optimize:"Автооптимизация",pareto:"Парето-оптимизация",save:"Сохранить",export:"Экспорт CSV",reset:"Сброс",calib:"Калибровка",loading:"Расчет...",connecting:"Подключение...",done:"Готово!",
  stages:["Дегумминг...","Нейтрализация...","Отбелка...","Дезодорация...","Анализ...","Расширенная аналитика..."],
  yieldL:"Выход рафинации",lossL:"Общие потери",avL:"Кислотное число",colorL:"Цвет (Ловибонд)",emptyMsg:"Задайте параметры и запустите расчет",noSaved:"Нет сохраненных",clearAll:"Очистить",severe:"Критично",warning:"Внимание",
  rootCause:"Причина",improve:"Улучшение",savingBreakdown:"Разбор экономии",invest:"Инвестиции",payback:"Окупаемость(мес)",
  matFlow:"Материальный поток",crudeOil:"T Сырое",product_oil:"T Продукт",lossNote:"Общие потери",yieldNote:"Выход рафинации",
  advTitle:"Рекомендации по оптимизации",costTitle:"Структура затрат",processFee:"Стоимость переработки/т",marginPerTon:"Маржа/т",totalCost:"Общие затраты",byproductInc:"Доход от побочных",grossMargin:"Валовая маржа",
  stageDetail:"Детальные параметры",
  radarTitle:"5D-диаграмма оценки", carbonTitle:"Углеродный след", supplyTitle:"Оптимизация поставок", gbTitle:"Стандарты GB", byproductTitle:"Переработка побочных продуктов",
  contaminantsTitle:"Пищевая безопасность",waterTitle:"Водный след",byproductParams:"Параметры переработки",processSheet:"Технологическая карта",
  foodSafety:"Пищевая безопасность",freshWater:"Свежая вода",wastewaterCOD:"ХПК сточных вод",
  benchmarkTitle:"Отраслевой бенчмарк",regulatoryTitle:"Регуляторные требования",
  oilLabel:"Тип масла",massLabel:"Партия(т)",avLabel:"Кислотное число",pLabel:"Фосфор(ppm)",nhpLabel:"Доля НГФ",degumLabel:"Дегумминг",routeLabel:"Способ рафинации",paLabel:"Фосфорная кислота(%)",exLabel:"Избыток щелочи(%)",waxLabel:"Винтеризация",
  oils:{大豆油:"Соевое",菜籽油:"Рапсовое",花生油:"Арахисовое",葵花籽油:"Подсолнечное",玉米油:"Кукурузное",棉籽油:"Хлопковое",棕榈油:"Пальмовое",米糠油:"Рисовое"},
  degums:{acid:"Кислотный",water:"Водный",super:"Глубокий",enzymatic:"Ферментативный"},
  routes:{chemical:"Химическая",physical:"Физическая"},wax:{false:"Нет",true:"Да"},
  recommended:"Рекомендовано",bestYield:"Макс. выход",bestQuality:"Лучшее качество",rationale:"Оптимальный баланс выхода, качества и стоимости",
  byproductEcon:"Экономика побочных продуктов",project:"Продукт",currentPlan:"Текущий план",upgradedPlan:"Глубокая переработка",batchGain:"Доход/партия",
  dcsSheet:"Готово для инженера",constraints:"Ограничения",
  noteFmt:"💡 {0}",footer:"Модель на основе литературных коэффициентов | Поддержка: Цзян Чжэньюй 15961418818"
}};
function tr(k){var d=T[LANG]||T.zh;return d[k]||k}
function setLang(lang){LANG=lang;localStorage.setItem('refining_lang',lang);location.reload()}
function rebuildSelect(el,opts,cur){if(!el)return;var c=cur||el.value;while(el.firstChild)el.removeChild(el.firstChild);for(var k in opts){var o=document.createElement('option');o.value=k;o.textContent=opts[k];if(String(k)===String(c))o.selected=true;el.appendChild(o)}}
window.addEventListener('DOMContentLoaded',function(){
  try{var s=localStorage.getItem('refining_lang');if(s)LANG=s}catch(e){}
  var d=T[LANG]||T.zh;document.title=d.title;
  var ls=document.querySelectorAll('.fg label'),keys=['oilLabel','massLabel','avLabel','pLabel','nhpLabel','degumLabel','routeLabel','paLabel','exLabel','waxLabel'];
  for(var i=0;i<Math.min(ls.length,keys.length);i++)if(d[keys[i]])ls[i].textContent=d[keys[i]];
  rebuildSelect(document.getElementById('oilType'),d.oils);rebuildSelect(document.getElementById('degum'),d.degums);
  rebuildSelect(document.getElementById('route'),d.routes);rebuildSelect(document.getElementById('wax'),d.wax,document.getElementById('wax')?.value||'0');
});
