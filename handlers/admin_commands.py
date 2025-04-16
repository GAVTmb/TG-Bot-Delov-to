import os
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())

import datetime

from aiogram import F, types, Router, Bot
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from sqlalchemy.ext.asyncio import AsyncSession

from keyboards import kb_admin, kb_worker
from keyboards.inline_kb import get_callback_buts

from handlers.admin_authorization import RegistrationAdmin, AddWorkingShift


from database.orm_admin_table_queries import orm_get_admin
from database.orm_worker_table_queries import orm_update_worker_access, orm_get_worker, orm_get_all_workers
from database.orm_working_shift_table_queries import (orm_add_working_shift, orm_update_working_shift,
                                                      orm_get_upcoming_working_shifts, orm_get_working_shift,
                                                      orm_get_past_work_shifts)
from database.orm_work_shift_worker_table_queries import orm_update_approval_admin

from additional_functions import sending_shifts_workers, generation_text_shifts_workers


admin_commands_router = Router()


# Отлавливает нажатие кнопки "Посмотреть смены"
@admin_commands_router.message(F.text == "Посмотреть смены")
async def show_all_working_change_admin(message: types.Message, session: AsyncSession, bot: Bot):
    await message.answer(f"Какие смены вам показать?",
                         reply_markup=get_callback_buts(buts={"Предстоящие": f"upcomingworkshifts_",
                                                              "Прошедшие": f"pastworkshifts_",},
                                                        sizes=(2,))
                         )

# Отлавливает нажатие кнопки "➡Посмотреть мои данные"
@admin_commands_router.message(F.text == "➡Посмотреть мои данные")
async def view_data_admin(message: types.Message, session: AsyncSession):
    admin = await orm_get_admin(session, str(message.from_user.id))
    await message.answer(f"❗ Ваши данные ❗\n"
                         f"Телегам id: {admin.tg_id_admin}\n"
                         f"Имя: {admin.name}\n"
                         f"Фамилия: {admin.surname}\n"
                         f"Номер тел-а: +7{admin.phone_number}",
                         reply_markup=get_callback_buts(buts={
                             "➡Изменить мои данные⬅": f"changedataadmin_{str(message.from_user.id)}",},
                                   sizes=(1,))
    )

# Отлавливает нажатие кнопки "Посмотреть работников"
@admin_commands_router.message(F.text == "Посмотреть работников")
async def view_data_worker(message: types.Message, session: AsyncSession):
    print("view_data_worker")
    workers = await orm_get_all_workers(session)
    for worker in workers:
        print(worker)
        await message.answer(f"Телегам id: {worker.tg_id_worker}\n"
                             f"Имя: {worker.name_worker}\n"
                             f"Фамилия: {worker.surname_worker}\n"
                             f"Возраст: {worker.age_worker}\n"
                             f"Опыт работы: {worker.work_experience}\n"
                             f"Номер тел-а: +7{worker.phone_number_worker}",
                             reply_markup=get_callback_buts(buts={
                                 "Заблокировать": f"blockworker_{str(worker.tg_id_worker)}",
                                 "Разблокировать": f"unblockworker_{str(worker.tg_id_worker)}",},
                                 sizes=(2,))
                             )

