from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import WorkingShift

import datetime


# Добавление новой рабочей смены в БД через админку.
async def orm_add_working_shift(session: AsyncSession, data: dict):
    obj = WorkingShift(
        tg_id_admin=data["tg_id_admin"],
        date_time_working_shift=data["date_working_shift"],
        address=data["address"],
        description_working_shift=data["description_working_shift"],
        quantity_workers=data["quantity_workers"],
        cost_work=data["cost_work"],
    )
    session.add(obj)
    await session.commit()


# Изменеие существующей рабочей смены.
async def orm_update_working_shift(session: AsyncSession, working_shift_id: int, data):
    query = update(WorkingShift).where(WorkingShift.id == working_shift_id).values(
        tg_id_admin=data["tg_id_admin"],
        date_time_working_shift=data["date_working_shift"],
        address=data["address"],
        description_working_shift=data["description_working_shift"],
        quantity_workers=data["quantity_workers"],
        cost_work=data["cost_work"],
    )
    await session.execute(query)
    await session.commit()


# Выдает все рабочей смены.
async def orm_get_all_working_shifts(session: AsyncSession):
    query = select(WorkingShift)
    result = await session.execute(query)
    return result.scalars().all()


# Находит и выдает предстоящие смены.
async def orm_get_upcoming_working_shifts(session: AsyncSession):
    query = select(WorkingShift).where(WorkingShift.date_time_working_shift > datetime.datetime.today())
    result = await session.execute(query)
    return result.scalars().all()



# Находит и выдает прошедшие смены.
async def orm_get_past_work_shifts(session: AsyncSession):
    query = select(WorkingShift).where(WorkingShift.date_time_working_shift < datetime.datetime.today())
    result = await session.execute(query)
    return result.scalars().all()


# Находит и выдает смену по id.
async def orm_get_working_shift(session: AsyncSession, working_shift_id: int):
    query = select(WorkingShift).where(WorkingShift.id == working_shift_id)
    result = await session.execute(query)
    return result.scalar()


# Удалить смену
async def orm_delete_working_shift(session: AsyncSession, working_shift_id: int):
    query = delete(WorkingShift).where(WorkingShift.id == working_shift_id)
    await session.execute(query)
    await session.commit()

