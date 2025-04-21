
from aiogram import F, types, Router, Bot
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from sqlalchemy.ext.asyncio import AsyncSession

from keyboards import kb_admin, kb_worker
from keyboards.inline_kb import get_callback_buts

from database.orm_worker_table_queries import orm_get_worker
from database.orm_admin_table_queries import orm_get_all_admin, orm_get_admin
from database.orm_working_shift_table_queries import orm_get_upcoming_working_shifts, orm_get_working_shift
from database.orm_work_shift_worker_table_queries import orm_add_work_shift_worker, orm_get_work_shift_worker, \
    orm_update_going_on_shift, orm_get_all_work_shift_worker

from handlers.worker_authorization import RegistrationWorker

from additional_functions import generation_text_shifts_workers

worker_commands_router = Router()


@worker_commands_router.message(F.text == "♻Посмотреть мои данные♻")
async def view_data_worker(message: types.Message, session: AsyncSession):
    worker = await orm_get_worker(session, str(message.from_user.id))
    await message.answer_photo(worker.passport_photo_worker,
                               f"❗ Ваши данные ❗\n"
                               f"Телегам id: {worker.tg_id_worker}\n"
                               f"Имя: {worker.name_worker}\n"
                               f"Фамилия: {worker.surname_worker}\n"
                               f"Возраст: {worker.age_worker}\n"
                               f"Опыт работы: {worker.work_experience}\n"
                               f"Номер тел-а: +7{worker.phone_number_worker}",
                               reply_markup=get_callback_buts(buts={
                                   "♻Изменить мои данные♻": f"changedataworker_{str(message.from_user.id)}",},
                                   sizes=(1,))
                               )


