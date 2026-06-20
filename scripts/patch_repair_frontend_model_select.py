from pathlib import Path
p=Path('/vol1/@appcenter/vehicle-mgr/后端/后台管理/index.html')
s=p.read_text(encoding='utf-8')
over=r'''

// ===== 维修发单车型选择/确认 =====
var VEHICLE_CACHE=[];
function loadVehicleOptionsWithModels(selected, cb){api('GET','/api/vehicles').then(function(vs){VEHICLE_CACHE=vs||[];var h='<option value="">请选择车辆</option>';for(var i=0;i<VEHICLE_CACHE.length;i++){var v=VEHICLE_CACHE[i];h+='<option value="'+v.plate_number+'" data-model="'+esc(v.model||'')+'" '+(String(selected||'')===String(v.plate_number)?'selected':'')+'>'+v.plate_number+(v.model?' - '+v.model:'')+(v.driver_name?' - '+v.driver_name:'')+'</option>'}cb(h)}).catch(function(){cb('<option value="">暂无车辆</option>')})}
function onRepairVehicleChange(){var sel=document.getElementById('r1');var opt=sel.options[sel.selectedIndex];var model=(opt&&opt.getAttribute('data-model'))||'';document.getElementById('rmodel').value=model}
function showRepForm(){
  loadVehicleOptionsWithModels('',function(vehicles){loadShopOptions('',function(shops){
    var d=document.createElement('div');
    d.innerHTML='<div class="modal-overlay"><div class="modal-content" style="width:560px;"><h3>发起维修单</h3>'+ 
    '<div class="form-group"><label>车辆 *</label><select id="r1" onchange="onRepairVehicleChange()">'+vehicles+'</select></div>'+ 
    '<div class="form-group"><label>车型 *（用于合同配件校验，可手动确认/修改）</label><input id="rmodel" placeholder="例如：帕萨特/依维柯/车型型号" /></div>'+ 
    '<div class="form-group"><label>汽修厂 *</label><select id="r2">'+shops+'</select></div>'+ 
    '<div class="form-group"><label>故障描述</label><textarea id="r3" rows="3"></textarea></div>'+ 
    '<div class="form-group"><label>内部OA审批截图</label><input type="file" id="r4" multiple accept="image/*" /></div>'+ 
    '<div style="text-align:right;margin-top:16px;"><button class="btn btn-secondary" onclick="clo()">取消</button><button class="btn btn-primary" onclick="doAddRep()" style="margin-left:8px;">发单</button></div></div></div>';
    document.body.appendChild(d.firstElementChild);
  })})
}
function doAddRep(){
  var plate=document.getElementById('r1').value, model=document.getElementById('rmodel').value.trim(), shop=parseInt(document.getElementById('r2').value)||0;
  if(!plate||!model||!shop){toast('请选择车辆、填写车型并选择汽修厂',1);return}
  uploadFiles('r4').then(function(photos){return api('POST','/api/repairs',{plate_number:plate,vehicle_model:model,shop_id:shop,description:document.getElementById('r3').value,dispatch_photos:photos})}).then(function(){clo();toast('发单成功');loadRep()}).catch(function(e){toast('失败: '+e.message,1)});
}
'''
s=s.replace('\n</script>','\n'+over+'\n</script>')
p.write_text(s,encoding='utf-8')
print('repair frontend model select patched')
