import os
from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())

from aiogram import F, types, Router
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_admin_table_queries import orm_get_admin, orm_add_admin, orm_update_admin

from keyboards import kb_admin, kb_worker

ADMIN_PASSWORD = ["54321",]

admin_login_router = Router()


class AddWorkingShift(StatesGroup):
    tg_id_admin = State()
    date_time_working_shift = State()
    address = State()
    description_working_shift = State()
    quantity_workers = State()
    cost_work = State()

    shift_for_working_change = None

    texts_working_shift = {
        "AddWorkingShift:date_time_working_shift": "Напиши дату заново!",
        "AddWorkingShift:address": "Напиши адрес заново!",
        "AddWorkingShift:description_working_shift": "Напиши описание заново!",
        "AddWorkingShift:quantity_workers": "Напиши кол-во работников заново!",
        "AddWorkingShift:cost_work": "Напиши стоимость работ заново!",
        }


class RegistrationAdmin(StatesGroup):
    tg_id_admin = State()
    name = State()
    surname = State()
    phone_number = State()
    admin_access = State()
    main_admin = State()

    admin_data_for_change = None

    texts_admin = {
        "RegistrationAdmin:surname": "Напиши Фамилию заново!",
        "RegistrationAdmin:name": "Напиши Имя заново!",
        "RegistrationAdmin:phone_number": "Напиши номер телефона заново!",
    }


@admin_login_router.message(StateFilter(None), Command("admin"))
async def admin_login(message: types.Message, state: FSMContext, session: AsyncSession):
    admin = await orm_get_admin(session, str(message.from_user.id))
    if admin is None:
        await message.answer("Введите пароль!",
                             reply_markup=kb_admin.kb_cancel_admin.as_markup(resize_keyboard=True))
        await state.set_state(RegistrationAdmin.tg_id_admin)
    elif admin.admin_access:
        await message.answer("Вы вошли в режим администратора!",
                             reply_markup=kb_admin.start_kb_admin.as_markup(resize_keyboard=True))
    elif admin.main_admin:
        await message.answer("Приветствую хозяин!",
                             reply_markup=kb_admin.start_kb_main_admin.as_markup(resize_keyboard=True))
    else:
        await message.answer("Извините. Вам ограничили право доступа!",
                             reply_markup=kb_worker.kb_start_worker.as_markup(resize_keyboard=True))


# Отменяет все действия и выходит из режима FSM
@admin_login_router.message(StateFilter("*"), Command("_Отменить_"))
@admin_login_router.message(StateFilter("*"), F.text == "_Отменить_")
async def cancel_handler_admin(message: types.Message, state: FSMContext, session: AsyncSession):
    current_state = await state.get_state()
    if current_state is None:
        return
    if RegistrationAdmin.admin_data_for_change:
        RegistrationAdmin.admin_data_for_change = None
    if AddWorkingShift.shift_for_working_change:
        AddWorkingShift.shift_for_working_change = None
    await state.clear()
    admin = await orm_get_admin(session, str(message.from_user.id))
    if admin is None:
        await message.answer("Отменил!", reply_markup=kb_worker.kb_start.as_markup(resize_keyboard=True))
    elif admin.admin_access:
        await message.answer("Отменил!", reply_markup=kb_admin.start_kb_admin.as_markup(resize_keyboard=True))
    elif admin.main_admin:
        await message.answer("Отменил!", reply_markup=kb_admin.start_kb_main_admin.as_markup(resize_keyboard=True))
    else:
        await message.answer("Что то пошло не так!!!",
                             reply_markup=kb_worker.del_kb.as_markup(resize_keyboard=True))


# Возвращает на шаг назад.
@admin_login_router.message(StateFilter("*"), Command("_Назад_"))
@admin_login_router.message(StateFilter("*"), F.text == "_Назад_")
async def return_handler_admin(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == AddWorkingShift.date_time_working_shift:
        await message.answer("Напиши дату или нажми Отменить")
        return

    previous = None
    for step in AddWorkingShift.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f"Вернул к предыдущему шагу. \n"
                                 f" {AddWorkingShift.texts_working_shift[previous.state]}")
            return
        previous = step

    if current_state == RegistrationAdmin.name:
        await message.answer("Напиши ваше имя или нажми Отменить")
        return

    previous = None
    for step in RegistrationAdmin.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f"Вернул к предыдущему шагу. \n"
                                 f" {RegistrationAdmin.texts_admin[previous.state]}")
            return
        previous = step


@admin_login_router.message(StateFilter(RegistrationAdmin.tg_id_admin))
async def admin_registration_tg_id(message: types.Message, state: FSMContext):
    tg_id_admin = message.from_user.id
    if os.getenv('MASTER_PASSWORD') == message.text:
        await state.update_data(tg_id_admin=str(tg_id_admin))
        await state.update_data(admin_access=False)
        await state.update_data(main_admin=True)
        await state.set_state(RegistrationAdmin.name)
        await message.answer("Приветствую хозяин! Пройдите регистрацию, напишите ваше Имя.",
                             reply_markup=kb_admin.kb_cancel_admin.as_markup(resize_keyboard=True))
    elif message.text in ADMIN_PASSWORD:
        await state.update_data(tg_id_admin=str(tg_id_admin))
        await state.update_data(admin_access=True)
        await state.update_data(main_admin=False)
        await state.set_state(RegistrationAdmin.name)
        await message.answer("Добро пожаловать в команду! Пройдите регистрацию, напишите ваше Имя.",
                             reply_markup=kb_admin.kb_cancel_admin.as_markup(resize_keyboard=True))
    else:
        await message.answer("Вы ввели не верный пароль! Попробуйте снова.",
                             reply_markup=kb_admin.kb_cancel_admin.as_markup(resize_keyboard=True))


