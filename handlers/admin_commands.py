
import datetime

from aiogram import F, types, Router, Bot
from aiogram.filters import StateFilter, or_f
from aiogram.fsm.context import FSMContext

from sqlalchemy.ext.asyncio import AsyncSession

from keyboards import kb_admin, kb_worker
from keyboards.inline_kb import get_callback_buts

from handlers.admin_authorization import RegistrationAdmin, AddWorkingShift, ChangePassword, ADMIN_PASSWORD

from database.orm_admin_table_queries import orm_get_admin, orm_get_all_admin, orm_update_admin_access
from database.orm_worker_table_queries import orm_update_worker_access, orm_get_worker, orm_get_all_workers
from database.orm_working_shift_table_queries import (orm_add_working_shift, orm_update_working_shift,
                                                      orm_get_upcoming_working_shifts, orm_get_working_shift,
                                                      orm_get_past_work_shifts, orm_delete_working_shift)
from database.orm_work_shift_worker_table_queries import orm_get_all_work_shift_worker, orm_update_going_on_shift_approval_admin

from additional_functions import sending_new_shift_workers, generation_text_shifts_workers, sending_update_shift_workers

admin_commands_router = Router()


# Отлавливает нажатие кнопки "Посмотреть смены🛠"
@admin_commands_router.message(F.text == "Посмотреть смены🛠")
async def show_all_working_change_admin(message: types.Message, session: AsyncSession, bot: Bot):
    await message.answer(f"Какие смены вам показать?",
                         reply_markup=get_callback_buts(buts={"➡Предстоящие": f"upcomingworkshifts_",
                                                              "Прошедшие⬅": f"pastworkshifts_",},
                                                        sizes=(2,))
                         )

# Отлавливает нажатие кнопки "🔎Посмотреть мои данные"
@admin_commands_router.message(F.text == "🔎Посмотреть мои данные")
async def view_data_admin(message: types.Message, session: AsyncSession):
    admin = await orm_get_admin(session, str(message.from_user.id))
    await message.answer(f"❗ Ваши данные ❗\n"
                         f"Телегам id: {admin.tg_id_admin}\n"
                         f"Имя: {admin.name}\n"
                         f"Фамилия: {admin.surname}\n"
                         f"Номер тел-а: +7{admin.phone_number}",
                         reply_markup=get_callback_buts(buts={
                             "Изменить мои данные🔄": f"changedataadmin_{str(message.from_user.id)}",},
                                   sizes=(1,))
    )

# Отлавливает нажатие кнопки "Посмотреть работников‍👷‍♂️"
@admin_commands_router.message(F.text == "Посмотреть работников‍👷‍♂️")
async def view_data_worker(message: types.Message, session: AsyncSession):
    workers = await orm_get_all_workers(session)
    for worker in workers:
        await message.answer(f"{worker.name_worker} {worker.surname_worker}\n"
                             f"Номер тел-а: +7{worker.phone_number_worker}",
                             reply_markup=get_callback_buts(buts={"Подробнее🕵️‍♂️": f"detailed_{str(worker.tg_id_worker)}",},
                                    sizes=(2,))
                             )


