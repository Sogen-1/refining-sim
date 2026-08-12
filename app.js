var OIL_TYPICALS={大豆油:{av:2.0,p:800,nhp:.15},菜籽油:{av:2.0,p:300,nhp:.10},花生油:{av:1.0,p:100,nhp:.08},葵花籽油:{av:2.0,p:200,nhp:.10},玉米油:{av:3.0,p:250,nhp:.10},棉籽油:{av:8.0,p:600,nhp:.12},棕榈油:{av:5.0,p:15,nhp:.05},米糠油:{av:15.0,p:1200,nhp:.10}};
var currentResult=null,allResults=[],savedScenarios=[],pendingRadar=null;
// Load saved scenarios from localStorage
try{var stored=localStorage.getItem('refining_scenarios');if(stored)savedScenarios=JSON.parse(stored)}catch(e){}
window.addEventListener('beforeunload',function(){try{localStorage.setItem('refining_scenarios',JSON.stringify(savedScenarios))}catch(e){}});
if(savedScenarios.length>0)renderSidebar();

async function onOilChange(){
  var v=document.getElementById('oilType').value,t=OIL_TYPICALS[v];
  if(t){document.getElementById('av').value=t.av;document.getElementById('p').value=t.p;document.getElementById('nhp').value=t.nhp}
  try{var r=await fetch('/api/smart-defaults?oil='+encodeURIComponent(v)),s=await r.json();
    document.getElementById('degum').value=s.degum||'acid';document.getElementById('pa_pct').value=s.pa_pct||.1;
    document.getElementById('excess').value=s.excess_lye||.12;document.getElementById('route').value=s.route||'chemical';
    document.getElementById('wax').value=s.wax?'1':'0';document.getElementById('note').textContent='💡 '+s.note||'';document.getElementById('note').style.display='block';
  }catch(e){}
}

function getParams(){return{oil:document.getElementById('oilType').value,mass:parseFloat(document.getElementById('mass').value),av:parseFloat(document.getElementById('av').value),p:parseFloat(document.getElementById('p').value),nhp:parseFloat(document.getElementById('nhp').value),degum:document.getElementById('degum').value,pa_pct:parseFloat(document.getElementById('pa_pct').value),excess:parseFloat(document.getElementById('excess').value),route:document.getElementById('route').value,wax:document.getElementById('wax').value==='1'}}

