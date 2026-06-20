from pathlib import Path
p=Path('/vol1/@appcenter/vehicle-mgr/后端/后台管理/index.html')
s=p.read_text(encoding='utf-8')
# Patch latest override snippets broadly
s=s.replace('<th>修理厂ID</th><th>配件名称</th><th>型号</th>', '<th>修理厂ID</th><th>车型</th><th>配件名称</th><th>型号</th>')
s=s.replace("'<tr><td>'+x.id+'</td><td>'+(x.shop_id||'')+'</td><td>'+esc(x.part_name)+'</td><td>'+esc(x.part_model)", "'<tr><td>'+x.id+'</td><td>'+(x.shop_id||'')+'</td><td>'+esc(x.vehicle_model||'')+'</td><td>'+esc(x.part_name)+'</td><td>'+esc(x.part_model)")
s=s.replace("<div class=\"form-group\"><label>配件名称 *</label><input id=\"cp2\"", "<div class=\"form-group\"><label>车型 *</label><input id=\"cpv\" value=\"'+esc(x.vehicle_model||'')+'\" /></div><div class=\"form-group\"><label>配件名称 *</label><input id=\"cp2\"")
s=s.replace("var d={shop_id:shop?parseInt(shop):null,part_name:document.getElementById('cp2').value", "var d={shop_id:shop?parseInt(shop):null,vehicle_model:document.getElementById('cpv').value,part_name:document.getElementById('cp2').value")
s=s.replace('Excel列：修理厂ID、配件名称、型号、合同价、质保天数、备注', 'Excel列：修理厂ID、车型、配件名称、型号、合同价、质保天数、备注')
p.write_text(s,encoding='utf-8')
print('contract frontend model patched')
