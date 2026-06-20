from pathlib import Path
p=Path('/vol1/@appcenter/vehicle-mgr/后端/后台管理/index.html')
s=p.read_text(encoding='utf-8')
over=r'''

// ===== 修理厂权限：仅显示维修单 =====
function filterSidebarByRole(){
  var u=getU();
  if(!u)return;
  var role=u.role;
  var map={
    'repair_shop':['维修管理']
  };
  var allow=map[role];
  if(!allow)return;
  document.querySelectorAll('.sidebar a').forEach(function(a){
    var txt=a.textContent.trim();
    if(allow.indexOf(txt)===-1&&txt!=='退出')a.style.display='none';
  });
}
var _origShowPage=showPage;
showPage=function(name){
  var u=getU();
  if(u&&u.role==='repair_shop'&&name!=='repairs'){return}
  _origShowPage(name);
};
var _origSwitchPage=switchPage;
if(typeof switchPage==='function'){
  switchPage=function(name){
    var u=getU();
    if(u&&u.role==='repair_shop'&&name!=='repairs'){return}
    _origSwitchPage(name);
  };
}
'''
s=s.replace('\n</script>','\n'+over+'\n</script>')
# add shop_name to user form
s=s.replace(
'''    '<div class="form-group"><label>分组</label><select id="u5">'+groups+'</select></div>'+ 
    '<div class="form-group"><label>手机号</label><input id="u6" value="'+esc(x.phone||'')+'" /></div>'+''',
'''    '<div class="form-group"><label>分组</label><select id="u5">'+groups+'</select></div>'+ 
    '<div class="form-group" id="ushop"><label>修理厂名称</label><input id="u7" value="'+esc(x.shop_name||'')+'" placeholder="同一修理厂可建多个账号，名称一致即可" /></div>'+ 
    '<div class="form-group"><label>手机号</label><input id="u6" value="'+esc(x.phone||'')+'" /></div>'+'''
)
# toggle shop_name field by role in user form
s=s.replace(
'''function checkUserForm(username,password,phone,isEdit){
  if(!username||!username.match(/^[A-Za-z]+$/)){toast('用户名只能纯英文字母',1);return!1}
  if(password&&password.length<6){toast('密码至少6位',1);return!1}
  if(phone&&!phone.match(/^1\\d{10}$/)){toast('手机号必须为11位大陆手机号',1);return!1}
  return!0
}''',
'''function checkUserForm(username,password,phone,isEdit){
  if(!username||!username.match(/^[A-Za-z]+$/)){toast('用户名只能纯英文字母',1);return!1}
  if(password&&password.length<6){toast('密码至少6位',1);return!1}
  if(phone&&!phone.match(/^1\\d{10}$/)){toast('手机号必须为11位大陆手机号',1);return!1}
  return!0
}
function toggleShopField(){
  var role=document.getElementById('u4').value;
  var sf=document.getElementById('ushop');
  if(sf)sf.style.display=role==='repair_shop'?'flex':'none';
}'''
)
# add onchange to role select in user form
s=s.replace(
'''    '<div class="form-group"><label>角色 *</label><select id="u4">'+roles+'</select></div>'+''',
'''    '<div class="form-group"><label>角色 *</label><select id="u4" onchange="toggleShopField()">'+roles+'</select></div>'+'''
)
# save user include shop_name
s=s.replace(
'''  var d={username:document.getElementById('u1').value,password:document.getElementById('u2').value,role:document.getElementById('u4').value,phone:document.getElementById('u6').value,group_id:parseInt(document.getElementById('u5').value)||null,isActive:document.getElementById('u8').checked};''',
'''  var d={username:document.getElementById('u1').value,password:document.getElementById('u2').value,role:document.getElementById('u4').value,phone:document.getElementById('u6').value,group_id:parseInt(document.getElementById('u5').value)||null,shop_name:document.getElementById('u7')?document.getElementById('u7').value.trim():'',isActive:document.getElementById('u8').checked};'''
)
# user list table add shop_name column
s=s.replace(
'''<th>角色</th><th>分组</th><th>手机号</th><th>状态</th><th>操作</th></tr>';''',
'''<th>角色</th><th>分组</th><th>修理厂</th><th>手机号</th><th>状态</th><th>操作</th></tr>';'''
)
s=s.replace(
'''h+='<tr><td>'+esc(x.username)+'</td><td>'+roleText(x.role)+'</td><td>'+(x.group_id||'')+'</td><td>'+esc(x.phone)+'</td><td><span class="tag '+(x.is_active?'tag-active':'tag-retired')+'">'+(x.is_active?'正常':'已停用')+'</span></td><td><button class="btn btn-sm btn-secondary" onclick="showUserForm('+x.id+')">编辑</button><button class="btn btn-sm btn-danger" onclick="delUser('+x.id+')">删除</button></td></tr>';''',
'''h+='<tr><td>'+esc(x.username)+'</td><td>'+roleText(x.role)+'</td><td>'+(x.group_id||'')+'</td><td>'+esc(x.shop_name||'')+'</td><td>'+esc(x.phone)+'</td><td><span class="tag '+(x.is_active?'tag-active':'tag-retired')+'">'+(x.is_active?'正常':'已停用')+'</span></td><td><button class="btn btn-sm btn-secondary" onclick="showUserForm('+x.id+')">编辑</button><button class="btn btn-sm btn-danger" onclick="delUser('+x.id+')">删除</button></td></tr>';'''
)
# on login success, apply sidebar filter
s=s.replace(
'''localStorage.setItem('token',d.token);localStorage.setItem('user',JSON.stringify(d.user));location.reload()''',
'''localStorage.setItem('token',d.token);localStorage.setItem('user',JSON.stringify(d.user));location.reload()'''
)
# hook into page load
s=s.replace(
'''document.addEventListener('DOMContentLoaded',function(){checkAuth()})''',
'''document.addEventListener('DOMContentLoaded',function(){checkAuth();filterSidebarByRole()})'''
)
p.write_text(s,encoding='utf-8')
print('repair_shop frontend scope patched')