@admin_login_router.message(StateFilter(RegistrationAdmin.name))
async def admin_registration_name(message: types.Message, state: FSMContext):
    print(message.text)
    try:
        if RegistrationAdmin.admin_data_for_change:
            await state.update_data(tg_id_admin=RegistrationAdmin.admin_data_for_change.tg_id_admin)
            await state.update_data(admin_access=RegistrationAdmin.admin_data_for_change.admin_access)
            await state.update_data(main_admin=RegistrationAdmin.admin_data_for_change.main_admin)
        if message.text == "_Пропустить_":
            await state.update_data(name=RegistrationAdmin.admin_data_for_change.name)
            await message.answer("Напиши свою Фамилию.",
                                 reply_markup=kb_admin.kb_cancel_back_skip_admin.as_markup(resize_keyboard=True))
        else:
            await state.update_data(name=str(message.text))
            if RegistrationAdmin.admin_data_for_change is None:
                await message.answer("Напиши свою Фамилию.",
                                     reply_markup=kb_admin.kb_cancel_back_admin.as_markup(resize_keyboard=True))
            else:
                await message.answer("Напиши свою Фамилию.",
                                     reply_markup=kb_admin.kb_cancel_back_skip_admin.as_markup(resize_keyboard=True))
        await state.set_state(RegistrationAdmin.surname)
    except Exception as error:
        print(error)
        await message.answer(f"Ошибка:{str(error)}\nВы ввели недопустимые значения!\n"
                             f"Напишите ваше Имя!",
                             reply_markup=kb_worker.kb_cancel_back_worker.as_markup(resize_keyboard=True))


@admin_login_router.message(StateFilter(RegistrationAdmin.surname))
async def admin_registration_surname(message: types.Message, state: FSMContext):
    try:
        if message.text == "_Пропустить_":
            await state.update_data(surname=RegistrationAdmin.admin_data_for_change.surname)
            await message.answer("Напишите ваш Номер телефона в формате 89001112233.",
                                 reply_markup=kb_admin.kb_cancel_back_skip_admin.as_markup(resize_keyboard=True))
        else:
            await state.update_data(surname=message.text)
            if RegistrationAdmin.admin_data_for_change is None:
                await message.answer("Напишите ваш Номер телефона в формате 89001112233.",
                                     reply_markup=kb_admin.kb_cancel_back_admin.as_markup(resize_keyboard=True))
            else:
                await message.answer("Напишите ваш Номер телефона в формате 89001112233.",
                                     reply_markup=kb_admin.kb_cancel_back_skip_admin.as_markup(resize_keyboard=True))
        await state.set_state(RegistrationAdmin.phone_number)
    except Exception as error:
        print(error)
        await message.answer(f"Ошибка:{str(error)}\nВы ввели недопустимые значения!\n"
                             f"Напишите вашу фамилию!",
                             reply_markup=kb_worker.kb_cancel_back_worker.as_markup(resize_keyboard=True))


@admin_login_router.message(StateFilter(RegistrationAdmin.phone_number))
async def admin_registration_phone_number(message: types.Message, state: FSMContext, session: AsyncSession):
    try:
        if message.text == "_Пропустить_":
            await state.update_data(phone_number=RegistrationAdmin.admin_data_for_change.phone_number)
        else:
            int_phone_number = message.text
            if len(message.text) != 11:
                raise ValueError
            await state.update_data(phone_number=message.text[1:])
        admin_data = await state.get_data()
        print(f"admin_data - !!!{admin_data}!!!")
        if RegistrationAdmin.admin_data_for_change:
            await orm_update_admin(session, RegistrationAdmin.admin_data_for_change.id, admin_data)
            if admin_data["admin_access"]:
                await message.answer("Ваши данные изменены!",
                                     reply_markup=kb_admin.start_kb_admin.as_markup(resize_keyboard=True))
            else:
                await message.answer("Ваши данные изменены!",
                                     reply_markup=kb_admin.start_kb_main_admin.as_markup(resize_keyboard=True))
        else:
            await orm_add_admin(session, admin_data)
            if admin_data["admin_access"]:
                await message.answer("Регистрация прошла успешно. Добро пожаловать в команду!",
                                     reply_markup=kb_admin.start_kb_admin.as_markup(resize_keyboard=True))
            else:
                await message.answer("Регистрация прошла успешно. Добро пожаловать в команду!",
                                     reply_markup=kb_admin.start_kb_main_admin.as_markup(resize_keyboard=True))
        await state.clear()
        RegistrationAdmin.admin_data_for_change = None
    except Exception as error:
        print(error)
        await message.answer(f"Ошибка:{str(error)}\nВы ввели недопустимые значения!\n"
                             f"Напишите ваш Номер телефона в формате 89001112233!",
                             reply_markup=kb_admin.kb_cancel_admin.as_markup(resize_keyboard=True))
