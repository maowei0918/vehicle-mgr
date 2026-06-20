from pathlib import Path
p=Path('/vol1/@appcenter/vehicle-mgr/后端/后台管理/index.html')
s=p.read_text(encoding='utf-8')
over=r'''

/* ===== 移动端自适应 ===== */
(function(){
  var meta=document.querySelector('meta[name="viewport"]');
  if(!meta){meta=document.createElement('meta');meta.name='viewport';document.head.appendChild(meta)}
  meta.content='width=device-width,initial-scale=1.0,maximum-scale=1.0,user-scalable=no';
})();
'''
s=s.replace('<style>\n*','<style>\n'+over+'\n*')
s=s.replace(
'''body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#0F0F19;color:#E0E0E0;display:flex;min-height:100vh}''',
'''body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#0F0F19;color:#E0E0E0;display:flex;min-height:100vh;overflow-x:hidden}'''
)
s=s.replace(
'''  <style>
:root{--sidebar-w:200px;--pad:20px}
''','')  # no such root block yet
s=s.replace(
'''sidebar{width:200px;background:#1A1A2E;padding:20px 0;display:flex;flex-direction:column;flex-shrink:0}''',
'''sidebar{width:200px;background:#1A1A2E;padding:20px 0;display:flex;flex-direction:column;flex-shrink:0;transition:transform .25s;overflow-y:auto}'''
)
s=s.replace(
'''sidebar h2{text-align:center;color:#E82337;margin-bottom:24px;font-size:16px;padding:0 12px}''',
'''sidebar h2{text-align:center;color:#E82337;margin-bottom:24px;font-size:16px;padding:0 12px;display:flex;align-items:center;justify-content:space-between}'''
)
s=s.replace(
'''sidebar a{display:block;padding:10px 20px;color:#AAA;text-decoration:none;cursor:pointer;font-size:14px;transition:all .2s}''',
'''sidebar a{display:block;padding:12px 20px;color:#AAA;text-decoration:none;cursor:pointer;font-size:14px;transition:all .2s}'''
)
s=s.replace(
'''.main{flex:1;padding:20px 30px;overflow:auto}''',
'''.main{flex:1;padding:20px 30px;overflow:auto}'''
)
s=s.replace(
'''table{width:100%;border-collapse:collapse;font-size:13px}
th{padding:8px 10px;text-align:left;background:#2A2A3E;color:#888;font-weight:400}
td{padding:8px 10px;border-bottom:1px solid #2A2A3E}''',
'''table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:8px 10px;text-align:left;border-bottom:1px solid #2A2A3E}
th{background:#2A2A3E;color:#888;font-weight:400;position:sticky;top:0;z-index:1}'''
)
s=s.replace(
'''.filter-bar{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-end}''',
'''.filter-bar{display:flex;flex-wrap:wrap;gap:12px;align-items:flex-end}'''
)
s=s.replace(
'''.modal-content{background:#1A1A2E;border:1px solid #3A3A4E;border-radius:8px;padding:24px;min-width:400px;max-width:80vw;max-height:80vh;overflow:auto}''',
'''.modal-content{background:#1A1A2E;border:1px solid #3A3A4E;border-radius:8px;padding:24px;min-width:400px;max-width:92vw;max-height:80vh;overflow:auto}'''
)
# Append mobile media queries before </style>
mq='''
@media (max-width: 768px) {
  body { flex-direction: column; }
  .sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    width: 240px;
    z-index: 1100;
    transform: translateX(-100%);
    box-shadow: 2px 0 12px rgba(0,0,0,.5);
  }
  .sidebar.open { transform: translateX(0); }
  .main { padding: 12px; }
  .page-title { font-size: 18px; }
  .filter-bar { flex-direction: column; align-items: stretch; }
  .filter-bar .form-group,
  .filter-bar .btn { width: 100%; }
  .filter-bar .btn { justify-content: center; }
  .card { padding: 12px; overflow-x: auto; }
  table { min-width: 600px; font-size: 12px; }
  .modal-content { min-width: auto; max-width: 96vw; padding: 16px; }
  .form-group input,
  .form-group select,
  .form-group textarea { font-size: 16px; padding: 10px 12px; }
  .btn { font-size: 14px; padding: 10px 14px; }
  .topbar-mobile-toggle {
    display: flex;
    align-items: center;
    padding: 8px 12px;
    background: #1A1A2E;
    border-bottom: 1px solid #2A2A3E;
  }
  .topbar-mobile-toggle button {
    background: none;
    border: none;
    color: #E82337;
    font-size: 22px;
    cursor: pointer;
    margin-right: 10px;
  }
}
@media (max-width: 480px) {
  .modal-content { padding: 12px; }
  table { min-width: 500px; font-size: 11px; }
}
'''
s=s.replace('</style>',mq+'</style>')
p.write_text(s,encoding='utf-8')
print('mobile responsive patched')
