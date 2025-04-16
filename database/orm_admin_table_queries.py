from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Admin


# Добавляет админа в БД. На вход принимает словарь с данными.
async def orm_add_admin(session: AsyncSession, data: dict):
    obj = Admin(
        tg_id_admin=data["tg_id_admin"],
        name=data["name"],
        surname=data["surname"],
        phone_number=data["phone_number"],
        admin_access=data["admin_access"],
        main_admin=data["main_admin"],
    )
    session.add(obj)
    await session.commit()

# Изменение данных администратора.
async def orm_update_admin(session: AsyncSession, admin_id: int, data):
    query = update(Admin).where(Admin.id == admin_id).values(
        tg_id_admin=data["tg_id_admin"],
        name=data["name"],
        surname=data["surname"],
        phone_number=data["phone_number"],
        admin_access=data["admin_access"],
        main_admin=data["main_admin"],
    )
    await session.execute(query)
    await session.commit()


# Находит Админа по телеграм id
async def orm_get_admin(session: AsyncSession, tg_id_admin: str):
    query = select(Admin).where(Admin.tg_id_admin == tg_id_admin)
    result = await session.execute(query)
    return result.scalar()


# Находит Телегам id всех админов (Простых админов).
async def orm_get_all_tg_id_admin(session: AsyncSession):
    query = select(Admin.tg_id_admin).where(Admin.main_admin != True)
    result = await session.execute(query)
    return result.scalars().all()


# Находит всех админов (Простых админов).
async def orm_get_all_admin(session: AsyncSession):
    query = select(Admin).where(Admin.main_admin != True)
    result = await session.execute(query)
    return result.scalars().all()


# Изменяет значение в admin_access у определенного админа.
# На вход принимает телеграм id и новое значение True или False
async def orm_update_admin_access(session: AsyncSession, tg_id_admin: str, data: bool):
    query = update(Admin).where(Admin.tg_id_admin == tg_id_admin).values(
        admin_access=data,)
    await session.execute(query)
    await session.commit()