async function runPareto(){
  if(!validateInputs())return;
  showLoading();updateProgress(0,'帕累托搜索中...');
  try{
    var body=getParams();body.obj='all';body.steps=5;
    var r=await fetch('/api/advanced/pareto',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    if(!r.ok)throw new Error('HTTP '+r.status);
    var d=await r.json();updateProgress(100,'完成!');
    var h='<div class=stage style=border-left:4px solid #8e44ad;margin-top:12px><div class=head style=background:#faf5ff>📊 帕累托多目标优化 · '+d.objective+' · '+d.total_solutions+'组参数 → '+d.pareto_optimal_count+'个最优解</div><div class="body show" style=padding:12px>';
    // Recommended
    if(d.recommended){var rec=d.recommended;h+='<div style=background:#faf5ff;padding:12px;border-radius:8px;margin-bottom:12px><div style=font-weight:700;color:#8e44ad;font-size:14px>🎯 推荐方案: 得率 '+rec.yield+'% | AV '+rec.AV+' | 成本 ¥'+rec.cost+'/t</div><div style=font-size:11px;color:#666;margin-top:4px>'+rec.rationale+'</div><div style=font-size:10px;color:#888;margin-top:4px>参数: PA='+rec.params['PA%']+'% | 超量碱='+rec.params['超量碱%']+'% | 脱臭='+rec.params['脱臭°C']+'°C</div></div>'}
    // Extremes
    if(d.extremes){h+='<div style=display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px>';
      for(var ek in d.extremes){var ex=d.extremes[ek];h+='<div style=background:#faf8f2;padding:10px;border-radius:6px;text-align:center><div style=font-size:10px;color:#8b7a66>'+ek+'</div><div style=font-size:20px;font-weight:700;color:#8e44ad>得率 '+ex.yield+'%</div><div style=font-size:11px;color:#888>AV '+ex.AV+' | ¥'+ex.cost+'/t</div></div>'}
      h+='</div>'}
    // Insights
    if(d.insight){h+='<div style=background:#fef9f0;padding:10px;border-radius:6px;font-size:11px;line-height:1.6>';
      for(var ii=0;ii<d.insight.length;ii++)h+='<div>📌 '+d.insight[ii]+'</div>';h+='</div>'}
    h+='</div></div>';
    document.getElementById('results').insertAdjacentHTML('afterbegin',h);
  }catch(e){alert('帕累托优化失败: '+e.message)}
  hideLoading();
}

function toggleCalibration(){document.getElementById('calibPanel').style.display=document.getElementById('calibPanel').style.display==='none'?'block':'none'}
function runCalibration(){
  if(!currentResult){alert('请先运行模拟');return}
  var o=currentResult.output,deviations=[];
  var actY=parseFloat(document.getElementById('calYield').value),actAV=parseFloat(document.getElementById('calAV').value),actSteam=parseFloat(document.getElementById('calSteam').value),actEarth=parseFloat(document.getElementById('calEarth').value);
  if(actY){var dY=Math.abs(o.yield_pct-actY);deviations.push('得率偏差: |'+o.yield_pct.toFixed(1)+'% - '+actY+'%| = '+dY.toFixed(1)+'个百分点 '+(dY<1?'✅':dY<2?'⚠️':'❌'))}
  if(actAV){var dAV=Math.abs(o.product_av-actAV);deviations.push('AV偏差: |'+o.product_av.toFixed(2)+' - '+actAV+'| = '+dAV.toFixed(3)+' '+(dAV<0.02?'✅':'❌'))}
  if(actSteam){var dS=Math.abs(127-actSteam);deviations.push('蒸汽偏差: |127 - '+actSteam+'| = '+dS.toFixed(0)+' kg/t '+(dS<10?'✅':'❌'))}
  if(actEarth){var dE=Math.abs(1.5-actEarth);deviations.push('白土偏差: |1.5 - '+actEarth+'| = '+dE.toFixed(1)+'% '+(dE<0.3?'✅':'❌'))}
  document.getElementById('calibResult').innerHTML=deviations.length>0?'<div style=font-weight:700;margin-bottom:4px>模型 vs 实测:</div>'+deviations.map(function(d){return '<div>'+d+'</div>'}).join(''):'请至少填入一个实测值';
}

function resetParams(){
  document.getElementById('oilType').value='大豆油';onOilChange();
  document.getElementById('mass').value=100;document.getElementById('av').value=2.0;
  document.getElementById('p').value=800;document.getElementById('nhp').value=0.15;
  document.getElementById('degum').value='acid';document.getElementById('pa_pct').value=0.10;
  document.getElementById('excess').value=0.12;document.getElementById('route').value='chemical';
  document.getElementById('wax').value='0';
}
function toggleSidebar(){
  var sb=document.querySelector('.sidebar');sb.classList.toggle('collapsed');
}
function validateInputs(){
  var mass=parseFloat(document.getElementById('mass').value),av=parseFloat(document.getElementById('av').value),p=parseFloat(document.getElementById('p').value);
  var errors=[];
  if(isNaN(mass)||mass<1||mass>10000)errors.push('批量须在1-10000吨之间');
  if(isNaN(av)||av<0||av>50)errors.push('酸价须在0-50 mgKOH/g之间');
  if(isNaN(p)||p<0||p>5000)errors.push('磷含量须在0-5000 ppm之间');
  if(errors.length>0){alert('输入校验失败:\n'+errors.join('\n'));return false}
  return true;
}
var progressTimer=null;
function showLoading(){var ov=document.getElementById('loadingOverlay');ov.style.display='block';document.getElementById('progressBar').style.width='0%';document.getElementById('loadingPct').textContent='0%';document.getElementById('loadingStage').textContent=tr('connecting');var btn=document.querySelector('.btn-p');btn.disabled=true;btn.textContent=tr('loading')}
function hideLoading(){var ov=document.getElementById('loadingOverlay');ov.style.display='none';clearInterval(progressTimer);var btn=document.querySelector('.btn-p');btn.disabled=false;btn.textContent=tr('run')}
function updateProgress(pct,stage){document.getElementById('progressBar').style.width=pct+'%';document.getElementById('loadingPct').textContent=pct+'%';if(stage)document.getElementById('loadingStage').textContent=stage}

function startProgress(){var st=(T[LANG]||T['zh']).stages||['Degumming...','Neutralizing...','Bleaching...','Deodorizing...','Generating advice...','Loading analytics...'];updateProgress(0,tr('connecting'));var elapsed=0;progressTimer=setInterval(function(){elapsed+=200;
  if(elapsed<1500){updateProgress(Math.min(15,elapsed/1500*15),st[0])}
  else if(elapsed<3000){updateProgress(15+Math.min(25,(elapsed-1500)/1500*25),st[1])}
  else if(elapsed<4500){updateProgress(40+Math.min(25,(elapsed-3000)/1500*25),st[2])}
  else if(elapsed<6000){updateProgress(65+Math.min(20,(elapsed-4500)/1500*25),st[3])}
  else if(elapsed<7500){updateProgress(85+Math.min(10,(elapsed-6000)/1500*10),st[4])}
  else if(elapsed<9000){updateProgress(95+Math.min(5,(elapsed-7500)/1500*5),st[5])}
  else{updateProgress(99,'...')}
},200)}

async function run(){
  if(!validateInputs())return;
  showLoading();startProgress();
  try{var r=await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(getParams())});
    if(!r.ok)throw new Error('HTTP '+r.status);var d=await r.json();currentResult=d;allResults=[d];updateProgress(100,tr('done'));renderResult(d);fetchAdvanced();
  }catch(e){document.getElementById('results').innerHTML='<div class=empty style=color:#c0392b><p style=font-size:18px>⚠ '+tr('run')+'</p><p>'+e.message+'</p></div>'}
  hideLoading();
}

