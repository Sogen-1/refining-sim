function renderPanels(cm,wf,bpp,bp,ps){
  var block='';

  // Contaminants
  if(cm&&cm.GE){
    var geVal=cm.GE.GE_预估含量_mg_per_kg;
    var geOK=String(cm.GE.普通食品合规).indexOf('达标')>=0;
    var mcpdVal=cm.MCPD['3MCPDE_预估含量_mg_per_kg'];
    var mcpdOK=String(cm.MCPD.合规判定).indexOf('✅')>=0;
    var bapVal=cm.PAHs.苯并芘残留_μg_per_kg;
    var bapKey='合规判定(≤10μg/kg)';
    var bapOK=String(cm.PAHs[bapKey]).indexOf('✅')>=0;
    var geColor=geOK?'#27ae60':'#c0392b';
    var mcpdColor=mcpdOK?'#27ae60':'#c0392b';
    var bapColor=bapOK?'#27ae60':'#c0392b';
    block+='<div class=stage style=border-left:4px solid #e74c3c;margin-top:12px><div class=head style=background:#fff5f5 onclick="this.nextElementSibling.classList.toggle(\'show\')">🔬 食品安全 · GE: '+cm.GE.风险等级+' | 3-MCPDE: '+cm.MCPD.合规判定+' | BaP: '+cm.PAHs[bapKey]+'</div><div class="body show" style=padding:12px><table style=font-size:11px><tr style=font-weight:700><td>污染物</td><td>预估值</td><td>合规</td><td>减缓措施</td></tr>';
    block+='<tr><td>缩水甘油酯(GE)</td><td>'+geVal+' mg/kg</td><td style=color:'+geColor+'>'+cm.GE.普通食品合规+'</td><td style=font-size:10px>'+cm.GE.减缓措施.join('; ')+'</td></tr>';
    block+='<tr><td>3-MCPDE</td><td>'+mcpdVal+' mg/kg</td><td style=color:'+mcpdColor+'>'+cm.MCPD.合规判定+'</td><td style=font-size:10px>'+cm.MCPD.关键控制点+'</td></tr>';
    block+='<tr><td>苯并芘(PAHs)</td><td>'+bapVal+' μg/kg</td><td style=color:'+bapColor+'>'+cm.PAHs[bapKey]+'</td><td style=font-size:10px>'+cm.PAHs.优化建议+'</td></tr>';
    block+='</table></div></div>';
  }

  // Water footprint
  if(wf&&wf['新鲜水用量_吨每批']!==undefined){
    block+='<div class=stage style=border-left:4px solid #3498db;margin-top:12px><div class=head onclick="this.nextElementSibling.classList.toggle(\'show\')">💧 水足迹 · 新鲜水 '+wf['新鲜水用量_吨每批']+' T/批 | COD '+wf['废水COD_预估_mg每L']+' mg/L | '+wf['排放合规(GB 8978)']+'</div><div class="body show" style=padding:12px><table style=font-size:11px>';
    var wfKeys=['新鲜水用量_吨每批','含冷却水总用量_吨每批','废水产生量_m3每批','废水COD_预估_mg每L','废水中磷_预估_mg每L'];
    for(var i=0;i<wfKeys.length;i++){var k=wfKeys[i];block+='<tr><td>'+k+'</td><td>'+wf[k]+'</td></tr>'}
    block+='</table></div></div>';
  }

  // Byproduct process params
  if(bpp){
    block+='<div class=stage style=border-left:4px solid #c8963e;margin-top:12px><div class=head style=background:#fef9ee onclick="this.nextElementSibling.classList.toggle(\'show\')">🛢 副产物深加工工艺参数</div><div class="body show" style=padding:12px>';
    for(var bn in bpp){var bd=bpp[bn];
      block+='<div style=margin-bottom:12px;font-size:11px><b>'+bn+' → '+bd.目标产品+'</b><br>路线: '+bd.工艺路线+'<br>收率: '+bd.收率+' | 投资: '+bd.投资估算_万元+'<br><table style=font-size:10px;margin-top:4px>';
      for(var pk in bd.操作参数)block+='<tr><td>'+pk+'</td><td>'+bd.操作参数[pk]+'</td></tr>';
      block+='</table></div>';
    }
    block+='</div></div>';
  }

  // Process sheet
  if(ps&&ps.工段参数){
    block+='<div class=stage style=border-left:4px solid #8e44ad;margin-top:12px><div class=head style=background:#faf5ff onclick="this.nextElementSibling.classList.toggle(\'show\')">📋 标准工艺单 · 可直接交付DCS工程师</div><div class="body show" style=padding:12px;font-size:11px>';
    for(var stg in ps.工段参数){var stgd=ps.工段参数[stg];
      block+='<div style=margin-bottom:8px><b>'+stg+'</b><table style=font-size:10px>';
      for(var pk in stgd){var pv=stgd[pk];if(typeof pv==='object')pv=pv.设定值+((pv.范围)?' ('+pv.范围+')':'');block+='<tr><td>'+pk+'</td><td>'+pv+'</td></tr>'}
      block+='</table></div>';
    }
    block+='<div style=background:#faf5ff;padding:8px;border-radius:4px;font-size:10px;margin-top:8px><b>约束条件:</b><br>'+ps.约束条件.join('<br>')+'</div></div></div>';
  }

  return block;
}
