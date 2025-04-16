from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Worker


# Добавляет Работника в БД. На вход принимает словарь с данными.
async def orm_add_worker(session: AsyncSession, data: dict):
    obj = Worker(
        tg_id_worker=data["tg_id_worker"],
        name_worker=data["name_worker"],
        surname_worker=data["surname_worker"],
        age_worker=data["age_worker"],
        work_experience=data["work_experience"],
        phone_number_worker=data["phone_number_worker"],
        passport_photo_worker=data["passport_photo_worker"],
        access_worker=data["access_worker"],
    )
    session.add(obj)
    await session.commit()


# Изменение данных Работника
async def orm_update_worker(session: AsyncSession, worker_id: int, data):
    query = update(Worker).where(Worker.id == worker_id).values(
        tg_id_worker=data["tg_id_worker"],
        name_worker=data["name_worker"],
        surname_worker=data["surname_worker"],
        age_worker=data["age_worker"],
        work_experience=data["work_experience"],
        phone_number_worker=data["phone_number_worker"],
        passport_photo_worker=data["passport_photo_worker"],
        access_worker=data["access_worker"],
    )
    await session.execute(query)
    await session.commit()



# Изменяет значение в "access_worker" у определенного работника.
# На вход принимает телеграм id и новое значение True или False
async def orm_update_worker_access(session: AsyncSession, tg_id: str, data: bool):
    query = update(Worker).where(Worker.tg_id_worker == tg_id).values(
        access_worker=data,)
    await session.execute(query)
    await session.commit()


# Находит работника по телеграм id
async def orm_get_worker(session: AsyncSession, tg_id: str):
    query = select(Worker).where(Worker.tg_id_worker == tg_id)
    result = await session.execute(query)
    return result.scalar()


# Находит Телегам id всех работников.
async def orm_get_all_tg_id_workers(session: AsyncSession):
    query = select(Worker.tg_id_worker).where(Worker.access_worker == True)
    result = await session.execute(query)
    return result.scalars().all()


# Находит всех работников.
async def orm_get_all_workers(session: AsyncSession):
    query = select(Worker)
    result = await session.execute(query)
    return result.scalars().all()
