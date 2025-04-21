import datetime

from sqlalchemy import select

from database.engine import engine, session_maker
from database.models import WorkingShift, WorkShiftWorker


# Находит и выдает предстоящие смены.
async def orm_get_upcoming_working_shifts_for_sending():
    async with session_maker() as session:
        now = datetime.datetime.now()
        time_threshold = now + datetime.timedelta(hours=1)
        query = (select(WorkingShift).
                 where(WorkingShift.date_time_working_shift.between(now, time_threshold)))
        result = await session.execute(query)
        return result.scalars().all()


async def orm_get_all_work_shift_worker_for_sending( work_shift_id: int):
    async with session_maker() as session:
        query = select(WorkShiftWorker.tg_id_worker).where(WorkShiftWorker.working_shift_id == work_shift_id,
                                                           WorkShiftWorker.approval_admin == True)
        result = await session.execute(query)
        return result.scalars().all()