# Отлавливает нажатие кнопки "➡Изменить мои данные⬅"
@admin_commands_router.callback_query(StateFilter(None), F.data.startswith("changedataadmin_"))
async def change_data_admin(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    tg_id_admin = callback.data.split("_")[-1]
    admin = await orm_get_admin(session, str(tg_id_admin))
    RegistrationAdmin.admin_data_for_change = admin
    await state.set_state(RegistrationAdmin.name)
    await callback.answer()
    await callback.message.answer("Напиши свое имя.",
                                  reply_markup=kb_admin.kb_cancel_back_skip_admin.as_markup(resize_keyboard=True))


# Отлавливает нажатие кнопки Принять!✅
@admin_commands_router.callback_query(StateFilter(None), F.data.startswith("acceptworker_"))
async def accept_worker(callback: types.CallbackQuery, bot: Bot, session: AsyncSession):
    tg_id_worker = callback.data.split("_")[-1]
    worker = await orm_get_worker(session, str(tg_id_worker))
    await orm_update_worker_access(session, str(tg_id_worker), True)
    await bot.send_message(int(tg_id_worker), f"Ваша заявка подтверждена✅\nПоздравляем! Вам открыт доступ к сменам!",
                           reply_markup=kb_worker.kb_start_worker.as_markup(resize_keyboard=True))
    await callback.answer()
    await callback.message.answer(f"Заявка {worker.name_worker} {worker.surname_worker} принята✅"
                                  f"\nДоступ к сменам открыт!")


# Отлавливает нажатие кнопки Отклонить!❌
@admin_commands_router.callback_query(StateFilter(None), F.data.startswith("notacceptworker_"))
async def reject_worker(callback: types.CallbackQuery, bot: Bot, session: AsyncSession):
    tg_id_worker = callback.data.split("_")[-1]
    worker = await orm_get_worker(session, str(tg_id_worker))
    await orm_update_worker_access(session, str(tg_id_worker), False)
    await bot.send_message(int(tg_id_worker), f"Ваша заявка отклонена❌\nОбратитесь к менеджеру",
                           reply_markup=kb_worker.kb_contact_manager_view_worker.as_markup(resize_keyboard=True))
    await callback.answer()
    await callback.message.answer(f"Заявка {worker.name_worker} {worker.surname_worker} Отклонена❌"
                                  f"\nДоступ к сменам закрыт!")


# Отлавливает нажатие кнопки "✅Одобрить"
@admin_commands_router.callback_query(StateFilter(None), F.data.startswith("allowshift_"))
async def allow_shift_worker(callback: types.CallbackQuery, bot: Bot, session: AsyncSession):
    working_shift_id = callback.data.split("_")[-2]
    tg_id_worker = callback.data.split("_")[-1]
    working_shift = await orm_get_working_shift(session, int(working_shift_id))
    await orm_update_approval_admin(session, str(tg_id_worker), int(working_shift_id), True)
    await callback.answer()
    await bot.send_message(tg_id_worker,
                           f"Менеджер вас одобрил✅\n"
                            f"Ждём вас {working_shift.date_time_working_shift.strftime("%d.%m.20%y")} "
                            f"в {working_shift.date_time_working_shift.strftime("%H:%M")}\n"
                            f"По адресу {working_shift.address}")


# Отлавливает нажатие кнопки "❌Отказать"
@admin_commands_router.callback_query(StateFilter(None), F.data.startswith("notallowshift_"))
async def not_allow_shift_worker(callback: types.CallbackQuery, bot: Bot, session: AsyncSession):
    working_shift_id = callback.data.split("_")[-2]
    tg_id_worker = callback.data.split("_")[-1]
    working_shift = await orm_get_working_shift(session, int(working_shift_id))
    text = await generation_text_shifts_workers(working_shift)
    await orm_update_approval_admin(session, str(tg_id_worker), int(working_shift_id), False)
    await callback.answer()
    await bot.send_message(tg_id_worker,
                           f"❌Менеджер вам отказал❌\n{text}")


# Отлавливает нажатие кнопки "Предстоящие". Выдает предстоящие рабочие смены.
@admin_commands_router.callback_query(StateFilter(None), F.data.startswith("upcomingworkshifts_"))
async def upcoming_work_shifts(callback: types.CallbackQuery, session: AsyncSession):
    for upcoming_work_shift in await orm_get_upcoming_working_shifts(session):
        admin = await orm_get_admin(session, str(upcoming_work_shift.tg_id_admin))
        text = await generation_text_shifts_workers(upcoming_work_shift)
        await callback.message.answer(f"➡Предстоящие смены⬅\n"
                                      f"Смену создал(а): {admin.name} {admin.surname}\n☎+7{admin.phone_number}\n"
                                      f"{text}")
    await callback.answer()


# Отлавливает нажатие кнопки "Прошедшие". Выдает прошедшие рабочие смены.
@admin_commands_router.callback_query(StateFilter(None), F.data.startswith("pastworkshifts_"))
async def past_work_shifts(callback: types.CallbackQuery, session: AsyncSession):
    for past_work_shift in await orm_get_past_work_shifts(session):
        admin = await orm_get_admin(session, str(past_work_shift.tg_id_admin))
        text = await generation_text_shifts_workers(past_work_shift)
        await callback.message.answer(f"➡Прошедшие смены⬅\n"
                                      f"Смену создал(а): {admin.name} {admin.surname}\n☎+7{admin.phone_number}\n"
                                      f"{text}")
    await callback.answer()


# Отлавливает нажатие кнопки "Добавить смену". Входит в режим FSM, отправляет сообщение пользователю
# "Напиши дату". Становится в состояние "date_time_working_shift"
@admin_commands_router.message(StateFilter(None), F.text == "Добавить смену💬")
async def start_fsm_admin(message: types.Message, state: FSMContext):
    await message.answer("Давай добавим смену!!!\nНапиши дату 📆 и время⌚\nВ формате 01.01.25 10:00",
                         reply_markup=kb_admin.kb_cancel_admin.as_markup(resize_keyboard=True))
    await state.set_state(AddWorkingShift.date_time_working_shift)


# Отлавливает сообщение написанное в режиме "date_time_working_shift" и сохраняет. Отправляет сообщение "Напиши адрес 🏠".
# Становится в состояние "time_shift"
@admin_commands_router.message(StateFilter(AddWorkingShift.date_time_working_shift), or_f(F.text, F.text == "_Пропустить_"))
async def add_date_shift_admin(message: types.Message, state: FSMContext):
    tg_id_admin = message.from_user.id
    await state.update_data(tg_id_admin=str(tg_id_admin))
    print(message.text)
    try:
        if message.text == "_Пропустить_":
            await state.update_data(date_working_shift=AddWorkingShift.shift_for_working_change.date_working_shift)
            await message.answer("Напиши адрес 🏠",
                                 reply_markup=kb_admin.kb_cancel_back_skip_admin.as_markup(resize_keyboard=True))
        else:
            result = datetime.datetime.strptime(message.text, "%d.%m.%y %H:%M")
            print(f"!!!!!{type(result)}!!!!!")
            print(result)
            await state.update_data(date_working_shift=result)
            if AddWorkingShift.shift_for_working_change is None:
                await message.answer("Напиши адрес 🏠",
                                     reply_markup=kb_admin.kb_cancel_back_admin.as_markup(resize_keyboard=True))
            else:
                await message.answer("Напиши адрес 🏠",
                                     reply_markup=kb_admin.kb_cancel_back_skip_admin.as_markup(resize_keyboard=True))
        await state.set_state(AddWorkingShift.address)
    except Exception as error:
        print(error)
        await message.answer(f"Ошибка:{str(error)}\nВы ввели недопустимые значения!\n"
                             f"Напиши дату 📆 и время⌚\nВ формате 01.01.25 10:00")


# Отлавливает сообщение написанное в режиме "address" и сохраняет. Отправляет сообщение "Напиши описание!".
# Становится в состояние "description_shift"
@admin_commands_router.message(StateFilter(AddWorkingShift.address), or_f(F.text, F.text == "_Пропустить_"))
async def add_address_admin(message: types.Message, state: FSMContext):
    print(message.text)
    if message.text == "_Пропустить_":
        await state.update_data(address=AddWorkingShift.shift_for_working_change.address)
        await message.answer("Напиши описание 📝",
                             reply_markup=kb_admin.kb_cancel_back_skip_admin.as_markup(resize_keyboard=True))
    else:
        await state.update_data(address=message.text)
        if AddWorkingShift.shift_for_working_change is None:
            await message.answer("Напиши описание 📝",
                                 reply_markup=kb_admin.kb_cancel_back_admin.as_markup(resize_keyboard=True))
        else:
            await message.answer("Напиши описание 📝",
                                 reply_markup=kb_admin.kb_cancel_back_skip_admin.as_markup(resize_keyboard=True))
    await state.set_state(AddWorkingShift.description_working_shift)


# Отлавливает сообщение написанное в режиме "description_working_shift" и сохраняет. Отправляет сообщение
# "Напиши кол-во работников!". Становится в состояние "quantity_workers"
@admin_commands_router.message(StateFilter(AddWorkingShift.description_working_shift), or_f(F.text, F.text == "_Пропустить_"))
async def add_description_shift_admin(message: types.Message, state: FSMContext):
    print(message.text)
    try:
        if message.text == "_Пропустить_":
            await state.update_data(description_working_shift=AddWorkingShift.shift_for_working_change.description_working_shift)
            await message.answer("Напиши кол-во работников!",
                                 reply_markup=kb_admin.kb_cancel_back_skip_admin.as_markup(resize_keyboard=True))
        else:
            await state.update_data(description_working_shift=message.text)
            if AddWorkingShift.shift_for_working_change is None:
                await message.answer("Напиши кол-во работников!",
                                     reply_markup=kb_admin.kb_cancel_back_admin.as_markup(resize_keyboard=True))
            else:
                await message.answer("Напиши кол-во работников!",
                                     reply_markup=kb_admin.kb_cancel_back_skip_admin.as_markup(resize_keyboard=True))
        await state.set_state(AddWorkingShift.quantity_workers)
    except Exception as error:
        print(error)
        await message.answer(f"Ошибка:{str(error)}\nВы ввели недопустимые значения. "
                             f"Напиши Напиши описание!",
                             reply_markup=kb_admin.kb_cancel_back_admin.as_markup(resize_keyboard=True))


# Отлавливает сообщение написаное в режиме "quantity_workers" и сохраняет. Отправляет сообщение
# "Напиши кол-во работников!". Становится в состояние "cost_work"
@admin_commands_router.message(StateFilter(AddWorkingShift.quantity_workers), or_f(F.text, F.text == "_Пропустить_"))
async def add_quantity_workers_admin(message: types.Message, state: FSMContext):
    print(message.text)
    try:
        if message.text == "_Пропустить_":
            await state.update_data(quantity_workers=AddWorkingShift.shift_for_working_change.quantity_workers)
            await message.answer("Напиши стоимость 💰",
                                 reply_markup=kb_admin.kb_cancel_back_skip_admin.as_markup(resize_keyboard=True))
        else:
            quantity_workers_int = int(message.text)
            await state.update_data(quantity_workers=quantity_workers_int)
            if AddWorkingShift.shift_for_working_change is None:
                await message.answer("Напиши стоимость 💰",
                                     reply_markup=kb_admin.kb_cancel_back_admin.as_markup(resize_keyboard=True))
            else:
                await message.answer("Напиши стоимость 💰",
                                     reply_markup=kb_admin.kb_cancel_back_skip_admin.as_markup(resize_keyboard=True))
        await state.set_state(AddWorkingShift.cost_work)
    except Exception as error:
        print(error)
        await message.answer(f"Ошибка:{str(error)}\nВы ввели недопустимые значения. "
                             f"Напиши кол-во работников!",
                             reply_markup=kb_admin.kb_cancel_back_admin.as_markup(resize_keyboard=True))


# Отправляет сообщение пользователю, что все добавлено. Формирует словарь с данными отправляет в БД.
# После чего удаляет из памяти и выходит из режима FSM.
@admin_commands_router.message(StateFilter(AddWorkingShift.cost_work), F.text)
async def add_cost_work_admin(message: types.Message, state: FSMContext, session: AsyncSession, bot: Bot):
    admin = await orm_get_admin(session, str(message.from_user.id))
    try:
        if message.text == "_Пропустить_":
            await state.update_data(cost_work=AddWorkingShift.shift_for_working_change.cost_work)
        else:
            cost_work_int = int(message.text)
            await state.update_data(cost_work=cost_work_int)
        data = await state.get_data()
        print(data)

        if AddWorkingShift.shift_for_working_change:
            await orm_update_working_shift(session, AddWorkingShift.shift_for_working_change.id, data)
            if admin.admin_access:
                await message.answer("Смена изменена!✅",
                                     reply_markup=kb_admin.start_kb_admin.as_markup(resize_keyboard=True))
            else:
                await message.answer("Смена изменена!✅",
                                     reply_markup=kb_admin.start_kb_main_admin.as_markup(resize_keyboard=True))
        else:
            await orm_add_working_shift(session, data)
            await sending_shifts_workers(session, bot)
            if admin.admin_access:
                await message.answer("Смена добавлена!✅",
                                     reply_markup=kb_admin.start_kb_admin.as_markup(resize_keyboard=True))
            else:
                await message.answer("Смена добавлена!✅",
                                     reply_markup=kb_admin.start_kb_main_admin.as_markup(resize_keyboard=True))
        await state.clear()
        AddWorkingShift.shift_for_working_change = None
    except Exception as error:
        await message.answer(f"Ошибка:\n{str(error)}\nВы ввели недопустимые значения. "
                             f"Напиши стоимость",
                             reply_markup=kb_admin.kb_cancel_back_admin.as_markup(resize_keyboard=True))


@admin_commands_router.message(F.text == "Выход")
async def exit_admin(message: types.Message):
    await message.answer("Досвидания!", reply_markup=kb_worker.kb_start.as_markup(resize_keyboard=True))

