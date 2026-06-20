from pathlib import Path
p=Path('/vol1/@appcenter/vehicle-mgr/后端/后台管理/index.html')
s=p.read_text(encoding='utf-8')

over=r'''

// ===== 维修流程撤回/退回 =====
function statusText3(s){
  var m={dispatched:'已派单',accepted:'已接单',submitted:'已提交明细',in_progress:'维修中',completed:'已完成',verified:'已验收',rejected:'已驳回',cancelled:'已撤回'};
  return m[s]||s;
}
function canRollback(order){
  var u=getU();if(!u)return null;
  var r=u.role;
  if(order.status==='dispatched'&&(r==='admin'||r==='fleet_manager'||r==='manager'||r==='dispatcher'))return 'cancel';
  if(order.status==='accepted'&&r==='repair_shop'&&order.assigned_to===u.id)return 'reject';
  if(order.status==='submitted'&&r==='repair_shop'&&order.assigned_to===u.id)return 'withdraw';
  if(order.status==='completed'&&(r==='admin'||r==='fleet_manager'||r==='manager'||r==='dispatcher'))return 'sendback';
  if(order.status==='verified'&&(r==='admin'||r==='fleet_manager'||r==='manager'||r==='dispatcher'))return 'reverify';
  return null;
}
function rollbackReasonDialog(action, id){
  var labels={cancel:'撤回原因',reject:'退回原因',withdraw:'撤回原因',sendback:'退回原因',reverify:'撤回原因'};
  var d=document.createElement('div');
  d.innerHTML='<div class="modal-overlay"><div class="modal-content" style="width:460px;"><h3>'+(labels[action]||'原因')+'</h3><div class="form-group"><label>请填写原因</label><textarea id="rbReason" rows="3" style="width:100%;"></textarea></div><div style="text-align:right;margin-top:16px;"><button class="btn btn-secondary" onclick="clo()">取消</button><button class="btn btn-danger" onclick="doRollback(\''+action+'\','+id+'\')" style="margin-left:8px;">确认</button></div></div></div>';
  document.body.appendChild(d.firstElementChild);
}
function doRollback(action, id){
  var reason=document.getElementById('rbReason').value.trim();
  if(!reason){toast('请填写原因',1);return}
  api('PUT','/api/repairs/'+id+'/'+action,{reason:reason}).then(function(r){
    clo();toast((r.msg||'操作成功'));
    loadRep();
    if(vid){viewRep(vid)}
  }).catch(function(e){toast('失败: '+e.message,1)});
}
var vid=null;
function viewRep(id){
  vid=id;
  api('GET','/api/repairs/'+id).then(function(v){
    var u=getU();
    var rb=canRollback(v);
    var rbLabels={cancel:'撤回派单',reject:'退回派单',withdraw:'撤回明细',sendback:'退回重做',reverify:'撤回验收'};
    var rbHtml=rb?'<button class="btn btn-danger" onclick="rollbackReasonDialog(\''+rb+'\','+v.id+')" style="margin-left:12px;">'+(rbLabels[rb]||'撤回/退回')+'</button>':'';
    var reasonHtml=v.rollback_reason?'<div style="background:#5C2A2A;border-radius:4px;padding:10px;font-size:13px;margin-top:12px;color:#EF9A9A;"><strong>最近撤回/退回原因：</strong>'+esc(v.rollback_reason)+'</div>':'';
    var detailHtml='';
    if(v.details&&v.details.length){detailHtml='<table><tr><th>配件</th><th>型号/说明</th><th>费用</th><th>质保</th><th>提醒</th></tr>';for(var i=0;i<v.details.length;i++){var it=v.details[i];detailHtml+='<tr><td>'+esc(it.item_name)+'</td><td>'+esc(it.item_desc||'')+'</td><td>'+(it.cost||0)+'</td><td>'+(it.warranty_days||0)+'天</td><td style="color:'+(it.contract_warning?'#EF9A9A':'#81C784')+'">'+(it.contract_warning||'合同内')+'</td></tr>'}detailHtml+='</table>'}else detailHtml='<p style="color:#777;">暂无维修明细</p>';
    var dispatchPhotos=(v.dispatch_photos||[]).length?JSON.parse(typeof v.dispatch_photos==='string'?v.dispatch_photos:'[]'):[];
    var acceptPhotos=(v.accept_photos||[]).length?JSON.parse(typeof v.accept_photos==='string'?v.accept_photos:'[]'):[];
    var verifyPhotos=(v.verify_photos||[]).length?JSON.parse(typeof v.verify_photos==='string'?v.verify_photos:'[]'):[];
    var photosHtml='';
    function renderPhotos(photos,label){if(!photos.length)return '';var h='<div style="margin-top:8px;font-size:13px;color:#888;">'+label+'</div><div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:4px;">';for(var i=0;i<photos.length;i++){var p=typeof photos[i]==='string'?{url:photos[i],desc:''}:photos[i];h+='<a href="'+esc(p.url)+'" target="_blank"><img src="'+esc(p.url)+'" style="width:80px;height:80px;object-fit:cover;border-radius:4px;"></a>'}return h+'</div>'}
    photosHtml=renderPhotos(dispatchPhotos,'OA审批截图')+renderPhotos(acceptPhotos,'车辆照片')+renderPhotos(verifyPhotos,'I8验收截图');
    var d=document.createElement('div');
    d.innerHTML='<div class="modal-overlay"><div class="modal-content" style="width:680px;"><h3>维修单详情</h3>'+
    '<div style="font-size:14px;line-height:2;">'+
    '<strong>#'+v.id+'</strong> | 车牌：'+esc(v.plate_number||'')+' | 车型：'+esc(v.vehicle_model||'')+' | 维修厂：'+esc(v.shop_name||'')+'<br/>'+
    '状态：<span class="tag tag-'+v.status+'">'+statusText3(v.status)+'</span> | 创建：'+(v.created_at||'')+'</div>'+
    reasonHtml+
    '<div style="background:#2A2A3E;border-radius:4px;padding:10px;font-size:13px;margin-top:12px;">'+(v.description||'-')+'</div>'+
    '<div style="margin-top:12px;font-size:13px;"><strong>维修明细：</strong></div>'+detailHtml+
    photosHtml+
    '<div style="text-align:right;margin-top:16px;">'+
    (v.status==='dispatched'&&u.role!=='repair_shop'?'<button class="btn btn-primary" onclick="acceptRep('+v.id+')" style="margin-right:8px;">确认接单</button>':'')+
    rbHtml+
    '<button class="btn btn-secondary" onclick="clo()">关闭</button></div></div></div>';
    document.body.appendChild(d.firstElementChild);
  }).catch(function(e){toast('加载失败: '+e.message,1)});
}
function acceptRep(id){api('PUT','/api/repairs/'+id+'/accept',{accept_photos:'[]',notes:''}).then(function(){toast('接单成功');loadRep();viewRep(id)}).catch(function(e){toast('失败: '+e.message,1)})}
function showDetailForm(id){var rows='<div id="partRows"><div class="card" style="background:#2A2A3E;"><div class="form-group"><label>配件名称</label><input class="pn" /></div><div class="form-group"><label>型号/规格</label><input class="pm" /></div><div class="form-group"><label>费用/单价</label><input class="pc" type="number" value="0" /></div><div class="form-group"><label>质保天数</label><input class="pw" type="number" value="0" /></div></div></div>';var d=document.createElement('div');d.innerHTML='<div class="modal-overlay"><div class="modal-content" style="width:680px;"><h3>填写维修明细</h3>'+rows+'<button class="btn btn-secondary" onclick="addPartRow()">+ 增加配件</button><div class="form-group" style="margin-top:12px;"><label>车辆照片</label><input type="file" id="detailPhotos" multiple accept="image/*" /></div><div style="text-align:right;margin-top:16px;"><button class="btn btn-secondary" onclick="clo()">取消</button><button class="btn btn-primary" onclick="submitDetails('+id+')" style="margin-left:8px;">提交明细</button></div></div></div>';document.body.appendChild(d.firstElementChild)}
function addPartRow(){var box=document.querySelector('#partRows');var div=document.createElement('div');div.className='card';div.style.background='#2A2A3E';div.innerHTML='<div class="form-group"><label>配件名称</label><input class="pn" /></div><div class="form-group"><label>型号/规格</label><input class="pm" /></div><div class="form-group"><label>费用/单价</label><input class="pc" type="number" value="0" /></div><div class="form-group"><label>质保天数</label><input class="pw" type="number" value="0" /></div>';box.appendChild(div)}
function submitDetails(id){var rows=document.querySelectorAll('#partRows .card');var items=[];for(var i=0;i<rows.length;i++){var n=rows[i].querySelector('.pn').value.trim();if(!n)continue;items.push({item_name:n,part_model:rows[i].querySelector('.pm').value.trim(),cost:parseFloat(rows[i].querySelector('.pc').value)||0,warranty_days:parseInt(rows[i].querySelector('.pw').value)||0})}if(!items.length){toast('请至少填写一个配件',1);return}uploadFiles('detailPhotos').then(function(photos){return api('PUT','/api/repairs/'+id+'/details',{items:items,photos:photos})}).then(function(){clo();toast('明细已提交');loadRep();viewRep(id)}).catch(function(e){toast('失败: '+e.message,1)})}
function compRep(id){api('PUT','/api/repairs/'+id+'/complete',{}).then(function(){toast('已标记完成');loadRep();viewRep(id)}).catch(function(e){toast('失败: '+e.message,1)})}
function showVerifyForm(id){var d=document.createElement('div');d.innerHTML='<div class="modal-overlay"><div class="modal-content"><h3>验收维修单</h3><div class="form-group"><label>内部I8流程截图</label><input type="file" id="verifyPhotos" multiple accept="image/*" /></div><div class="form-group"><label>验收备注</label><textarea id="verifyNotes" rows="3"></textarea></div><div style="text-align:right;margin-top:16px;"><button class="btn btn-secondary" onclick="clo()">取消</button><button class="btn btn-primary" onclick="submitVerify('+id+')" style="margin-left:8px;">验收通过</button></div></div></div>';document.body.appendChild(d.firstElementChild)}
function submitVerify(id){uploadFiles('verifyPhotos').then(function(photos){return api('PUT','/api/repairs/'+id+'/verify',{verify_photos:photos,notes:document.getElementById('verifyNotes').value})}).then(function(){clo();toast('验收完成');loadRep()}).catch(function(e){toast('失败: '+e.message,1)})}
'''
s=s.replace('\n</script>','\n'+over+'\n</script>')
p.write_text(s,encoding='utf-8')
print('repair rollback frontend patched')