# Отлавливает нажатие кнопки "Подробнее"
@admin_commands_router.callback_query(StateFilter(None), F.data.startswith("detailed_"))
async def detailed_view_data_worker(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    tg_id_worker = callback.data.split("_")[-1]
    worker = await orm_get_worker(session, str(tg_id_worker))
    text_message = (f"Информация о работнике:\n"
                    f"-Телегам id: {worker.tg_id_worker}\n"
                    f"-Имя: {worker.name_worker}\n"
                    f"-Фамилия: {worker.surname_worker}\n"
                    f"-Возраст: {worker.age_worker}\n"
                    f"-Опыт работы: {worker.work_experience}\n"
                    f"-Номер тел-а: +7{worker.phone_number_worker}\n\n")
    if worker.access_worker:
        await callback.message.edit_text(f"{text_message}"
                                         f"Работнику доступны смены.✅",
                                         reply_markup=get_callback_buts(buts={
                                             "Заблокировать❌": f"notacceptworker_{str(worker.tg_id_worker)}",},
                                             sizes=(1,))
                                         )
    else:
        await callback.message.edit_text(f"{text_message}"
                                         f"Работник заблокирован, смены не доступны.❌",
                                         reply_markup=get_callback_buts(buts={
                                             "Разблокировать✅": f"acceptworker_{str(worker.tg_id_worker)}", },
                                             sizes=(1,))
                                         )



# Отлавливает нажатие кнопки Принять!✅
@admin_commands_router.callback_query(StateFilter(None), F.data.startswith("acceptworker_"))
async def accept_worker(callback: types.CallbackQuery, bot: Bot, session: AsyncSession):
    tg_id_worker = callback.data.split("_")[-1]
    worker = await orm_get_worker(session, str(tg_id_worker))
    await orm_update_worker_access(session, str(tg_id_worker), True)
    await bot.send_message(int(tg_id_worker), f"Поздравляем! Вам открыт доступ к сменам!✅",
                           reply_markup=kb_worker.kb_start_worker.as_markup(resize_keyboard=True))
    await callback.answer()
    await callback.message.edit_text(f"Работнику {worker.name_worker} {worker.surname_worker}\n"
                                     f"Номер тел-а: +7{worker.phone_number_worker}"
                                     f"\n\nОткрыт доступ к сменам!✅",
                                     reply_markup=get_callback_buts(buts={
                                         "Заблокировать❌": f"notacceptworker_{str(worker.tg_id_worker)}", },
                                         sizes=(1,))
                                     )


# Отлавливает нажатие кнопки Отклонить!❌
@admin_commands_router.callback_query(StateFilter(None), F.data.startswith("notacceptworker_"))
async def reject_worker(callback: types.CallbackQuery, bot: Bot, session: AsyncSession):
    tg_id_worker = callback.data.split("_")[-1]
    worker = await orm_get_worker(session, str(tg_id_worker))
    await orm_update_worker_access(session, str(tg_id_worker), False)
    await bot.send_message(int(tg_id_worker), f"Доступ к сменам закрыт❌\nОбратитесь к менеджеру",
                           reply_markup=kb_worker.kb_contact_manager_view_worker.as_markup(resize_keyboard=True))
    await callback.answer()
    await callback.message.edit_text(f"Работнику {worker.name_worker} {worker.surname_worker}\n"
                                     f"Номер тел-а: +7{worker.phone_number_worker}"
                                     f"\n\nЗакрыт доступ к сменам!❌",
                                     reply_markup=get_callback_buts(buts={
                                         "Разблокировать✅": f"acceptworker_{str(worker.tg_id_worker)}", },
                                         sizes=(1,))
                                     )


# Отлавливает нажатие кнопки "✅Одобрить"
@admin_commands_router.callback_query(StateFilter(None), F.data.startswith("allowshift_"))
async def allow_shift_worker(callback: types.CallbackQuery, bot: Bot, session: AsyncSession):
    message_text = callback.message.text
    working_shift_id = callback.data.split("_")[-2]
    tg_id_worker = callback.data.split("_")[-1]
    working_shift = await orm_get_working_shift(session, int(working_shift_id))
    work_shift_workers = await orm_get_all_work_shift_worker(session, working_shift.id)
    if len(work_shift_workers) < working_shift.quantity_workers:
        await orm_update_going_on_shift_approval_admin(session, str(tg_id_worker), int(working_shift_id),
                                                       True, True)
        await callback.message.edit_text(f"{message_text}\n✅Одобрено!")
        await bot.send_message(tg_id_worker,
                               f"Менеджер вас одобрил✅\n"
                                f"Ждём вас {working_shift.date_time_working_shift.strftime("%d.%m.20%y")} "
                                f"в {working_shift.date_time_working_shift.strftime("%H:%M")}\n"
                                f"По адресу {working_shift.address}")
    else:
        await callback.message.edit_text(f"{callback.message.text}\n\n"
                                         f"❗Работники в эту смену уже набраны.❗")
    await callback.answer()


# Отлавливает нажатие кнопки "❌Отказать"
@admin_commands_router.callback_query(StateFilter(None), F.data.startswith("notallowshift_"))
async def not_allow_shift_worker(callback: types.CallbackQuery, bot: Bot, session: AsyncSession):
    working_shift_id = callback.data.split("_")[-2]
    tg_id_worker = callback.data.split("_")[-1]
    working_shift = await orm_get_working_shift(session, int(working_shift_id))
    await orm_update_going_on_shift_approval_admin(session, str(tg_id_worker), int(working_shift_id),
                                                   True, False)
    await callback.message.edit_text(f"{callback.message.text}\n❌Отказано!")
    await callback.answer()
    await bot.send_message(tg_id_worker,
                           f"❌Менеджер вам отказал❌\n{callback.message.text}")


# Отлавливает нажатие кнопки "Предстоящие". Выдает предстоящие рабочие смены.
@admin_commands_router.callback_query(StateFilter(None), F.data.startswith("upcomingworkshifts_"))
async def upcoming_work_shifts(callback: types.CallbackQuery, session: AsyncSession):
    for upcoming_work_shift in await orm_get_upcoming_working_shifts(session):
        admin = await orm_get_admin(session, str(upcoming_work_shift.tg_id_admin))
        text = await generation_text_shifts_workers(upcoming_work_shift)
        await callback.message.answer(f"➡Предстоящие смены\n"
                                      f"Смену создал(а): {admin.name} {admin.surname}\n☎+7{admin.phone_number}\n"
                                      f"{text}",
                                      reply_markup=get_callback_buts(buts={
                                          "Изменить смену🔄": f"changeshift_{upcoming_work_shift.id}",
                                          "Удалить смену🗑": f"deleteshift_{upcoming_work_shift.id}",
                                          "Посмотреть работников смены👷‍♂️": f"shiftworkers_{upcoming_work_shift.id}",},
                                          sizes=(2, 1))
                                      )
    await callback.answer()


# Отлавливает нажатие кнопки "Прошедшие". Выдает прошедшие рабочие смены.
@admin_commands_router.callback_query(StateFilter(None), F.data.startswith("pastworkshifts_"))
async def past_work_shifts(callback: types.CallbackQuery, session: AsyncSession):
    for past_work_shift in await orm_get_past_work_shifts(session):
        admin = await orm_get_admin(session, str(past_work_shift.tg_id_admin))
        text = await generation_text_shifts_workers(past_work_shift)
        await callback.message.answer(f"Прошедшие смены⬅\n"
                                      f"Смену создал(а): {admin.name} {admin.surname}\n☎+7{admin.phone_number}\n"
                                      f"{text}",
                                      reply_markup=get_callback_buts(buts={
                                          "Посмотреть работников смены👷‍♂️": f"shiftworkers_{past_work_shift.id}", },
                                          sizes=(1,))
                                      )
    await callback.answer()


# Отлавливает нажатие кнопки "Удалить смену".
@admin_commands_router.callback_query(StateFilter(None), F.data.startswith("deleteshift_"))
async def delete_work_shifts(callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    work_shift_id = int(callback.data.split("_")[-1])
    tg_id_workers_list = await orm_get_all_work_shift_worker(session, int(work_shift_id))
    await callback.answer()
    for tg_id_workers in tg_id_workers_list:
        await bot.send_message(int(tg_id_workers), f"🗑❗Эта смена была удалена❗🗑\n\n{callback.message.text}")
    await orm_delete_working_shift(session, work_shift_id)
    await callback.message.edit_text(f"Смена удалена!🗑")



# Отлавливает нажатие кнопки "Посмотреть работников смены".
@admin_commands_router.callback_query(StateFilter(None), F.data.startswith("shiftworkers_"))
async def view_shift_workers(callback: types.CallbackQuery, session: AsyncSession):
    work_shift_id = int(callback.data.split("_")[-1])
    tg_id_workers_list = await orm_get_all_work_shift_worker(session, int(work_shift_id))
    worker_shift = await orm_get_working_shift(session, work_shift_id)
    message_text = callback.message.text
    if tg_id_workers_list:
        text_worker_list = []
        counter = 0
        ikb = None
        if worker_shift.date_time_working_shift > datetime.datetime.now():
            ikb = get_callback_buts(buts={
                                          "Изменить смену🔄": f"changeshift_{worker_shift.id}",
                                          "Удалить смену🗑": f"deleteshift_{worker_shift.id}",},
                                          sizes=(2,))
        for tg_id_worker in tg_id_workers_list:
            counter += 1
            worker = await orm_get_worker(session, str(tg_id_worker))
            print(worker)
            text_worker = f"{counter}. {worker.name_worker} {worker.surname_worker}\n"
            text_worker_list.append(text_worker)
        await callback.message.edit_text(f"{message_text}\n\n"
                                         f"Работники смены!\n"
                                         f"{"".join(text_worker_list)}",
                                         reply_markup=ikb)
    else:
        await callback.message.edit_text(f"{message_text}\n\n"
                                         f"В этой смене еще нет работников.")
    await callback.answer()


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


# Отлавливает нажатие кнопки "changeshift_"
@admin_commands_router.callback_query(StateFilter(None), F.data.startswith("changeshift_"))
async def change_shift(callback: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    work_shift_id = callback.data.split("_")[-1]
    work_shift = await orm_get_working_shift(session, int(work_shift_id))
    AddWorkingShift.shift_for_working_change = work_shift
    await state.set_state(AddWorkingShift.date_time_working_shift)
    await callback.answer()
    await callback.message.answer("Напиши дату 📆 и время⌚\nВ формате 01.01.25 10:00",
                                  reply_markup=kb_admin.kb_cancel_back_skip_admin.as_markup(resize_keyboard=True))


# Отлавливает нажатие кнопки "Посмотреть администраторов".
@admin_commands_router.message(F.text == "Посмотреть адин-в")
async def view_admins(message: types.Message, session: AsyncSession):
    for admin in await orm_get_all_admin(session):
        print(f"{admin.surname} {admin.name}\n т.{admin.phone_number}")
        if admin.admin_access:
            await message.answer(f"{admin.name} {admin.surname}\nтел: ☎+7{admin.phone_number}\nДоступ разрешен!✅",
                                 reply_markup=get_callback_buts(buts={
                                     "Запретить доступ": f"block_{admin.tg_id_admin}",
                                 }, sizes=(1,))
                                 )
        elif not admin.admin_access:
            await message.answer(f"{admin.name} {admin.surname}\nтел: ☎+7{admin.phone_number}\nДоступ запрещен!❌",
                                 reply_markup=get_callback_buts(buts={
                                     "Разрешить доступ": f"unblock_{admin.tg_id_admin}",
                                 }, sizes=(1,))
                                 )


# Отлавливает нажатие кнопки "Запретить доступ".
@admin_commands_router.callback_query(F.data.startswith("block_"))
async def block_admin (callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    tg_id_admin = callback.data.split("_")[-1]
    admin_data = await orm_get_admin(session, str(tg_id_admin))
    data = False
    await orm_update_admin_access(session, str(tg_id_admin), data)
    await callback.answer()
    await bot.send_message(tg_id_admin, f"Вам запретили доступ!",
                           reply_markup=kb_admin.del_kb)
    await callback.message.edit_text(f"{admin_data.name} {admin_data.surname}\n"
                                     f"тел: ☎+7{admin_data.phone_number}\nДоступ запрещен!❌",
                                     reply_markup=kb_admin.start_kb_main_admin.as_markup(resize_keyboard=True))


# Отлавливает нажатие кнопки "Разрешить доступ".
@admin_commands_router.callback_query(F.data.startswith("unblock_"))
async def unblock_admin (callback: types.CallbackQuery, session: AsyncSession, bot: Bot):
    tg_id_admin = callback.data.split("_")[-1]
    admin_data = await orm_get_admin(session, str(tg_id_admin))
    data = True
    await orm_update_admin_access(session, str(tg_id_admin), data)
    await callback.answer()
    await bot.send_message(tg_id_admin, f"Вам разрешили доступ!",
                           reply_markup=kb_admin.start_kb_admin.as_markup(resize_keyboard=True))
    await callback.message.edit_text(f"{admin_data.name} {admin_data.surname}\n"
                                     f"тел: ☎+7{admin_data.phone_number}\nДоступ разрешен!✅",
                                     reply_markup=kb_admin.start_kb_main_admin.as_markup(resize_keyboard=True))


# Отлавливает нажатие кнопки "Изменить пароль". Входит в режим FSM, отправляет сообщение пользователю
# "Напишите новый пароль!". Становится в состояние "new_password"
@admin_commands_router.message(StateFilter(None), F.text == "Изменить пароль")
async def change_password(message: types.Message, state: FSMContext):
    await message.answer("Напишите новый пароль!",
                         reply_markup=kb_admin.kb_cancel_admin.as_markup(resize_keyboard=True))
    await state.set_state(ChangePassword.new_password)


# Отлавливает сообщение написанное в состоянии "new_password". Изменяет пароль на новый, выходит из режима FSM.
# Отправляет сообщение об успешной замене и клавиатуру главного админ-а.
@admin_commands_router.message(StateFilter(ChangePassword.new_password))
async def new_password(message: types.Message, state: FSMContext):
    new_pass = message.text
    ADMIN_PASSWORD[0] = str(new_pass)
    print(f"Новый вароль - {ADMIN_PASSWORD}")
    await message.answer(f"Пароль успешно изменен!",
                         reply_markup=kb_admin.start_kb_main_admin.as_markup(resize_keyboard=True))
    await state.clear()


# Отлавливает нажатие кнопки "Добавить смену🆕". Входит в режим FSM, отправляет сообщение пользователю
# "Напиши дату". Становится в состояние "date_time_working_shift"
@admin_commands_router.message(StateFilter(None), F.text == "Добавить смену🆕")
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
            await sending_update_shift_workers(session, bot, AddWorkingShift.shift_for_working_change)
            await orm_update_working_shift(session, AddWorkingShift.shift_for_working_change.id, data)
            if admin.admin_access:
                await message.answer("Смена изменена!✅",
                                     reply_markup=kb_admin.start_kb_admin.as_markup(resize_keyboard=True))
            else:
                await message.answer("Смена изменена!✅",
                                     reply_markup=kb_admin.start_kb_main_admin.as_markup(resize_keyboard=True))
        else:
            await orm_add_working_shift(session, data)
            await sending_new_shift_workers(session, bot)
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

