from aiogram import Bot, types
import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from database.engine import engine
from database.orm_admin_table_queries import orm_get_admin
from database.orm_sending_reminders_about_work_shifts_queries import orm_get_upcoming_working_shifts_for_sending, \
    orm_get_all_work_shift_worker_for_sending
from database.orm_worker_table_queries import orm_get_all_tg_id_workers
from database.orm_working_shift_table_queries import orm_get_all_working_shifts, orm_get_upcoming_working_shifts
from keyboards.inline_kb import get_callback_buts


async def generation_text_shifts_workers(working_shift):
    text = (f"Дата📆: {working_shift.date_time_working_shift.strftime("%d.%m.20%y")}\n"
            f"Время начала⌚: {working_shift.date_time_working_shift.strftime("%H:%M")}\n"
            f"Адрес🏠: {working_shift.address}\n"
            f"Описание: {working_shift.description_working_shift}\n"
            f"Нужно {working_shift.quantity_workers} чел.\n"
            f"Оплата: {working_shift.cost_work}руб.")
    return text


async def sending_new_shift_workers(session: AsyncSession, bot):
    list_tg_id_workers = await orm_get_all_tg_id_workers(session)
    list_working_shift = await orm_get_all_working_shifts(session)
    working_shift = list_working_shift[-1]
    admin = await orm_get_admin(session, str(working_shift.tg_id_admin))
    text = await generation_text_shifts_workers(working_shift)

    for tg_id_worker in list_tg_id_workers:
        await bot.send_message(int(tg_id_worker), f"❗❗❗ Новая смена ❗❗❗\n"
                                                  f"{text}"
                                                  f"Для уточнения деталей свяжитесь с менеджером!\n"
                                                  f"{admin.name} - ☎+7{admin.phone_number}",
                               reply_markup=get_callback_buts(buts={"✅Еду на смену": f"yes_{working_shift.id}",
                                                                    "❌Не могу": f"no_{working_shift.id}"},
                                                              sizes=(2, ))
                               )


async def sending_update_shift_workers(session: AsyncSession, bot, data):
    admin = await orm_get_admin(session, str(data.tg_id_admin))
    list_tg_id_workers = await orm_get_all_tg_id_workers(session)
    text = await generation_text_shifts_workers(data)

    for tg_id_worker in list_tg_id_workers:
        await bot.send_message(int(tg_id_worker), f"❗❗❗ Смена была изменена ❗❗❗\n"
                                                  f"{text}"
                                                  f"Для уточнения деталей свяжитесь с менеджером!\n"
                                                  f"{admin.name} - ☎+7{admin.phone_number}")


async def sending_reminders_about_work_shifts(bot: Bot):
    upcoming_working_shifts = await orm_get_upcoming_working_shifts_for_sending()
    for upcoming_working_shift in upcoming_working_shifts:
        text_message = await generation_text_shifts_workers(upcoming_working_shift)
        for tg_id_worker in await orm_get_all_work_shift_worker_for_sending(int(upcoming_working_shift.id)):
            await bot.send_message(int(tg_id_worker), f"❗Напоминаем вы записаны на смену❗\n\n"
                                                      f"{text_message}\n\n❗Время начала➡ "
                                                      f"{upcoming_working_shift.date_time_working_shift.strftime("%H:%M")}❗")