function renderResult(d){
  var o=d.output,adv=d.advisor||{},cost=d.cost||{},stages=d.stages||[],mass=d.input.mass_ton;
  var yieldColor=o.yield_pct>=92?'#27ae60':o.yield_pct>=85?'#2980b9':'#c0392b';
  var avColor=o.product_av<=.08?'#27ae60':o.product_av<=.2?'#e67e22':'#c0392b';

  var h='<div class=kpi-row>';
  h+='<div class=kpi><div class=num style=color:'+yieldColor+'>'+o.yield_pct+'%</div><div class=tag>精炼得率</div></div>';
  h+='<div class=kpi><div class=num>'+(o.total_loss_kg/1000).toFixed(1)+' T</div><div class=tag>总油损 ('+o.total_loss_pct+'%)</div></div>';
  h+='<div class=kpi><div class=num style=color:'+avColor+'>'+o.product_av+'</div><div class=tag>成品酸价 AV</div></div>';
  h+='<div class=kpi><div class=num>R '+o.product_color_r+' / Y '+o.product_color_y+'</div><div class=tag>成品色泽 (罗维朋 1")</div></div>';
  h+='</div>';

  // Sankey
  var colors=['#e67e22','#c0392b','#8e44ad','#2980b9'],losses=[];
  for(var si=0;si<stages.length;si++){var s=stages[si],lp=0,lk=0;
    for(var k in s.results){var vs=String(s.results[k]);
      if(k.indexOf('总油损%')>=0||k.indexOf('总油损_%')>=0)lp=parseFloat(vs.replace('%',''))||0;
      if(k.indexOf('总油损_kg')>=0)lk=parseFloat(vs)||0}
    losses.push({name:s.name,pct:lp,kg:lk/1000})}
  var tLoss=losses.reduce(function(a,b){return a+b.kg},0),prod=mass-tLoss;
  h+='<div class=stage><div class=head onclick="this.nextElementSibling.classList.toggle(\'show\')">📊 物料流向图 · '+mass.toFixed(0)+'T 毛油 → '+prod.toFixed(1)+'T 成品 ▼</div><div class="body show"><div class=sankey>';
  for(var i=0;i<losses.length;i++){var w=losses[i].kg/mass*100;h+='<div style=width:'+w+'%;background:'+colors[i]+' title='+losses[i].name+'>'+losses[i].kg.toFixed(1)+'</div>'}
  h+='<div style=flex:1;background:#27ae60;min-width:55px>成品 '+prod.toFixed(1)+'T</div></div><div style=display:flex;gap:14px;flex-wrap:wrap;font-size:10px;margin-top:6px>';
  for(var i=0;i<losses.length;i++)h+='<span><span style=display:inline-block;width:10px;height:10px;border-radius:2px;background:'+colors[i]+';margin-right:3px></span>'+losses[i].name+': '+losses[i].kg.toFixed(1)+'T ('+losses[i].pct.toFixed(1)+'%)</span>';
  h+='</div><p style="font-size:10px;color:var(--muted);margin-top:4px">油损占比合计: '+(tLoss/mass*100).toFixed(1)+'% | 精炼得率: '+(prod/mass*100).toFixed(1)+'%</p></div></div>';

  // Advisor
  if(adv.findings&&adv.findings.length>0){
    h+='<div class=stage style=border-left:4px solid #e67e22><div class=head style=background:#fef9f0 onclick="this.nextElementSibling.classList.toggle(\'show\')">🔍 工艺优化建议 · '+adv.findings.length+'项 · '+adv.saving_desc+' ▼</div><div class="body show">';
    for(var fi=0;fi<adv.findings.length;fi++){var f=adv.findings[fi];
      var fcolor=f.severity===3?'#c0392b':'#e67e22',fsev=f.severity===3?'🔴 严重':'🟡 需关注';
      h+='<div class=finding style=border-left:3px solid '+fcolor+'><div style=font-weight:700;color:'+fcolor+'>'+fsev+' | '+f.stage+' — '+f.title+'</div><div style=color:#888;font-size:10px;margin:3px 0>📋 根因分析: '+f.cause+'</div><div style=color:#27ae60;font-weight:600>✅ 改进措施: '+f.suggestion+'</div>';
      if(f.savings_breakdown&&f.savings_breakdown.length>0){h+='<div style=margin-top:6px;background:#fff;border-radius:4px;overflow:hidden;border:1px solid #e8e0d0><div style=font-size:10px;font-weight:700;padding:5px 8px;background:#f5efe0>💰 节费拆解 · 合计: '+f.total_saving_desc+'</div>';
        for(var sj=0;sj<f.savings_breakdown.length;sj++){var sb=f.savings_breakdown[sj],amt=sb.amount>=1e4?'¥'+(sb.amount/1e4).toFixed(1)+'万':'¥'+sb.amount.toFixed(0);
          h+='<div class=saving-row><span><span style=background:#e8e0d0;padding:1px 5px;border-radius:3px;font-size:9px;margin-right:4px>'+sb.category+'</span>'+sb.label+'</span><span style=color:#c0392b;font-weight:700>'+amt+'</span></div><div style=font-size:9px;color:#888;padding:1px 8px>'+sb.detail+'</div>'}
        if(f.investment>0)h+='<div style=font-size:10px;padding:4px 8px;background:#fef9f0;font-weight:600>🔧 预计投资: ¥'+(f.investment/1e4).toFixed(1)+'万 | 回收期: '+f.payback_months+'个月</div>';
        h+='</div>'}h+='</div>'}
    if(adv.saving_categories){var cats=adv.saving_categories,catKeys=Object.keys(cats);
      if(catKeys.length>0){h+='<div style=margin-top:8px;padding:12px;background:linear-gradient(135deg,#eaf7ea,#f0fdf0);border-radius:8px;border:1px solid #b8dcb8><div style=font-weight:700;color:#27ae60;font-size:13px>💎 节能增效汇总: '+adv.saving_desc+'</div><div style=display:flex;gap:8px;flex-wrap:wrap;margin-top:6px>';
        for(var ci=0;ci<catKeys.length;ci++){var cat=catKeys[ci],amt=cats[cat];h+='<div style=background:#fff;padding:7px 12px;border-radius:6px;text-align:center;font-size:11px><b style=color:#27ae60>¥'+(amt>=1e4?(amt/1e4).toFixed(1)+'万':amt.toFixed(0))+'</b><br><span style=font-size:9px;color:#7a6e5e>'+cat+'</span></div>'}
        h+='</div></div>'}}h+='</div></div>'}

  // Cost
  var costDetail=cost['加工成本'];
  if(costDetail){var costPerTon=cost['吨油加工成本_元每吨'],marginPerTon=cost['吨油毛利_元每吨'];
    var totalCostVal=cost['总加工成本_元'],byproductVal=cost['副产品总收入_元'],grossMarginVal=cost['加工毛利_元'];
    h+='<div class=stage><div class=head onclick="this.nextElementSibling.classList.toggle(\'show\')">💰 成本核算 · 吨油加工费 ¥'+costPerTon+' | 吨油毛利 ¥'+marginPerTon+' ▼</div><div class=body><table>';
    for(var ck in costDetail)h+='<tr><td>'+ck+'</td><td style=color:#c0392b>¥ '+costDetail[ck].toLocaleString()+'</td></tr>';
    h+='<tr style=font-weight:700;background:#f0f6fb><td>总加工成本</td><td>¥ '+totalCostVal.toLocaleString()+'</td></tr>';
    h+='<tr style=font-weight:700;background:#eaf7ea><td>副产品收入</td><td style=color:#27ae60>+¥ '+byproductVal.toLocaleString()+'</td></tr>';
    h+='<tr style=font-weight:700;background:#eaf7ea;font-size:13px"><td>加工毛利</td><td style=color:#27ae60>¥ '+grossMarginVal.toLocaleString()+'</td></tr>';
    h+='</table></div></div>'}

  // Stage details
  for(var si=0;si<stages.length;si++){var s=stages[si];h+='<div class=stage><div class=head onclick="this.nextElementSibling.classList.toggle(\'show\')">📋 '+s.name+' 详细参数 ▼</div><div class=body><table>';
    for(var k in s.results)h+='<tr><td>'+k+'</td><td>'+s.results[k]+'</td></tr>';h+='</table></div></div>'}
  document.getElementById('results').innerHTML=h;
}

