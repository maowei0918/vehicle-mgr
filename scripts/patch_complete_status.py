from pathlib import Path
p=Path('/vol1/@appcenter/vehicle-mgr/后端/路由/repair.py')
s=p.read_text(encoding='utf-8')
s=s.replace('if order.status != "in_progress":\n        raise HTTPException(400, "当前状态不可完成")', 'if order.status not in ("in_progress", "accepted", "submitted"):\n        raise HTTPException(400, "当前状态不可完成")')
p.write_text(s,encoding='utf-8')
print('complete status patched')
