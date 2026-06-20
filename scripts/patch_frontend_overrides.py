from pathlib import Path
p=Path('/vol1/@appcenter/vehicle-mgr/后端/后台管理/index.html')
s=p.read_text(encoding='utf-8')
over=r'''

// ===== 权限/分组/校验增强覆盖函数 =====
function roleText(r){var m={admin:'管理员',fleet_manager:'车管员',manager:'车管员',dispatcher:'车管员',driver:'驾驶员',repair_shop:'修理厂'};return m[r]||r}
function checkUserForm(username,password,phone,isEdit){
  if(username && !/^[A-Za-z]+$/.test(username)){toast('用户名只能使用纯英文字母',1);return false}
  if(!isEdit && (!password || password.length<6)){toast('密码至少6位',1);return false}
  if(password && password.length<6){toast('密码至少6位',1);return false}
  if(phone && !/^1\d{10}$/.test(phone)){toast('手机号必须为11位大陆手机号',1);return false}
  return true
}
function loadGroupOptions(selected, cb){api('GET','/api/groups').then(function(gs){var h='<option value="">不绑定</option>';for(var i=0;i<gs.length;i++){h+='<option value="'+gs[i].id+'" '+(String(selected||'')===String(gs[i].id)?'selected':'')+'>'+gs[i].name+'</option>'}cb(h)}).catch(function(){cb('<option value="">不绑定</option>')})}
function loadDriverOptions(selected, groupId, cb){var url='/api/users?role=driver';api('GET',url).then(function(us){var h='<option value="">不绑定</option>';for(var i=0;i<us.length;i++){if(groupId&&us[i].group_id&&String(us[i].group_id)!==String(groupId))continue;h+='<option value="'+us[i].id+'" '+(String(selected||'')===String(us[i].id)?'selected':'')+'>'+us[i].name+'('+us[i].username+')</option>'}cb(h)}).catch(function(){cb('<option value="">不绑定</option>')})}
function loadShopOptions(selected, cb){api('GET','/api/users?role=repair_shop').then(function(us){var h='<option value="">请选择维修厂</option>';for(var i=0;i<us.length;i++){h+='<option value="'+us[i].id+'" '+(String(selected||'')===String(us[i].id)?'selected':'')+'>'+us[i].name+'('+us[i].username+')</option>'}cb(h)}).catch(function(){cb('<option value="">暂无维修厂</option>')})}
function loadVehicleOptions(selected, cb){api('GET','/api/vehicles').then(function(vs){var h='<option value="">请选择车辆</option>';for(var i=0;i<vs.length;i++){h+='<option value="'+vs[i].plate_number+'" '+(String(selected||'')===String(vs[i].plate_number)?'selected':'')+'>'+vs[i].plate_number+(vs[i].driver_name?' - '+vs[i].driver_name:'')+'</option>'}cb(h)}).catch(function(){cb('<option value="">暂无车辆</option>')})}

function showUsrForm(){
  loadGroupOptions('',function(groups){
    var d=document.createElement('div');
    d.innerHTML='<div class="modal-overlay"><div class="modal-content"><h3>添加用户</h3>'+ 
    '<div class="form-group"><label>用户名 *（纯英文字母）</label><input id="u1" /></div>'+ 
    '<div class="form-group"><label>姓名</label><input id="u2" /></div>'+ 
    '<div class="form-group"><label>密码 *（至少6位）</label><input id="u3" type="password" value="123456" /></div>'+ 
    '<div class="form-group"><label>角色</label><select id="u4"><option value="driver">驾驶员</option><option value="fleet_manager">车管员</option><option value="repair_shop">修理厂</option><option value="admin">管理员</option></select></div>'+ 
    '<div class="form-group"><label>手机号（11位）</label><input id="u5" /></div>'+ 
    '<div class="form-group"><label>所属分组</label><select id="u6">'+groups+'</select></div>'+ 
    '<div style="text-align:right;margin-top:16px;"><button class="btn btn-secondary" onclick="clo()">取消</button><button class="btn btn-primary" onclick="doAddUsr()" style="margin-left:8px;">保存</button></div></div></div>';
    document.body.appendChild(d.firstElementChild);
  })
}
function doAddUsr(){
  var username=document.getElementById('u1').value.trim(), pass=document.getElementById('u3').value, phone=document.getElementById('u5').value.trim();
  if(!checkUserForm(username,pass,phone,false))return;
  var gid=document.getElementById('u6').value;
  var d={username:username,name:document.getElementById('u2').value,password:pass,role:document.getElementById('u4').value,phone:phone,group_id:gid?parseInt(gid):null};
  if(!d.username){toast('请输入用户名',1);return}
  api('POST','/api/users',d).then(function(){clo();toast('添加成功');loadUsr()}).catch(function(e){toast('失败: '+e.message,1)});
}
function editUsr(id){
  api('GET','/api/users/'+id).then(function(u){loadGroupOptions(u.group_id,function(groups){
    var d=document.createElement('div');
    d.innerHTML='<div class="modal-overlay"><div class="modal-content"><h3>编辑用户</h3>'+ 
    '<div class="form-group"><label>用户名</label><input id="u1" value="'+u.username+'" disabled /></div>'+ 
    '<div class="form-group"><label>姓名</label><input id="u2" value="'+(u.name||'')+'" /></div>'+ 
    '<div class="form-group"><label>密码（留空不修改，至少6位）</label><input id="u3" type="password" /></div>'+ 
    '<div class="form-group"><label>角色</label><select id="u4"><option value="driver" '+(u.role==='driver'?'selected':'')+'>驾驶员</option><option value="fleet_manager" '+(u.role==='fleet_manager'?'selected':'')+'>车管员</option><option value="repair_shop" '+(u.role==='repair_shop'?'selected':'')+'>修理厂</option><option value="admin" '+(u.role==='admin'?'selected':'')+'>管理员</option></select></div>'+ 
    '<div class="form-group"><label>手机号（11位）</label><input id="u5" value="'+(u.phone||'')+'" /></div>'+ 
    '<div class="form-group"><label>所属分组</label><select id="u6">'+groups+'</select></div>'+ 
    '<div style="text-align:right;margin-top:16px;"><button class="btn btn-secondary" onclick="clo()">取消</button><button class="btn btn-primary" onclick="doEditUsr('+id+')" style="margin-left:8px;">保存</button></div></div></div>';
    document.body.appendChild(d.firstElementChild);
  })}).catch(function(e){toast('加载用户失败: '+e.message,1)})
}
function doEditUsr(id){
  var pass=document.getElementById('u3').value, phone=document.getElementById('u5').value.trim();
  if(!checkUserForm('',pass,phone,true))return;
  var gid=document.getElementById('u6').value;
  var d={username:document.getElementById('u1').value,name:document.getElementById('u2').value,password:pass,role:document.getElementById('u4').value,phone:phone,group_id:gid?parseInt(gid):null};
  api('PUT','/api/users/'+id,d).then(function(){clo();toast('更新成功');loadUsr()}).catch(function(e){toast('失败: '+e.message,1)});
}

function showVehForm(){
  loadGroupOptions('',function(groups){loadDriverOptions('',null,function(drivers){
    var d=document.createElement('div');
    d.innerHTML='<div class="modal-overlay"><div class="modal-content"><h3>添加车辆</h3><div class="form-group"><label>车牌号 *</label><input id="v1" /></div><div class="form-group"><label>品牌</label><input id="v2" /></div><div class="form-group"><label>型号</label><input id="v3" /></div><div class="form-group"><label>颜色</label><input id="v4" /></div><div class="form-group"><label>车架号</label><input id="v5" /></div><div class="form-group"><label>所属分组</label><select id="v6">'+groups+'</select></div><div class="form-group"><label>绑定驾驶员</label><select id="v7">'+drivers+'</select></div><div style="text-align:right;margin-top:16px;"><button class="btn btn-secondary" onclick="clo()">取消</button><button class="btn btn-primary" onclick="doAddVeh()" style="margin-left:8px;">保存</button></div></div></div>';
    document.body.appendChild(d.firstElementChild);
  })})
}
function doAddVeh(){
  var gid=document.getElementById('v6')?document.getElementById('v6').value:'';var did=document.getElementById('v7')?document.getElementById('v7').value:'';
  var d={plate_number:document.getElementById('v1').value,brand:document.getElementById('v2').value,model:document.getElementById('v3').value,color:document.getElementById('v4').value,vin:document.getElementById('v5').value,group_id:gid?parseInt(gid):null,driver_id:did?parseInt(did):null};
  if(!d.plate_number){toast('请输入车牌号',1);return}
  api('POST','/api/vehicles',d).then(function(){clo();toast('添加成功');loadVeh()}).catch(function(e){toast('失败: '+e.message,1)});
}
function editVeh(p){
  api('GET','/api/vehicles/'+encodeURIComponent(p)).then(function(v){loadGroupOptions(v.group_id,function(groups){loadDriverOptions(v.driver_id,v.group_id,function(drivers){
    var d=document.createElement('div');
    d.innerHTML='<div class="modal-overlay"><div class="modal-content"><h3>编辑车辆</h3><div class="form-group"><label>车牌号</label><input id="v1" value="'+v.plate_number+'" /></div><div class="form-group"><label>品牌</label><input id="v2" value="'+(v.brand||'')+'" /></div><div class="form-group"><label>型号</label><input id="v3" value="'+(v.model||'')+'" /></div><div class="form-group"><label>颜色</label><input id="v4" value="'+(v.color||'')+'" /></div><div class="form-group"><label>车架号</label><input id="v5" value="'+(v.vin||'')+'" /></div><div class="form-group"><label>所属分组</label><select id="v6">'+groups+'</select></div><div class="form-group"><label>绑定驾驶员</label><select id="v7">'+drivers+'</select></div><div style="text-align:right;margin-top:16px;"><button class="btn btn-secondary" onclick="clo()">取消</button><button class="btn btn-primary" onclick="doEditVeh('+v.id+')" style="margin-left:8px;">保存</button></div></div></div>';
    document.body.appendChild(d.firstElementChild);
  })})})
}
function doEditVeh(id){
  var gid=document.getElementById('v6')?document.getElementById('v6').value:'';var did=document.getElementById('v7')?document.getElementById('v7').value:'';
  var d={plate_number:document.getElementById('v1').value,brand:document.getElementById('v2').value,model:document.getElementById('v3').value,color:document.getElementById('v4').value,vin:document.getElementById('v5').value,group_id:gid?parseInt(gid):null,driver_id:did?parseInt(did):null};
  api('PUT','/api/vehicles/'+id,d).then(function(){clo();toast('更新成功');loadVeh()}).catch(function(e){toast('失败: '+e.message,1)});
}

function showRepForm(){
  loadVehicleOptions('',function(vehicles){loadShopOptions('',function(shops){
    var d=document.createElement('div');
    d.innerHTML='<div class="modal-overlay"><div class="modal-content" style="width:540px;"><h3>新建维修单</h3>'+ 
    '<div class="form-group"><label>车辆 *</label><select id="r1">'+vehicles+'</select></div>'+ 
    '<div class="form-group"><label>维修厂 *</label><select id="r2">'+shops+'</select></div>'+ 
    '<div class="form-group"><label>故障描述</label><textarea id="r3" rows="3"></textarea></div>'+ 
    '<div style="text-align:right;margin-top:16px;"><button class="btn btn-secondary" onclick="clo()">取消</button><button class="btn btn-primary" onclick="doAddRep()" style="margin-left:8px;">创建</button></div></div></div>';
    document.body.appendChild(d.firstElementChild);
  })})
}
function doAddRep(){
  var plate=document.getElementById('r1').value, shop=parseInt(document.getElementById('r2').value)||0;
  if(!plate||!shop){toast('请选择车辆和维修厂',1);return}
  api('POST','/api/repairs',{plate_number:plate,shop_id:shop,description:document.getElementById('r3').value}).then(function(){clo();toast('创建成功');loadRep()}).catch(function(e){toast('失败: '+e.message,1)});
}
'''
s=s.replace('\n</script>','\n'+over+'\n</script>')
p.write_text(s,encoding='utf-8')
print('frontend override patched')