@worker_commands_router.callback_query(StateFilter(None), F.data.startswith("changedataworker_"))
async def change_data_worker(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    tg_id_worker = callback.data.split("_")[-1]
    worker = await orm_get_worker(session, str(tg_id_worker))
    RegistrationWorker.worker_data_for_change = worker
    await state.set_state(RegistrationWorker.name_worker)
    await callback.answer()
    await callback.message.answer("Напиши свое имя.",
                         reply_markup=kb_worker.kb_cancel_back_skip_worker.as_markup(resize_keyboard=True))


@worker_commands_router.message(F.text == "☎Связаться с менеджером☎")
async def contact_manager(message: types.Message, session: AsyncSession):
    try:
        list_contact_manager = []
        for manager in await orm_get_all_admin(session):
            text = f"➡{manager.name} - ☎+7{manager.phone_number}\n"
            list_contact_manager.append(text)
        await message.answer(f"{"".join(list_contact_manager)}")
    except Exception as error:
        print(error)
        await message.answer(f"Ошибка!!!\nМенеджеров еще нет!")


@worker_commands_router.message(F.text == "❗Посмотреть смены❗")
async def shifts_today(message: types.Message, session: AsyncSession):
    working_shifts = await orm_get_upcoming_working_shifts(session)
    if working_shifts:
        for working_shift in working_shifts:
            work_shift_workers = await orm_get_all_work_shift_worker(session, working_shift.id)
            admin = await orm_get_admin(session, str(working_shift.tg_id_admin))
            text = await generation_text_shifts_workers(working_shift)
            if str(message.from_user.id) in work_shift_workers:
                await message.answer(f"❗Предстояшие смены❗\n{text}\n"
                                     f"Для уточнения деталей свяжитесь с менеджером!\n"
                                     f"{admin.name} - ☎+7{admin.phone_number}\n\n"
                                     f"Вы записаны на эту смену!"
                                     )
            else:
                await message.answer(f"❗Предстояшие смены❗\n{text}\n"
                                     f"Для уточнения деталей свяжитесь с менеджером!\n"
                                     f"{admin.name} - ☎+7{admin.phone_number}",
                                     reply_markup=get_callback_buts(buts={"✅Еду на смену": f"yes_{working_shift.id}",
                                                                          "❌Не могу": f"no_{working_shift.id}"},
                                                                    sizes=(2, )))
    else:
        await message.answer("Предстоящих смен еще нет.")


@worker_commands_router.callback_query(F.data.startswith("yes_"))
async def going_on_shift(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    working_shift_id = callback.data.split("_")[-1]
    worker = await orm_get_worker(session, str(callback.from_user.id))
    working_shift = await orm_get_working_shift(session, int(working_shift_id))
    work_shift_workers = await orm_get_all_work_shift_worker(session, working_shift.id)
    work_shift_worker = await orm_get_work_shift_worker(session, str(callback.from_user.id), int(working_shift_id))
    message_text = (f"➡{worker.name_worker} {worker.surname_worker}⬅\n☎+7{worker.phone_number_worker}\n"
                    f"Готов выйти на смену!\n\n"
                    f"Дата📆: {working_shift.date_time_working_shift.strftime("%d.%m.20%y")}\n"
                    f"Время начала⌚: {working_shift.date_time_working_shift.strftime("%H:%M")}\n"
                    f"Адрес🏠: {working_shift.address}\n"
                    f"Описание: {working_shift.description_working_shift}\n")
    if len(work_shift_workers) < working_shift.quantity_workers:
        if work_shift_worker:
            if work_shift_worker.going_on_shift:
                await callback.message.answer("Вы уже записаны на эту смену!")
            else:
                await orm_update_going_on_shift(session, str(callback.from_user.id), int(working_shift_id), True)
                await callback.message.edit_text(f"{callback.message.text}\n\n"
                                                 f"Заявка отправлена, ожидайте ответа от менеджера.")
                await bot.send_message(working_shift.tg_id_admin, message_text,
                                       reply_markup=get_callback_buts(buts={"✅Одобрить": f"allowshift_{working_shift_id}_"
                                                                                         f"{worker.tg_id_worker}",
                                                                            "❌Отказать": f"notallowshift_{working_shift_id}_"
                                                                                         f"{worker.tg_id_worker}"},
                                                                      sizes=(2,))
                                       )
        else:
            await orm_add_work_shift_worker(session, int(working_shift_id), str(callback.from_user.id),
                                            True, None)
            await callback.message.edit_text(f"{callback.message.text}\n\n"
                                             f"Заявка отправлена, ожидайте ответа от менеджера.")
            await bot.send_message(working_shift.tg_id_admin, message_text,
                                   reply_markup=get_callback_buts(buts={"✅Одобрить": f"allowshift_{working_shift_id}_"
                                                                                     f"{worker.tg_id_worker}",
                                                                        "❌Отказать": f"notallowshift_{working_shift_id}_"
                                                                                       f"{worker.tg_id_worker}"},
                                                                  sizes=(2,))
                                   )
    else:
        await callback.message.edit_text(f"{callback.message.text}\n\n"
                                         f"Вы не можете записаться. Работники в эту смену уже набраны.")
    await callback.answer()


@worker_commands_router.callback_query(F.data.startswith("no_"))
async def going_on_shift(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    working_shift_id = callback.data.split("_")[-1]
    worker = await orm_get_worker(session, str(callback.from_user.id))
    working_shift = await orm_get_working_shift(session, int(working_shift_id))
    await orm_add_work_shift_worker(session, int(working_shift_id), str(callback.from_user.id),
                                    False, None)
    await bot.send_message(working_shift.tg_id_admin,
                           f"➡{worker.name_worker} {worker.surname_worker}⬅\n☎+7{worker.phone_number_worker}\n"
                           f"Не готов выйти на смену!\n\n"
                           f"Дата📆: {working_shift.date_time_working_shift.strftime("%d.%m.20%y")}\n"
                           f"Время начала⌚: {working_shift.date_time_working_shift.strftime("%H:%M")}\n"
                           f"Адрес🏠: {working_shift.address}\n"
                           f"{working_shift.description_working_shift}\n")
    await callback.answer()
