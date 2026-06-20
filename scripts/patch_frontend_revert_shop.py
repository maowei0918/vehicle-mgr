from pathlib import Path
p=Path('/vol1/@appcenter/vehicle-mgr/后端/后台管理/index.html')
s=p.read_text(encoding='utf-8')
# remove shop_name from user form
s=s.replace(
'''    '<div class="form-group" id="ushop"><label>修理厂名称</label><input id="u7" value="'+esc(x.shop_name||'')+'" placeholder="同一修理厂可建多个账号，名称一致即可" /></div>'+ 
    '<div class="form-group"><label>手机号</label><input id="u6" value="'+esc(x.phone||'')+'" /></div>'+''',
'''    '<div class="form-group"><label>手机号</label><input id="u6" value="'+esc(x.phone||'')+'" /></div>'+'''
)
# remove toggleShopField and onchange
s=s.replace(
'''    '<div class="form-group"><label>角色 *</label><select id="u4" onchange="toggleShopField()">'+roles+'</select></div>'+''',
'''    '<div class="form-group"><label>角色 *</label><select id="u4">'+roles+'</select></div>'+'''
)
s=s.replace(
'''function toggleShopField(){
  var role=document.getElementById('u4').value;
  var sf=document.getElementById('ushop');
  if(sf)sf.style.display=role==='repair_shop'?'flex':'none';
}''',
''''''
)
# remove shop_name from save
s=s.replace(
'''  var d={username:document.getElementById('u1').value,password:document.getElementById('u2').value,role:document.getElementById('u4').value,phone:document.getElementById('u6').value,group_id:parseInt(document.getElementById('u5').value)||null,shop_name:document.getElementById('u7')?document.getElementById('u7').value.trim():'',isActive:document.getElementById('u8').checked};''',
'''  var d={username:document.getElementById('u1').value,password:document.getElementById('u2').value,role:document.getElementById('u4').value,phone:document.getElementById('u6').value,group_id:parseInt(document.getElementById('u5').value)||null,isActive:document.getElementById('u8').checked};'''
)
# remove shop_name column from user list
s=s.replace(
'''<th>角色</th><th>分组</th><th>修理厂</th><th>手机号</th><th>状态</th><th>操作</th></tr>';''',
'''<th>角色</th><th>分组</th><th>手机号</th><th>状态</th><th>操作</th></tr>';'''
)
s=s.replace(
'''h+='<tr><td>'+esc(x.username)+'</td><td>'+roleText(x.role)+'</td><td>'+(x.group_id||'')+'</td><td>'+esc(x.shop_name||'')+'</td><td>'+esc(x.phone)+'</td><td><span class="tag '+(x.is_active?'tag-active':'tag-retired')+'">'+(x.is_active?'正常':'已停用')+'</span></td><td><button class="btn btn-sm btn-secondary" onclick="showUserForm('+x.id+')">编辑</button><button class="btn btn-sm btn-danger" onclick="delUser('+x.id+')">删除</button></td></tr>';''',
'''h+='<tr><td>'+esc(x.username)+'</td><td>'+roleText(x.role)+'</td><td>'+(x.group_id||'')+'</td><td>'+esc(x.phone)+'</td><td><span class="tag '+(x.is_active?'tag-active':'tag-retired')+'">'+(x.is_active?'正常':'已停用')+'</span></td><td><button class="btn btn-sm btn-secondary" onclick="showUserForm('+x.id+')">编辑</button><button class="btn btn-sm btn-danger" onclick="delUser('+x.id+')">删除</button></td></tr>';'''
)
p.write_text(s,encoding='utf-8')
print('frontend revert multi-account patched')
