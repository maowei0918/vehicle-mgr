"""车辆管理系统 - 数据库"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import DATABASE_URL

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    from models import user as _user_mod  # noqa
    from models import vehicle as _veh_mod  # noqa
    from models import inspection as _insp_mod  # noqa
    from models import repair as _rep_mod  # noqa
    from models import contract_part as _cp_mod  # noqa
    from models import contract as _contract_mod  # noqa
    from models import repair_flow as _rf_mod  # noqa
    from models import operation_log as _op_mod  # noqa
    from models import role as _role_mod  # noqa
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # 初始化默认数据
    from sqlalchemy import select
    from models.user import User
    from models.role import Role, RolePermission
    from services.auth import hash_password
    from services.permissions import (
        USER_VIEW, USER_CREATE, USER_EDIT, USER_DELETE, USER_IMPORT,
        GROUP_VIEW, GROUP_CREATE, GROUP_DELETE,
        VEHICLE_VIEW, VEHICLE_CREATE, VEHICLE_EDIT, VEHICLE_DELETE, VEHICLE_IMPORT, VEHICLE_EXPORT,
        INSPECTION_VIEW, INSPECTION_REPORT,
        REPAIR_VIEW, REPAIR_DISPATCH, REPAIR_ACCEPT, REPAIR_DETAIL, REPAIR_COMPLETE, REPAIR_VERIFY, REPAIR_EXPORT, REPAIR_ADVANCE,
        CONTRACT_VIEW, CONTRACT_CREATE, CONTRACT_EDIT, CONTRACT_DELETE, CONTRACT_ACTIVATE,
        PART_VIEW, PART_CREATE, PART_EDIT, PART_DELETE, PART_IMPORT,
        FLOW_VIEW, FLOW_CREATE, FLOW_EDIT, FLOW_DELETE,
        SETTINGS_EDIT, LOG_VIEW,
    )
    async with async_session() as db:
        # ---- 创建默认角色 ----
        role_map = {}
        role_defs = [
            ("admin", "管理员", True, [
                USER_VIEW, USER_CREATE, USER_EDIT, USER_DELETE, USER_IMPORT,
                GROUP_VIEW, GROUP_CREATE, GROUP_DELETE,
                VEHICLE_VIEW, VEHICLE_CREATE, VEHICLE_EDIT, VEHICLE_DELETE, VEHICLE_IMPORT, VEHICLE_EXPORT,
                INSPECTION_VIEW, INSPECTION_REPORT,
                REPAIR_VIEW, REPAIR_DISPATCH, REPAIR_ACCEPT, REPAIR_DETAIL, REPAIR_COMPLETE, REPAIR_VERIFY, REPAIR_EXPORT, REPAIR_ADVANCE,
                CONTRACT_VIEW, CONTRACT_CREATE, CONTRACT_EDIT, CONTRACT_DELETE, CONTRACT_ACTIVATE,
                PART_VIEW, PART_CREATE, PART_EDIT, PART_DELETE, PART_IMPORT,
                FLOW_VIEW, FLOW_CREATE, FLOW_EDIT, FLOW_DELETE,
                SETTINGS_EDIT, LOG_VIEW,
            ]),
            ("fleet_manager", "车管员", True, [
                USER_VIEW, USER_CREATE, USER_EDIT, GROUP_VIEW, GROUP_CREATE,
                VEHICLE_VIEW, VEHICLE_CREATE, VEHICLE_EDIT, VEHICLE_IMPORT, VEHICLE_EXPORT,
                INSPECTION_VIEW, INSPECTION_REPORT,
                REPAIR_VIEW, REPAIR_DISPATCH, REPAIR_VERIFY, REPAIR_EXPORT, REPAIR_ADVANCE,
                CONTRACT_VIEW, PART_VIEW, FLOW_VIEW, LOG_VIEW,
            ]),
            ("repair_shop", "汽修厂", True, [
                REPAIR_VIEW, REPAIR_ACCEPT, REPAIR_DETAIL, REPAIR_COMPLETE, REPAIR_ADVANCE,
            ]),
            ("driver", "司机", True, [
                VEHICLE_VIEW, INSPECTION_VIEW, INSPECTION_REPORT,
            ]),
        ]
        for name, display_name, is_system, perms in role_defs:
            exist = await db.execute(select(Role).where(Role.name == name))
            r = exist.scalar_one_or_none()
            if not r:
                ds = {"admin": "all", "fleet_manager": "group", "repair_shop": "self", "driver": "self"}.get(name, "all")
                r = Role(name=name, display_name=display_name, is_system=is_system, data_scope=ds)
                db.add(r)
                await db.flush()
                for pk in perms:
                    db.add(RolePermission(role_id=r.id, permission_key=pk))
            role_map[name] = r.id

        # ---- 迁移旧用户：role_id 为空时根据 role 字段关联 ----
        users_r = await db.execute(select(User).where(User.role_id.is_(None)))
        for u in users_r.scalars().all():
            if u.role in role_map:
                u.role_id = role_map[u.role]

        # ---- 创建默认管理员（仅当用户表为空时） ----
        rs = await db.execute(select(User).limit(1))
        if rs.scalar_one_or_none() is None:
            admin = User(
                username="admin", password_hash=hash_password("admin123"),
                name="管理员", role="admin", role_id=role_map["admin"], is_active=True,
            )
            db.add(admin)
            await db.commit()

        # ---- 创建默认维修流程 ----
        from models.repair_flow import RepairFlow, RepairFlowStep
        flow_rs = await db.execute(select(RepairFlow).limit(1))
        if flow_rs.scalar_one_or_none() is None:
            default_flow = RepairFlow(name="标准流程")
            db.add(default_flow)
            await db.flush()
            default_steps = [
                RepairFlowStep(flow_id=default_flow.id, step_order=1, step_name="车管员派单", action_role="fleet_manager", action_label="派单"),
                RepairFlowStep(flow_id=default_flow.id, step_order=2, step_name="修理厂接单", action_role="repair_shop", action_label="接单"),
                RepairFlowStep(flow_id=default_flow.id, step_order=3, step_name="提交维修明细", action_role="repair_shop", action_label="提交明细"),
                RepairFlowStep(flow_id=default_flow.id, step_order=4, step_name="完成维修", action_role="repair_shop", action_label="完成维修"),
                RepairFlowStep(flow_id=default_flow.id, step_order=5, step_name="车管员验收", action_role="fleet_manager", action_label="验收"),
            ]
            for s in default_steps:
                db.add(s)
            await db.commit()

        await db.commit()
