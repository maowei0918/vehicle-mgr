from pathlib import Path
p=Path('/vol1/@appcenter/vehicle-mgr/后端/后台管理/index.html')
s=p.read_text(encoding='utf-8')
over=r'''

// ===== 维修流程增强：OA/I8截图、修理厂明细、合同配件 =====
function esc(s){return String(s||'').replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function statusText2(s){var m={dispatched:'已派单',accepted:'已接单',submitted:'已提交明细',in_progress:'维修中',completed:'已完成',verified:'已验收',rejected:'已驳回'};return m[s]||sn(s)}
function uploadOne(file){var fd=new FormData();fd.append('file',file);return fetch(B+'/api/inspections/upload',{method:'POST',headers:{'Authorization':'Bearer '+T},body:fd}).then(function(r){if(!r.ok)throw new Error('上传失败');return r.json()}).then(function(d){return d.url})}
function uploadFiles(inputId){var el=document.getElementById(inputId);var fs=el&&el.files?Array.prototype.slice.call(el.files):[];var chain=Promise.resolve([]);fs.forEach(function(f){chain=chain.then(function(arr){return uploadOne(f).then(function(url){arr.push({url:url,desc:f.name});return arr})})});return chain.then(function(arr){return JSON.stringify(arr)})}

function page_contract(el){
  el.innerHTML='<div class="page-title">📦 合同配件明细</div>'+ 
    '<div class="card"><div class="filter-bar"><div class="form-group"><label>搜索配件</label><input id="cpq" placeholder="配件名称" /></div><button class="btn btn-primary" onclick="loadContractParts()">查询</button><button class="btn btn-primary" onclick="showContractPartForm()">+ 添加配件</button><button class="btn btn-secondary" onclick="showContractImport()">Excel导入</button></div></div>'+ 
    '<div class="card" id="cpw"><p class="loading">加载中...</p></div>';
  loadContractParts();
}
function loadContractParts(){var q=document.getElementById('cpq')?document.getElementById('cpq').value:'';api('GET','/api/contract-parts'+(q?'?q='+encodeURIComponent(q):'')).then(function(items){var h='<table><tr><th>ID</th><th>修理厂ID</th><th>配件名称</th><th>型号</th><th>合同价</th><th>质保天数</th><th>备注</th><th>操作</th></tr>';for(var i=0;i<items.length;i++){var x=items[i];h+='<tr><td>'+x.id+'</td><td>'+(x.shop_id||'')+'</td><td>'+esc(x.part_name)+'</td><td>'+esc(x.part_model)+'</td><td>'+x.contract_price+'</td><td>'+x.warranty_days+'</td><td>'+esc(x.notes)+'</td><td><button class="btn btn-sm btn-secondary" onclick="showContractPartForm('+x.id+')">编辑</button><button class="btn btn-sm btn-danger" onclick="delContractPart('+x.id+')">删除</button></td></tr>'}h+='</table>';if(!items.length)h='<p style="text-align:center;padding:20px;color:#555;">暂无数据</p>';document.getElementById('cpw').innerHTML=h})}
function showContractPartForm(id){var load=id?api('GET','/api/contract-parts').then(function(a){return a.find(function(x){return x.id===id})||{}}):Promise.resolve({});load.then(function(x){loadShopOptions(x.shop_id,function(shops){var d=document.createElement('div');d.innerHTML='<div class="modal-overlay"><div class="modal-content"><h3>'+(id?'编辑':'添加')+'合同配件</h3><div class="form-group"><label>修理厂</label><select id="cp1">'+shops+'</select></div><div class="form-group"><label>配件名称 *</label><input id="cp2" value="'+esc(x.part_name||'')+'" /></div><div class="form-group"><label>型号</label><input id="cp3" value="'+esc(x.part_model||'')+'" /></div><div class="form-group"><label>合同价</label><input id="cp4" type="number" value="'+(x.contract_price||0)+'" /></div><div class="form-group"><label>质保天数</label><input id="cp5" type="number" value="'+(x.warranty_days||0)+'" /></div><div class="form-group"><label>备注</label><input id="cp6" value="'+esc(x.notes||'')+'" /></div><div style="text-align:right;margin-top:16px;"><button class="btn btn-secondary" onclick="clo()">取消</button><button class="btn btn-primary" onclick="saveContractPart('+(id||0)+')" style="margin-left:8px;">保存</button></div></div></div>';document.body.appendChild(d.firstElementChild)})})}
function saveContractPart(id){var shop=document.getElementById('cp1').value;var d={shop_id:shop?parseInt(shop):null,part_name:document.getElementById('cp2').value,part_model:document.getElementById('cp3').value,contract_price:parseFloat(document.getElementById('cp4').value)||0,warranty_days:parseInt(document.getElementById('cp5').value)||0,notes:document.getElementById('cp6').value};if(!d.part_name){toast('请输入配件名称',1);return}api(id?'PUT':'POST','/api/contract-parts'+(id?'/'+id:''),d).then(function(){clo();toast('保存成功');loadContractParts()}).catch(function(e){toast('失败: '+e.message,1)})}
function delContractPart(id){if(!confirm('确定删除该合同配件？'))return;api('DELETE','/api/contract-parts/'+id).then(function(){toast('删除成功');loadContractParts()}).catch(function(e){toast('失败: '+e.message,1)})}
function showContractImport(){var d=document.createElement('div');d.innerHTML='<div class="modal-overlay"><div class="modal-content"><h3>导入合同配件</h3><p style="color:#888;font-size:13px;">Excel列：修理厂ID、配件名称、型号、合同价、质保天数、备注</p><input type="file" id="cpf" accept=".xlsx,.xls" /><div style="text-align:right;margin-top:16px;"><button class="btn btn-secondary" onclick="clo()">取消</button><button class="btn btn-primary" onclick="doContractImport()" style="margin-left:8px;">导入</button></div></div></div>';document.body.appendChild(d.firstElementChild)}
function doContractImport(){var f=document.getElementById('cpf').files[0];if(!f){toast('请选择文件',1);return}var fd=new FormData();fd.append('file',f);fetch(B+'/api/contract-parts/import/xlsx',{method:'POST',headers:{'Authorization':'Bearer '+T},body:fd}).then(function(r){if(!r.ok)throw new Error('导入失败');return r.json()}).then(function(x){clo();toast('导入完成：'+x.imported+'条');loadContractParts()}).catch(function(e){toast('失败: '+e.message,1)})}

// 覆盖页面切换，增加合同配件页
var _oldGoPage=goPage;
goPage=function(n,el){var a=document.querySelectorAll('.sidebar a');for(var i=0;i<a.length;i++)a[i].classList.remove('active');if(el)el.classList.add('active');var m=document.getElementById('mc');if(n==='contract')page_contract(m);else _oldGoPage(n,el)};
(function(){var side=document.querySelector('.sidebar .spacer');if(side&&!document.getElementById('nav-cp')){var a=document.createElement('a');a.id='nav-cp';a.onclick=function(){goPage('contract',a)};a.innerHTML='📦 合同配件';side.parentNode.insertBefore(a,side)}})();

function showRepForm(){
  loadVehicleOptions('',function(vehicles){loadShopOptions('',function(shops){
    var d=document.createElement('div');
    d.innerHTML='<div class="modal-overlay"><div class="modal-content" style="width:560px;"><h3>发起维修单</h3>'+ 
    '<div class="form-group"><label>车辆 *</label><select id="r1">'+vehicles+'</select></div>'+ 
    '<div class="form-group"><label>汽修厂 *</label><select id="r2">'+shops+'</select></div>'+ 
    '<div class="form-group"><label>故障描述</label><textarea id="r3" rows="3"></textarea></div>'+ 
    '<div class="form-group"><label>内部OA审批截图</label><input type="file" id="r4" multiple accept="image/*" /></div>'+ 
    '<div style="text-align:right;margin-top:16px;"><button class="btn btn-secondary" onclick="clo()">取消</button><button class="btn btn-primary" onclick="doAddRep()" style="margin-left:8px;">发单</button></div></div></div>';
    document.body.appendChild(d.firstElementChild);
  })})
}
function doAddRep(){
  var plate=document.getElementById('r1').value, shop=parseInt(document.getElementById('r2').value)||0;
  if(!plate||!shop){toast('请选择车辆和汽修厂',1);return}
  uploadFiles('r4').then(function(photos){return api('POST','/api/repairs',{plate_number:plate,shop_id:shop,description:document.getElementById('r3').value,dispatch_photos:photos})}).then(function(){clo();toast('发单成功');loadRep()}).catch(function(e){toast('失败: '+e.message,1)});
}
function viewRep(id){
  api('GET','/api/repairs/'+id).then(function(v){
    var detailHtml='';
    if(v.details&&v.details.length){detailHtml='<table><tr><th>配件</th><th>型号/说明</th><th>费用</th><th>质保</th><th>提醒</th></tr>';for(var i=0;i<v.details.length;i++){var it=v.details[i];detailHtml+='<tr><td>'+esc(it.item_name)+'</td><td>'+esc(it.item_desc)+'</td><td>'+it.cost+'</td><td>'+it.warranty_days+'天</td><td style="color:'+(it.contract_warning?'#EF9A9A':'#81C784')+'">'+(it.contract_warning||'合同内')+'</td></tr>'}detailHtml+='</table>'}else detailHtml='<p style="color:#777;">暂无维修明细</p>';
    var btn='';
    if(v.status==='dispatched')btn+='<button class="btn btn-primary" onclick="acceptRep('+v.id+')" style="margin-right:8px;">修理厂接单</button>';
    if(v.status==='accepted'||v.status==='submitted'||v.status==='in_progress')btn+='<button class="btn btn-primary" onclick="showDetailForm('+v.id+')" style="margin-right:8px;">填写/修改维修明细</button><button class="btn btn-primary" onclick="compRep('+v.id+')" style="margin-right:8px;">标记完成</button>';
    if(v.status==='completed')btn+='<button class="btn btn-primary" onclick="showVerifyForm('+v.id+')" style="margin-right:8px;">验收</button>';
    var d=document.createElement('div');
    d.innerHTML='<div class="modal-overlay"><div class="modal-content" style="width:760px;"><h3>维修单 #'+v.id+'</h3>'+ 
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;font-size:13px;"><div><strong>车牌号：</strong>'+esc(v.plate_number)+'</div><div><strong>汽修厂：</strong>'+esc(v.shop_name||'')+'</div><div><strong>状态：</strong><span class="tag tag-'+v.status+'">'+statusText2(v.status)+'</span></div><div><strong>创建时间：</strong>'+(v.created_at||'')+'</div></div>'+ 
      '<div style="margin-top:12px;font-size:13px;"><strong>故障描述：</strong></div><div style="background:#2A2A3E;border-radius:4px;padding:10px;margin-top:4px;">'+esc(v.description||'-')+'</div>'+ 
      '<div style="margin-top:12px;font-size:13px;"><strong>维修配件明细：</strong></div><div style="background:#2A2A3E;border-radius:4px;padding:10px;margin-top:4px;max-height:260px;overflow:auto;">'+detailHtml+'</div>'+ 
      '<div style="margin-top:12px;color:#888;font-size:12px;">OA截图数量：'+((v.dispatch_photos||[]).length||0)+'；车辆照片数量：'+((v.accept_photos||[]).length||0)+'；I8截图数量：'+((v.verify_photos||[]).length||0)+'</div>'+ 
      '<div style="text-align:right;margin-top:16px;">'+btn+'<button class="btn btn-secondary" onclick="clo()">关闭</button></div></div></div>';
    document.body.appendChild(d.firstElementChild);
  }).catch(function(e){toast('加载失败: '+e.message,1)})
}
function acceptRep(id){api('PUT','/api/repairs/'+id+'/accept',{accept_photos:'[]',notes:''}).then(function(){clo();toast('接单成功');loadRep();viewRep(id)}).catch(function(e){toast('失败: '+e.message,1)})}
function showDetailForm(id){var rows='<div id="partRows"><div class="card" style="background:#2A2A3E;"><div class="form-group"><label>配件名称</label><input class="pn" /></div><div class="form-group"><label>型号/规格</label><input class="pm" /></div><div class="form-group"><label>费用/单价</label><input class="pc" type="number" value="0" /></div><div class="form-group"><label>质保天数</label><input class="pw" type="number" value="0" /></div></div></div>';var d=document.createElement('div');d.innerHTML='<div class="modal-overlay"><div class="modal-content" style="width:680px;"><h3>填写维修明细</h3>'+rows+'<button class="btn btn-secondary" onclick="addPartRow()">+ 增加配件</button><div class="form-group" style="margin-top:12px;"><label>车辆照片</label><input type="file" id="detailPhotos" multiple accept="image/*" /></div><div style="text-align:right;margin-top:16px;"><button class="btn btn-secondary" onclick="clo()">取消</button><button class="btn btn-primary" onclick="submitDetails('+id+')" style="margin-left:8px;">提交明细</button></div></div></div>';document.body.appendChild(d.firstElementChild)}
function addPartRow(){var box=document.querySelector('#partRows');var div=document.createElement('div');div.className='card';div.style.background='#2A2A3E';div.innerHTML='<div class="form-group"><label>配件名称</label><input class="pn" /></div><div class="form-group"><label>型号/规格</label><input class="pm" /></div><div class="form-group"><label>费用/单价</label><input class="pc" type="number" value="0" /></div><div class="form-group"><label>质保天数</label><input class="pw" type="number" value="0" /></div>';box.appendChild(div)}
function submitDetails(id){var rows=document.querySelectorAll('#partRows .card');var items=[];for(var i=0;i<rows.length;i++){var n=rows[i].querySelector('.pn').value.trim();if(!n)continue;items.push({item_name:n,part_model:rows[i].querySelector('.pm').value.trim(),cost:parseFloat(rows[i].querySelector('.pc').value)||0,warranty_days:parseInt(rows[i].querySelector('.pw').value)||0})}if(!items.length){toast('请至少填写一个配件',1);return}uploadFiles('detailPhotos').then(function(photos){return api('PUT','/api/repairs/'+id+'/details',{items:items,photos:photos})}).then(function(){clo();toast('明细已提交，如有非合同配件会在详情提醒');loadRep();viewRep(id)}).catch(function(e){toast('失败: '+e.message,1)})}
function compRep(id){api('PUT','/api/repairs/'+id+'/complete',{}).then(function(){clo();toast('已标记完成');loadRep()}).catch(function(e){toast('失败: '+e.message,1)})}
function showVerifyForm(id){var d=document.createElement('div');d.innerHTML='<div class="modal-overlay"><div class="modal-content"><h3>验收维修单</h3><div class="form-group"><label>内部I8流程截图</label><input type="file" id="verifyPhotos" multiple accept="image/*" /></div><div class="form-group"><label>验收备注</label><textarea id="verifyNotes" rows="3"></textarea></div><div style="text-align:right;margin-top:16px;"><button class="btn btn-secondary" onclick="clo()">取消</button><button class="btn btn-primary" onclick="submitVerify('+id+')" style="margin-left:8px;">验收通过</button></div></div></div>';document.body.appendChild(d.firstElementChild)}
function submitVerify(id){uploadFiles('verifyPhotos').then(function(photos){return api('PUT','/api/repairs/'+id+'/verify',{verify_photos:photos,notes:document.getElementById('verifyNotes').value})}).then(function(){clo();toast('验收完成');loadRep()}).catch(function(e){toast('失败: '+e.message,1)})}
'''
s=s.replace('\n</script>','\n'+over+'\n</script>')
p.write_text(s,encoding='utf-8')
print('repair frontend flow patched')
