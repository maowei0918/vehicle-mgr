from pathlib import Path
p=Path('/vol1/@appcenter/vehicle-mgr/后端/后台管理/index.html')
s=p.read_text(encoding='utf-8')
# Add close button inside sidebar
s=s.replace(
'''sidebar h2{text-align:center;color:#E82337;margin-bottom:24px;font-size:16px;padding:0 12px;display:flex;align-items:center;justify-content:space-between}''',
'''sidebar h2{text-align:center;color:#E82337;margin-bottom:24px;font-size:16px;padding:0 12px;display:flex;align-items:center;justify-content:space-between}''')
# Add sidebar close button after h2
s=s.replace(
'''sidebar h2{text-align:center;color:#E82337;margin-bottom:24px;font-size:16px;padding:0 12px;display:flex;align-items:center;justify-content:space-between}\n.sidebar a{display:block''',
'''sidebar h2{text-align:center;color:#E82337;margin-bottom:24px;font-size:16px;padding:0 12px;display:flex;align-items:center;justify-content:space-between}\n.sidebar h2 .sidebar-close{display:none;background:none;border:none;color:#AAA;font-size:20px;cursor:pointer}\n@media(max-width:768px){.sidebar h2 .sidebar-close{display:block}}\n.sidebar a{display:block''')
# Add topbar and sidebar overlay + toggle JS
over=r'''
// ===== 移动端侧栏切换 =====
function initMobileSidebar(){
  if(document.getElementById('mobile-toggle'))return;
  var topbar=document.createElement('div');
  topbar.className='topbar-mobile-toggle';
  topbar.id='mobile-toggle';
  topbar.innerHTML='<button id="menuBtn">☰</button><span style="color:#E82337;font-weight:700;">车辆管理</span>';
  document.body.insertBefore(topbar,document.body.firstChild);
  var overlay=document.createElement('div');
  overlay.id='sidebar-overlay';
  overlay.style.cssText='display:none;position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:1050;';
  document.body.appendChild(overlay);
  document.getElementById('menuBtn').addEventListener('click',function(){
    var sb=document.querySelector('.sidebar');
    var open=sb.classList.toggle('open');
    document.getElementById('sidebar-overlay').style.display=open?'block':'none';
  });
  overlay.addEventListener('click',function(){
    document.querySelector('.sidebar').classList.remove('open');
    overlay.style.display='none';
  });
  document.querySelectorAll('.sidebar a').forEach(function(a){
    a.addEventListener('click',function(){
      if(window.innerWidth<=768){
        document.querySelector('.sidebar').classList.remove('open');
        document.getElementById('sidebar-overlay').style.display='none';
      }
    });
  });
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initMobileSidebar);else initMobileSidebar();
'''
s=s.replace('\n</script>','\n'+over+'\n</script>')
p.write_text(s,encoding='utf-8')
print('mobile sidebar toggle patched')
