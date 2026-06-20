from pathlib import Path
base=Path('/vol1/@appcenter/vehicle-mgr/后端')

# user model: remove shop_name
p=base/'模型/user.py'
s=p.read_text(encoding='utf-8')
if 'shop_name' in s:
    s=s.replace(
'''    group_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("groups.id"), nullable=True)
    shop_name: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)  # 修理厂名称，同一厂可建多个账号''',
'''    group_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("groups.id"), nullable=True)'''
    )
p.write_text(s,encoding='utf-8')

# db: skip shop_name migration (just don't add it - if already added, leave it, harmless)
# group_user.py: revert shop_name changes
p=base/'路由/group_user.py'
s=p.read_text(encoding='utf-8')
s=s.replace(
'''class UserReq(BaseModel):
    username: str
    password: str = ""
    role: str = "driver"
    phone: str = ""
    group_id: int | None = None
    shop_name: str = ""
    is_active: bool = True''',
'''class UserReq(BaseModel):
    username: str
    password: str = ""
    role: str = "driver"
    phone: str = ""
    group_id: int | None = None
    is_active: bool = True'''
)
s=s.replace(
'''        data = req.model_dump()
        if data.get("role") == "repair_shop" and not data.get("shop_name"):
            data["shop_name"] = data.get("username")
        u = User(**data)''',
'''        u = User(**req.model_dump())'''
)
s=s.replace(
'''    return {"id": u.id, "username": u.username, "role": u.role, "phone": u.phone, "group_id": u.group_id, "shop_name": u.shop_name, "is_active": u.is_active, "created_at": str(u.created_at)}''',
'''    return {"id": u.id, "username": u.username, "role": u.role, "phone": u.phone, "group_id": u.group_id, "is_active": u.is_active, "created_at": str(u.created_at)}'''
)
s=s.replace(
'''    data = req.model_dump()
    if data.get("role") == "repair_shop" and not data.get("shop_name"):
        data["shop_name"] = u.username
    for k, v in data.items():
        setattr(u, k, v)''',
'''    for k, v in req.model_dump().items():
        setattr(u, k, v)'''
)
s=s.replace(
'''    elif current.role == "repair_shop":
        query = select(User).where(User.role == "repair_shop", User.shop_name == current.shop_name).order_by(User.id.desc())
    else:''',
'''    else:'''
)
p.write_text(s,encoding='utf-8')

print('revert repair_shop multi-account done')
