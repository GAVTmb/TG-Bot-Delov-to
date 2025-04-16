from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import WorkShiftWorker


# Добавление новой рабочей смены в БД через админку.
async def orm_add_work_shift_worker(session: AsyncSession, working_shift_id: int, tg_id_worker: str,
                                    going_on_shift: bool, approval_admin: bool | None):
    obj = WorkShiftWorker(working_shift_id=working_shift_id,
                          tg_id_worker= tg_id_worker,
                          going_on_shift= going_on_shift,
                          approval_admin= approval_admin,)
    session.add(obj)
    await session.commit()


async def orm_update_approval_admin(session: AsyncSession, tg_id: str, w_s_id: int, data: bool):
    query = update(WorkShiftWorker).where(WorkShiftWorker.working_shift_id == w_s_id,
                                          WorkShiftWorker.tg_id_worker == tg_id). values(
        approval_admin=data,)
    await session.execute(query)
    await session.commit()


async def orm_update_going_on_shift(session: AsyncSession, tg_id: str, w_s_id: int, data: bool):
    query = update(WorkShiftWorker).where(WorkShiftWorker.working_shift_id == w_s_id,
                                          WorkShiftWorker.tg_id_worker == tg_id). values(
        going_on_shift=data,)
    await session.execute(query)
    await session.commit()


async def orm_get_work_shift_worker(session: AsyncSession, tg_id: str, w_s_id: int):
    query = select(WorkShiftWorker).where(WorkShiftWorker.working_shift_id == w_s_id,
                                          WorkShiftWorker.tg_id_worker == tg_id)
    result = await session.execute(query)
    return result.scalar()