async function fetchAdvanced(){
  if(!currentResult)return;
  var body=getParams();body.mass_ton=body.mass;body.stages=currentResult.stages;
  var fetchJSON=async function(url){try{var r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});if(!r.ok)return null;return await r.json()}catch(e){return null}};
  var results=await Promise.all([fetchJSON('/api/advanced/radar'),fetchJSON('/api/advanced/carbon'),fetchJSON('/api/advanced/chokepoint'),fetchJSON('/api/gb-check'),fetchJSON('/api/byproducts'),fetchJSON('/api/contaminants'),fetchJSON('/api/water-footprint'),fetchJSON('/api/byproduct-params'),fetchJSON('/api/process-sheet'),fetchJSON('/api/benchmark'),fetchJSON('/api/regulatory')]);
  var radar=results[0],carbon=results[1],cp=results[2],gb=results[3],bp=results[4],cm=results[5],wf=results[6],bpp=results[7],ps=results[8],bm=results[9],rg=results[10];
  var block='<div style=display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px>';

  // Radar
  if(radar&&radar.scores){block+='<div class=stage style=border-left:4px solid #8e44ad><div class=head style=background:#faf5ff>📡 五维综合评分 · '+radar.grade+' · '+radar.total_score+'/100 <span style=font-size:10px>经济性/品质/营养保留/食品安全/环保</span></div><div class="body show" style=padding:12px><div style=display:flex;align-items:center;gap:16px;flex-wrap:wrap;justify-content:center><canvas id=radarCanvas width=260 height=260></canvas><div style=font-size:11px>';
    var scores=radar.scores,scoreKeys=Object.keys(scores);
    for(var si=0;si<scoreKeys.length;si++){var sk=scoreKeys[si],sv=scores[sk],sc=sv>=80?'#27ae60':sv>=60?'#2980b9':sv>=40?'#e67e22':'#c0392b';block+='<div style=padding:3px 0><span style=display:inline-block;width:8px;height:8px;border-radius:50%;background:'+sc+';margin-right:6px></span><b>'+sv.toFixed(0)+'</b>/100 — '+sk+'</div>'}
    block+='</div></div>';
    // Detailed plans per dimension
    if(radar.plans){block+='<div style=margin-top:8px;text-align:left>';var plans=radar.plans,planKeys=Object.keys(plans);
      for(var pi=0;pi<planKeys.length;pi++){var pk=planKeys[pi],pv=plans[pk],ps=scores[pk]||0,pc=ps>=80?'#27ae60':ps>=60?'#2980b9':ps>=40?'#e67e22':'#c0392b';
        block+='<details style=margin-bottom:6px;font-size:11px;border:1px solid #e8e0d0;border-radius:4px;padding:6px 8px;border-left:3px solid '+pc+'><summary style=cursor:pointer;font-weight:600>'+pk+' ('+ps.toFixed(0)+'/100)</summary><div style=margin-top:4px;color:#555;line-height:1.6>'+pv+'</div></details>'}
      block+='</div>'}
    block+='</div></div>';pendingRadar=scores}else{block+='<div></div>'}

  // Carbon
  if(carbon){var cfRating=carbon['碳足迹评级']||'?',cfPerTon=parseFloat(carbon['吨油碳足迹_kgCO2每吨']||0).toFixed(0);
    var cfCBAM=carbon['EU_CBAM估算成本_元每批']||0,cfTotal=carbon['合计_kgCO2每批']||0,cfTip=carbon['减排建议']||'',cfDetail=carbon['排放明细']||{};
    block+='<div class=stage style=border-left:4px solid #27ae60><div class=head style=background:#f0fdf0>🌍 碳足迹 · '+cfRating+' · '+cfPerTon+' kg CO₂/t <span style=font-size:10px>EU CBAM预计 ¥'+cfCBAM+'/批</span></div><div class="body show" style=padding:12px;font-size:11px>';
    for(var ck in cfDetail)block+='<div style=display:flex;justify-content:space-between;padding:2px 0;border-bottom:1px solid #f0f8f0><span>'+ck+'</span><span style=font-weight:600>'+cfDetail[ck]+' kgCO₂</span></div>';
    block+='<div style=font-weight:700;padding:4px 0;border-top:2px solid #b8dcb8;margin-top:4px>合计: '+cfTotal+' kgCO₂/批 ('+cfPerTon+' kg/t)</div>';
    if(cfTip)block+='<div style=margin-top:6px;padding:6px;background:#fef9f0;border-radius:4px;font-size:10px>💡 '+cfTip+'</div>';block+='</div></div>'}else{block+='<div></div>'}
  block+='</div>';

  // Supply chain - rigorous version
  if(cp&&cp.items&&cp.items.length>0){block+='<div class=stage style=border-left:4px solid #2980b9;margin-top:12px><div class=head style=background:#f0f6fb>📦 供应链优化 · 进口与国产方案经济对比 <span style=font-size:10px>| 数据来源: 企业公开报价/招标信息/行业调研, 仅供参考</span></div><div class="body show" style=padding:12px;overflow-x:auto>';
    block+='<p style=font-size:10px;color:#888;margin-bottom:8px">⚠ 以下分析基于公开渠道可获取的价格信息。实际采购价格因批量、付款条件、合作年限等因素存在差异。国产替代方案的技术可行性需与供应商逐一确认。建议将本表作为初步筛查工具，具体决策前进行详细的技术经济论证。</p>';
    block+='<table style=font-size:11px;width:100%;min-width:700px><thead><tr style=background:#f0f6fb;font-weight:700><td>优化项目</td><td>进口方案</td><td>国产替代方案</td><td>进口占比(估)</td><td>进口年成本(估)</td><td>国产年成本(估)</td><td>差额</td><td>评估结论</td></tr></thead><tbody>';
    for(var ii=0;ii<cp.items.length;ii++){var item=cp.items[ii],sc=item.annual_saving>0?'#27ae60':'#c0392b';
      var ic=item.annual_cost_import||item.import_price_per_year||0,dc=item.annual_cost_domestic||item.domestic_price_per_year||0,sv=Math.abs(item.annual_saving||0);
      var vsName=(item.foreign_supplier||'').replace(/\(.*/,'').trim();
      var dsName=(item.domestic_alternative||'').replace(/\(.*/,'').trim();
      block+='<tr><td><b>'+vsName+'</b></td><td style=font-size:10px;color:#888>进口品牌</td><td style=font-size:10px>'+dsName+'</td><td style=color:#888>'+item.current_status+'</td><td>¥ '+ic.toLocaleString()+'</td><td>¥ '+dc.toLocaleString()+'</td><td style=color:'+sc+';font-weight:700>¥ '+sv.toLocaleString()+'</td><td style=font-size:10px>'+item.recommendation+'</td></tr>'}
    block+='<tr style=font-weight:700;background:#f0f6fb;font-size:12px"><td colspan=6>全部采纳后年度差额合计(仅作量级参考)</td><td style=color:#27ae60>约 ¥ '+(cp.total_annual_saving||0).toLocaleString()+'/年</td><td></td></tr></tbody></table>';
    block+='<p style=font-size:9px;color:#aaa;margin-top:6px">注: ①进口/国产价格取自2024-2026年公开报价及招标信息；②年成本基于标准工况(300天/年)估算,实际开工率可能不同；③差额包含设备折旧、维护、能耗及油损等全生命周期因素；④部分国产方案仍处于产业化早期或中试阶段,大规模应用前需实测验证。</p></div></div>'}

  // GB compliance
  if(gb&&gb.grade){block+='<div class=stage style=border-left:4px solid '+(gb.grade==='一级'?'#27ae60':gb.grade==='二级'?'#2980b9':gb.grade==='三级'?'#e67e22':'#c0392b')+';margin-top:12px><div class=head onclick="this.nextElementSibling.classList.toggle(\'show\')">🏷 国标合规 · '+gb.verdict+'</div><div class=body style=padding:12px><table>';for(var gk in gb.details){var gd=gb.details[gk];block+='<tr><td style=color:'+(gd.passed?'#27ae60':'#c0392b')+';font-weight:700>'+(gd.passed?'✅':'❌')+' '+gk+'</td><td style=font-size:11px>'+gd.checks.join(' | ')+'</td></tr>'}block+='</table></div></div>'}
  // Byproducts
  if(bp&&bp.items){block+='<div class=stage style=border-left:4px solid #c8963e;margin-top:12px><div class=head style=background:#fef9ee onclick="this.nextElementSibling.classList.toggle(\'show\')">🛢 副产物深加工 · '+bp.total_gain_desc+'</div><div class=body style=padding:12px><table style=font-size:11px><tr style=font-weight:700><td>项目</td><td>当前方案</td><td>深加工方案</td><td>批增收</td></tr>';for(var bi=0;bi<bp.items.length;bi++){var b=bp.items[bi];block+='<tr><td>'+b.name+'</td><td>'+b.current+'</td><td>'+b.upgraded+'</td><td style=color:#27ae60;font-weight:700>+¥'+b.net_gain.toLocaleString()+'</td></tr>'}block+='</table></div></div>'}

  try{if(typeof renderPanels==='function')block+=renderPanels(cm,wf,bpp,bp,ps,bm,rg)}catch(e){console.error('Panels error:',e);block+='<div class=stage style=border-left:4px solid #c0392b;margin-top:12px><div class=head>Panel Error</div><div class="body show">'+e.message+'</div></div>'}
  document.getElementById('results').insertAdjacentHTML('beforeend',block);
  setTimeout(drawRadarIfReady,300);
}

function drawRadarIfReady(){
  if(!pendingRadar)return;var c=document.getElementById('radarCanvas');if(!c)return;
  var ctx=c.getContext('2d'),cx=130,cy=130,r=105,keys=Object.keys(pendingRadar),n=keys.length,labels=['经济性','品质','营养保留','食品安全','环保'];
  ctx.clearRect(0,0,260,260);
  for(var i=5;i>=1;i--){ctx.beginPath();for(var j=0;j<n;j++){var a=-Math.PI/2+j*2*Math.PI/n,rr=r*i/5;ctx[j===0?'moveTo':'lineTo'](cx+rr*Math.cos(a),cy+rr*Math.sin(a))}ctx.closePath();ctx.strokeStyle=i===5?'rgba(0,0,0,.12)':'rgba(0,0,0,.04)';ctx.stroke();ctx.fillStyle='rgba(250,245,240,'+(i*.04)+')';ctx.fill()}
  for(var j=0;j<n;j++){var a=-Math.PI/2+j*2*Math.PI/n;ctx.beginPath();ctx.moveTo(cx,cy);ctx.lineTo(cx+r*Math.cos(a),cy+r*Math.sin(a));ctx.strokeStyle='rgba(0,0,0,.08)';ctx.stroke();ctx.fillStyle='#7a6e5e';ctx.font='10px Microsoft YaHei';ctx.textAlign='center';ctx.fillText(labels[j],cx+(r+16)*Math.cos(a),cy+(r+16)*Math.sin(a))}
  ctx.beginPath();for(var j=0;j<n;j++){var a=-Math.PI/2+j*2*Math.PI/n,rr=r*Math.max(.05,pendingRadar[keys[j]]/100);ctx[j===0?'moveTo':'lineTo'](cx+rr*Math.cos(a),cy+rr*Math.sin(a))}ctx.closePath();ctx.fillStyle='rgba(142,68,173,.12)';ctx.fill();ctx.strokeStyle='#8e44ad';ctx.lineWidth=2.5;ctx.stroke();
  for(var j=0;j<n;j++){var a=-Math.PI/2+j*2*Math.PI/n,rr=r*Math.max(.05,pendingRadar[keys[j]]/100);ctx.beginPath();ctx.arc(cx+rr*Math.cos(a),cy+rr*Math.sin(a),4,0,2*Math.PI);ctx.fillStyle='#8e44ad';ctx.fill();ctx.fillStyle='#fff';ctx.font='bold 8px Microsoft YaHei';ctx.textAlign='center';ctx.fillText(pendingRadar[keys[j]].toFixed(0),cx+rr*Math.cos(a),cy+rr*Math.sin(a)-8)}
  pendingRadar=null;
}

async function autoOptimize(){
  var body=getParams();
  try{var r=await fetch('/api/optimize',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),d=await r.json();
  if(d.degum_suggestion)document.getElementById('degum').value=d.degum_suggestion;document.getElementById('pa_pct').value=d.optimized.pa_pct;document.getElementById('excess').value=d.optimized.excess_lye;document.getElementById('route').value=d.optimized.route;document.getElementById('wax').value=d.optimized.wax?'1':'0';
  if(d.changes&&d.changes.length>0){var m='已优化 '+d.changes.length+' 项参数:\n';for(var i=0;i<d.changes.length;i++){var c=d.changes[i];m+='• '+c.param+': '+c.current+' → '+c.optimized+'\n  影响: '+c.impact+'\n'}alert(m)}run()}catch(e){alert('优化失败: '+e.message)}
}

function saveScenario(){if(!currentResult){alert('请先运行模拟');return}var p=getParams();savedScenarios.push({name:p.oil+' | AV:'+p.av+' P:'+p.p,params:p,result:currentResult});renderSidebar()}
function loadScenario(i){var s=savedScenarios[i];document.getElementById('oilType').value=s.params.oil;document.getElementById('mass').value=s.params.mass;document.getElementById('av').value=s.params.av;document.getElementById('p').value=s.params.p;document.getElementById('nhp').value=s.params.nhp;document.getElementById('degum').value=s.params.degum;document.getElementById('pa_pct').value=s.params.pa_pct;document.getElementById('excess').value=s.params.excess;currentResult=s.result;renderResult(s.result)}
function renderSidebar(){if(!savedScenarios.length){document.getElementById('scenarioList').innerHTML='<div style=padding:14px;font-size:11px;color:#ccc;text-align:center>暂无</div>';return}var h='';for(var i=0;i<savedScenarios.length;i++){var s=savedScenarios[i];h+='<div class=item onclick=loadScenario('+i+') style=cursor:pointer><span>'+(s.name||'').substring(0,20)+'</span><span class=badge>'+s.result.output.yield_pct+'%</span></div>'}document.getElementById('scenarioList').innerHTML=h}
async function exportCSV(){if(!currentResult){alert('请先运行');return}var r=await fetch('/api/export/csv',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(currentResult)}),b=await r.blob(),a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='精炼模拟报告.csv';a.click()}
