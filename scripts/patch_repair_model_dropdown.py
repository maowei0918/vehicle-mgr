from pathlib import Path
p=Path('/vol1/@appcenter/vehicle-mgr/后端/后台管理/index.html')
s=p.read_text(encoding='utf-8')
over=r'''

// ===== 维修车型改为合同来源下拉 =====
function loadContractModels(shopId, cb){
  if(!shopId){cb('<option value="">请先选择汽修厂</option>');return}
  api('GET','/api/contract-parts/models?shop_id='+encodeURIComponent(shopId)).then(function(ms){
    var h='<option value="">请选择合同车型</option>';
    for(var i=0;i<ms.length;i++){h+='<option value="'+esc(ms[i].model)+'">'+esc(ms[i].model)+'</option>'}
    if(!ms.length)h='<option value="">该汽修厂暂无合同车型</option>';
    cb(h);
  }).catch(function(){cb('<option value="">车型加载失败</option>')})
}
function onRepairShopChange(){var shop=document.getElementById('r2').value;loadContractModels(shop,function(h){document.getElementById('rmodel').innerHTML=h})}
function showRepForm(){
  loadVehicleOptionsWithModels('',function(vehicles){loadShopOptions('',function(shops){
    var d=document.createElement('div');
    d.innerHTML='<div class="modal-overlay"><div class="modal-content" style="width:560px;"><h3>发起维修单</h3>'+ 
    '<div class="form-group"><label>车辆 *</label><select id="r1">'+vehicles+'</select></div>'+ 
    '<div class="form-group"><label>汽修厂 *</label><select id="r2" onchange="onRepairShopChange()">'+shops+'</select></div>'+ 
    '<div class="form-group"><label>车型 *（来源：该汽修厂合同配件明细）</label><select id="rmodel"><option value="">请先选择汽修厂</option></select></div>'+ 
    '<div class="form-group"><label>故障描述</label><textarea id="r3" rows="3"></textarea></div>'+ 
    '<div class="form-group"><label>内部OA审批截图</label><input type="file" id="r4" multiple accept="image/*" /></div>'+ 
    '<div style="text-align:right;margin-top:16px;"><button class="btn btn-secondary" onclick="clo()">取消</button><button class="btn btn-primary" onclick="doAddRep()" style="margin-left:8px;">发单</button></div></div></div>';
    document.body.appendChild(d.firstElementChild);
  })})
}
function doAddRep(){
  var plate=document.getElementById('r1').value, model=document.getElementById('rmodel').value, shop=parseInt(document.getElementById('r2').value)||0;
  if(!plate||!shop||!model){toast('请选择车辆、汽修厂和合同车型',1);return}
  uploadFiles('r4').then(function(photos){return api('POST','/api/repairs',{plate_number:plate,vehicle_model:model,shop_id:shop,description:document.getElementById('r3').value,dispatch_photos:photos})}).then(function(){clo();toast('发单成功');loadRep()}).catch(function(e){toast('失败: '+e.message,1)});
}
'''
s=s.replace('\n</script>','\n'+over+'\n</script>')
p.write_text(s,encoding='utf-8')
print('repair model dropdown patched')
