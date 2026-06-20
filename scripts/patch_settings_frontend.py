from pathlib import Path
p=Path('/vol1/@appcenter/vehicle-mgr/后端/后台管理/index.html')
s=p.read_text(encoding='utf-8')
over=r'''

// ===== 系统设置修复：后端为单项 key/value 保存 =====
function showSettings(){
  api('GET','/api/settings').then(function(resp){
    var settings=(resp&&resp.settings)||{};
    var d=document.createElement('div');
    d.innerHTML='<div class="modal-overlay"><div class="modal-content" style="width:620px;"><h3>⚙ 系统设置</h3>'+ 
      '<p style="color:#888;font-size:13px;margin-bottom:12px;">配置文件：'+((resp&&resp.env_file_path)||'')+'</p>'+ 
      '<div class="form-group"><label>服务端口 PORT（修改后需重启服务）</label><input id="set_PORT" value="'+(settings.PORT||'')+'" /></div>'+ 
      '<div class="form-group"><label>OCR 里程识别 OCR_ENABLED（true/false）</label><select id="set_OCR_ENABLED"><option value="false" '+(String(settings.OCR_ENABLED)==='true'?'':'selected')+'>false</option><option value="true" '+(String(settings.OCR_ENABLED)==='true'?'selected':'')+'>true</option></select></div>'+ 
      '<div class="form-group"><label>里程预警阈值 MILEAGE_THRESHOLD</label><input id="set_MILEAGE_THRESHOLD" value="'+(settings.MILEAGE_THRESHOLD||'')+'" /></div>'+ 
      '<div class="form-group"><label>数据存储目录 DATA_DIR</label><input id="set_DATA_DIR" value="'+(settings.DATA_DIR||'')+'" /></div>'+ 
      '<div class="form-group"><label>数据库目录 DB_DIR</label><input id="set_DB_DIR" value="'+(settings.DB_DIR||'')+'" /></div>'+ 
      '<div class="form-group"><label>照片目录 UPLOAD_DIR</label><input id="set_UPLOAD_DIR" value="'+(settings.UPLOAD_DIR||'')+'" /></div>'+ 
      '<div style="text-align:right;margin-top:16px;"><button class="btn btn-secondary" onclick="clo()">取消</button><button class="btn btn-primary" onclick="doSet()" style="margin-left:8px;">保存</button></div></div></div>';
    document.body.appendChild(d.firstElementChild);
  }).catch(function(e){toast('加载设置失败: '+e.message,1)});
}
function putSetting(key,value){return api('PUT','/api/settings',{key:key,value:String(value||'')})}
function doSet(){
  var keys=['PORT','OCR_ENABLED','MILEAGE_THRESHOLD','DATA_DIR','DB_DIR','UPLOAD_DIR'];
  var chain=Promise.resolve();
  keys.forEach(function(k){chain=chain.then(function(){return putSetting(k,document.getElementById('set_'+k).value)})});
  chain.then(function(){clo();toast('保存成功，部分配置需重启服务后生效')}).catch(function(e){toast('失败: '+e.message,1)});
}
'''
s=s.replace('\n</script>','\n'+over+'\n</script>')
p.write_text(s,encoding='utf-8')
print('settings frontend patched')
