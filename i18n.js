var LANG='zh';
var T={
zh:{title:"油脂精炼工艺模拟引擎",run:"▶ 运行全流程模拟",optimize:"⚡ 一键智能优化",save:"💾 保存当前方案",export:"📥 导出 Excel",reset:"↺ 恢复默认",pareto:"📊 帕累托多目标优化",calib:"🔧 校准模式",toggle:"校准模式",loading:"正在运行模拟...",connecting:"连接服务器...",
 stages:["脱胶工段计算中...","碱炼脱酸计算中...","脱色工段计算中...","脱臭工段计算中...","生成优化建议...","加载高级分析..."],
 yieldL:"精炼得率",lossL:"总油损",avL:"成品酸价 AV",colorL:"成品色泽 (罗维朋 1\")",
 sankeyTitle:"物料流向图",sankeyFlow:"T 毛油 → ","T 成品",
 advisorTitle:"工艺优化建议",costTitle:"成本核算",radarTitle:"五维综合评分",carbonTitle:"碳足迹",supplyTitle:"供应链优化",gbTitle:"国标合规",byproductTitle:"副产物深加工",
 oilLabel:"油种选择",massLabel:"批量 (吨)",avLabel:"酸价 AV (mgKOH/g)",pLabel:"总磷 (ppm)",nhpLabel:"非水化磷脂占比",degumLabel:"脱胶方式",routeLabel:"精炼路线",paLabel:"磷酸添加量 (%)",exLabel:"超量碱 (%)",waxLabel:"脱蜡 (葵花/玉米/米糠油)",
 oils:{大豆油:"大豆油",菜籽油:"菜籽油",花生油:"花生油",葵花籽油:"葵花籽油",玉米油:"玉米油",棉籽油:"棉籽油",棕榈油:"棕榈油",米糠油:"米糠油"},
 degums:{acid:"酸法脱胶",water:"水化脱胶",super:"超级脱胶",enzymatic:"酶法脱胶"},
 routes:{chemical:"化学精炼 (碱炼)",physical:"物理精炼 (跳过碱炼)"},
 wax:{no:"否",yes:"是"},
 noteFmt:"💡 {0}",emptyMsg:"设置工艺参数后点击运行",noSaved:"暂无保存的方案",clearAll:"清空全部",
 severe:"严重",warning:"需关注",rootCause:"📋 根因分析:",improve:"✅ 改进措施:",saving:"💰 节费拆解",invest:"🔧 预计投资",payback:"回收期",
 materialFlow:"物料流向图",lossPctNote:"油损占比合计",yieldNote:"精炼得率",
 processingFee:"吨油加工费",margin:"吨油毛利",totalCost:"总加工成本",byproductIncome:"副产品收入",grossMargin:"加工毛利",
 stageDetail:"详细参数",
 carbonRating:"碳足迹评级", steamNote:"EU CBAM预计", kgCO2:"kg CO₂/t",
 product:"成品",
 recommended:"推荐方案", bestYield:"最高得率", bestQuality:"最佳品质",
 costBreakdown:"成本核算",
 fillIP:"请输入显示的IP地址并提交"
},
en:{title:"Edible Oil Refining Simulator",run:"▶ Run Simulation",optimize:"⚡ Auto Optimize",save:"💾 Save",export:"📥 Export CSV",reset:"↺ Reset",pareto:"📊 Pareto Optimization",calib:"🔧 Calibration",toggle:"Calibration",loading:"Running simulation...",connecting:"Connecting...",
 stages:["Degumming...","Neutralizing...","Bleaching...","Deodorizing...","Generating advice...","Loading analytics..."],
 yieldL:"Refining Yield",lossL:"Total Oil Loss",avL:"Product AV",colorL:"Product Color (Lovibond 1\")",
 sankeyTitle:"Material Flow",sankeyFlow:"T Crude → ","T Product",
 advisorTitle:"Optimization Advisor",costTitle:"Cost Breakdown",radarTitle:"5D Scorecard",carbonTitle:"Carbon Footprint",supplyTitle:"Supply Chain Optimization",gbTitle:"GB Standards Compliance",byproductTitle:"Byproduct Upgrading",
 oilLabel:"Oil Type",massLabel:"Batch (ton)",avLabel:"Acid Value (mgKOH/g)",pLabel:"Phosphorus (ppm)",nhpLabel:"NHP Ratio",degumLabel:"Degumming Method",routeLabel:"Refining Route",paLabel:"Phosphoric Acid (%)",exLabel:"Excess Lye (%)",waxLabel:"Winterization",
 oils:{大豆油:"Soybean Oil",菜籽油:"Rapeseed Oil",花生油:"Peanut Oil",葵花籽油:"Sunflower Oil",玉米油:"Corn Oil",棉籽油:"Cottonseed Oil",棕榈油:"Palm Oil",米糠油:"Rice Bran Oil"},
 degums:{acid:"Acid Degumming",water:"Water Degumming",super:"Super Degumming",enzymatic:"Enzymatic Degumming"},
 routes:{chemical:"Chemical Refining",physical:"Physical Refining"},
 wax:{no:"No",yes:"Yes"},
 noteFmt:"💡 {0}",emptyMsg:"Set parameters and run simulation",noSaved:"No saved scenarios",clearAll:"Clear All",
 severe:"Critical",warning:"Warning",rootCause:"Root Cause:",improve:"Improvement:",saving:"Savings Breakdown",invest:"Investment",payback:"Payback months",
 materialFlow:"Material Flow",lossPctNote:"Total loss ratio",yieldNote:"Yield",
 processingFee:"Processing cost/t",margin:"Margin/t",totalCost:"Total Cost",byproductIncome:"Byproduct Income",grossMargin:"Gross Margin",
 stageDetail:"Detailed Parameters",
 carbonRating:"Carbon Rating", steamNote:"EU CBAM Est.", kgCO2:"kg CO₂/t",
 product:"Product",
 recommended:"Recommended", bestYield:"Max Yield", bestQuality:"Best Quality",
 costBreakdown:"Cost Breakdown",
 fillIP:"Enter your IP address shown above"
},
ru:{title:"Симулятор рафинации масел",run:"▶ Запустить расчет",optimize:"⚡ Автооптимизация",save:"💾 Сохранить",export:"📥 Экспорт CSV",reset:"↺ Сброс",pareto:"📊 Парето-оптимизация",calib:"🔧 Калибровка",toggle:"Калибровка",loading:"Идет расчет...",connecting:"Подключение...",
 stages:["Дегумминг...","Нейтрализация...","Отбелка...","Дезодорация...","Анализ...","Расширенная аналитика..."],
 yieldL:"Выход рафинации",lossL:"Общие потери масла",avL:"Кислотное число",colorL:"Цвет (Ловибонд 1\")",
 sankeyTitle:"Материальный поток",sankeyFlow:"T Сырое → ","T Продукт",
 advisorTitle:"Рекомендации по оптимизации",costTitle:"Структура затрат",radarTitle:"5D-диаграмма",carbonTitle:"Углеродный след",supplyTitle:"Оптимизация поставок",gbTitle:"Стандарты GB",byproductTitle:"Переработка побочных продуктов",
 oilLabel:"Тип масла",massLabel:"Партия (т)",avLabel:"Кислотное число (мгKOH/г)",pLabel:"Фосфор (ppm)",nhpLabel:"Доля НГФ",degumLabel:"Метод дегумминга",routeLabel:"Способ рафинации",paLabel:"Фосфорная кислота (%)",exLabel:"Избыток щелочи (%)",waxLabel:"Винтеризация",
 oils:{大豆油:"Соевое",菜籽油:"Рапсовое",花生油:"Арахисовое",葵花籽油:"Подсолнечное",玉米油:"Кукурузное",棉籽油:"Хлопковое",棕榈油:"Пальмовое",米糠油:"Рисовое"},
 degums:{acid:"Кислотный",water:"Водный",super:"Глубокий",enzymatic:"Ферментативный"},
 routes:{chemical:"Химическая",physical:"Физическая"},
 wax:{no:"Нет",yes:"Да"},
 noteFmt:"💡 {0}",emptyMsg:"Задайте параметры и запустите расчет",noSaved:"Нет сохраненных",clearAll:"Очистить",
 severe:"Критично",warning:"Внимание",rootCause:"Причина:",improve:"Улучшение:",saving:"Разбор экономии",invest:"Инвестиции",payback:"Окупаемость (мес)",
 materialFlow:"Материальный поток",lossPctNote:"Общие потери",yieldNote:"Выход",
 processingFee:"Стоимость переработки/т",margin:"Маржа/т",totalCost:"Общие затраты",byproductIncome:"Доход от побочных",grossMargin:"Валовая маржа",
 stageDetail:"Детальные параметры",
 carbonRating:"Углеродный рейтинг", steamNote:"EU CBAM Оценка", kgCO2:"кг CO₂/т",
 product:"Продукт",
 recommended:"Рекомендовано", bestYield:"Макс. выход", bestQuality:"Лучшее качество",
 costBreakdown:"Структура затрат",
 fillIP:"Введите ваш IP-адрес"}
};
function t(k){var d=T[LANG]||T['zh'];return d[k]||k}
function setLang(lang){LANG=lang;localStorage.setItem('refining_lang',lang);applyLangNow()}
function applyLangNow(){
 var d=T[LANG]||T['zh'];
 document.title=d.title;
 var logoEl=document.querySelector('.brand');if(logoEl)logoEl.textContent='⚙ '+d.title;
 var ls=document.querySelectorAll('.fg label');
 var keys=['oilLabel','massLabel','avLabel','pLabel','nhpLabel','degumLabel','routeLabel','paLabel','exLabel','waxLabel'];
 for(var i=0;i<Math.min(ls.length,keys.length);i++){var k=keys[i];if(d[k])ls[i].textContent=d[k]}
 var oi=document.getElementById('oilType');if(oi&&d.oils){while(oi.firstChild)oi.removeChild(oi.firstChild);for(var ok in d.oils){var opt=document.createElement('option');opt.value=ok;opt.textContent=d.oils[ok];oi.appendChild(opt)}}
 var dg=document.getElementById('degum');if(dg&&d.degums){while(dg.firstChild)dg.removeChild(dg.firstChild);for(var dk in d.degums){var opt=document.createElement('option');opt.value=dk;opt.textContent=d.degums[dk];dg.appendChild(opt)}}
 var rt=document.getElementById('route');if(rt&&d.routes){while(rt.firstChild)rt.removeChild(rt.firstChild);for(var rk in d.routes){var opt=document.createElement('option');opt.value=rk;opt.textContent=d.routes[rk];rt.appendChild(opt)}}
 var wx=document.getElementById('wax');if(wx&&d.wax){while(wx.firstChild)wx.removeChild(wx.firstChild);for(var wk in d.wax){var opt=document.createElement('option');opt.value=(wk==='yes'?'1':'0');opt.textContent=d.wax[wk];wx.appendChild(opt)}}
 var btns=document.querySelectorAll('.btn-p,.btn-o,.btn-s');
 var btnKeys=['run','optimize','pareto','save','export','reset','calib','toggle'];
 for(var i=0;i<btns.length;i++){var idx=btnKeys[i];if(idx&&d[idx])btns[i].textContent=d[idx]}
}
function tr(k){return T[LANG]?.[k]||T['zh'][k]||k}
window.addEventListener('DOMContentLoaded',function(){
 try{var s=localStorage.getItem('refining_lang');if(s)LANG=s}catch(e){}
 var d=T[LANG]||T['zh'];
 // Update static elements
 document.title=d.title;
 var logoEl=document.querySelector('.brand');if(logoEl)logoEl.textContent='⚙ '+d.title;
 // Update labels
 var ls=document.querySelectorAll('.fg label');
 var keys=['oilLabel','massLabel','avLabel','pLabel','nhpLabel','degumLabel','routeLabel','paLabel','exLabel','waxLabel'];
 for(var i=0;i<Math.min(ls.length,keys.length);i++){var k=keys[i];if(d[k])ls[i].textContent=d[k]}
 // Update selects
 var oi=document.getElementById('oilType');if(oi&&d.oils){while(oi.firstChild)oi.removeChild(oi.firstChild);for(var ok in d.oils){var opt=document.createElement('option');opt.value=ok;opt.textContent=d.oils[ok];oi.appendChild(opt)}}
 var dg=document.getElementById('degum');if(dg&&d.degums){while(dg.firstChild)dg.removeChild(dg.firstChild);for(var dk in d.degums){var opt=document.createElement('option');opt.value=dk;opt.textContent=d.degums[dk];dg.appendChild(opt)}}
 var rt=document.getElementById('route');if(rt&&d.routes){while(rt.firstChild)rt.removeChild(rt.firstChild);for(var rk in d.routes){var opt=document.createElement('option');opt.value=rk;opt.textContent=d.routes[rk];rt.appendChild(opt)}}
 var wx=document.getElementById('wax');if(wx&&d.wax){while(wx.firstChild)wx.removeChild(wx.firstChild);for(var wk in d.wax){var opt=document.createElement('option');opt.value=(wk==='yes'?'1':'0');opt.textContent=d.wax[wk];wx.appendChild(opt)}}
 // Update buttons
 var btns=document.querySelectorAll('.btn-p,.btn-o,.btn-s');
 var btnKeys=['run','optimize','pareto','save','export','reset','calib','toggle'];
 for(var i=0;i<btns.length;i++){var idx=btnKeys[i];if(idx&&d[idx])btns[i].textContent=d[idx]}
});