import os
from aiogram import F, types, Router, Bot
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import LabeledPrice, PreCheckoutQuery

from sqlalchemy.ext.asyncio import AsyncSession
import datetime

from database.orm_admin_table_queries import orm_get_all_tg_id_admin
from database.orm_worker_table_queries import orm_add_worker, orm_get_worker, orm_update_worker

from keyboards import kb_worker
from keyboards.inline_kb import get_callback_buts

worker_authorization_router = Router()


class RegistrationWorker(StatesGroup):
    tg_id_worker = State()
    name_worker = State()
    surname_worker = State()
    age_worker = State()
    work_experience = State()
    phone_number_worker = State()
    passport_photo_worker = State()
    access_worker = State()

    worker_data_for_change = None

    texts_registration_worker = {
        "RegistrationWorker:name_worker": "Напишите ваше имя заново.",
        "RegistrationWorker:surname_worker": "Напишите вашу фамилию заново.",
        "RegistrationWorker:age_worker": "Напишите ваш возраст заново.",
        "RegistrationWorker:work_experience": "Напишите ваш опыт заново.",
        "RegistrationWorker:phone_number_worker": "Напишите ваш номер телефона заново.",
        "RegistrationWorker:passport_photo_worker": "Загрузите фото паспорта заново.",
    }


@worker_authorization_router.message(StateFilter(None), Command("start"))
async def worker_login(message: types.Message, state: FSMContext, session: AsyncSession):
    worker = await orm_get_worker(session, str(message.from_user.id))
    if worker:
        if worker.access_worker:
            await message.answer(f"Привет {worker.name_worker}! Я бот Delov-to! Чем могу помочь?",
                                 reply_markup=kb_worker.kb_start_worker.as_markup(resize_keyboard=True)
                                 )
        else:
            await message.answer(f"Привет {worker.name_worker}! Я бот Delov-to!\n"
                                 f"Тебе закрыли доступ к сменам, свяжись с менеджером!",
                                 reply_markup=kb_worker.kb_contact_manager_view_worker.as_markup(resize_keyboard=True)
                                 )
    else:
        await message.answer("Привет👋! Я бот Delov-to!\n"
                             "Вы не авторизованы, пройдите регистрацию.\n\nНапиши свое Имя.",
                             reply_markup=kb_worker.kb_cancel_worker.as_markup(resize_keyboard=True)
                             )
        await state.set_state(RegistrationWorker.name_worker)


@worker_authorization_router.message(StateFilter("*"), Command("Отмена"))
@worker_authorization_router.message(StateFilter("*"), F.text == "Отмена")
async def cancel_handler_worker(message: types.Message, state: FSMContext, session: AsyncSession):
    current_state = await state.get_state()
    if current_state is None:
        return
    if RegistrationWorker.worker_data_for_change:
        RegistrationWorker.worker_data_for_change = None
    await state.clear()

    worker = await orm_get_worker(session, str(message.from_user.id))
    if worker:
        if worker.access_worker:
            await message.answer(f"Отменил!", reply_markup=kb_worker.kb_start_worker.as_markup(resize_keyboard=True))
        else:
            await message.answer(f"Отменил!",
                                 reply_markup=kb_worker.kb_contact_manager_view_worker.as_markup(resize_keyboard=True))
    else:
        await message.answer("Отменил!", reply_markup=kb_worker.kb_start.as_markup(resize_keyboard=True))



# Возвращает на шаг назад
@worker_authorization_router.message(StateFilter("*"), Command("Назад"))
@worker_authorization_router.message(StateFilter("*"), F.text == "Назад")
async def return_handler_worker(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state == RegistrationWorker.name_worker:
        await message.answer("Напишите ваше Имя или нажмите Отмена")
        return

    previous = None
    for step in RegistrationWorker.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(f"Вернул к предыдущему шагу.\n"
                                 f"{RegistrationWorker.texts_registration_worker[previous.state]}")
            return
        previous = step


# Отлавливает сообщение написанное в режиме "name_worker" и сохраняет. Отправляет сообщение "Напишите вашу фамилию".
# Становится в состояние "surname_worker"
@worker_authorization_router.message(StateFilter(RegistrationWorker.name_worker))
async def add_name_worker(message: types.Message, state: FSMContext):
    await state.update_data(tg_id_worker=str(message.from_user.id))
    try:
        if len(message.text) < 2:
            raise ValueError
        if message.text == "Пропустить":
            await state.update_data(name_worker=RegistrationWorker.worker_data_for_change.name_worker)
            await message.answer("Напиши свою Фамилию.",
                                 reply_markup=kb_worker.kb_cancel_back_skip_worker.as_markup(resize_keyboard=True))
        else:
            await state.update_data(name_worker=str(message.text))
            if RegistrationWorker.worker_data_for_change is None:
                await message.answer("Напиши свою Фамилию.",
                                 reply_markup=kb_worker.kb_cancel_back_worker.as_markup(resize_keyboard=True))
            else:
                await message.answer("Напиши свою Фамилию.",
                                     reply_markup=kb_worker.kb_cancel_back_skip_worker.as_markup(resize_keyboard=True))
        await state.set_state(RegistrationWorker.surname_worker)

    except Exception as error:
        print(error)
        await message.answer(f"Ошибка:{str(error)}\nВы ввели недопустимые значения! Напиши свое Имя!",
                             reply_markup=kb_worker.kb_cancel_back_worker.as_markup(resize_keyboard=True))


# Отлавливает сообщение написанное в режиме "surname_worker" и сохраняет. Отправляет сообщение "Напишите ваш возраст.".
# Становится в состояние "age_worker"
@worker_authorization_router.message(StateFilter(RegistrationWorker.surname_worker))
async def add_surname_worker(message: types.Message, state: FSMContext):
    try:
        if len(message.text) < 2:
            raise ValueError
        if message.text == "Пропустить":
            await state.update_data(surname_worker=RegistrationWorker.worker_data_for_change.surname_worker)
            await message.answer("Напишите ваш возраст.",
                                 reply_markup=kb_worker.kb_cancel_back_skip_worker.as_markup(resize_keyboard=True))
        else:
            await state.update_data(surname_worker=message.text)
            if RegistrationWorker.worker_data_for_change is None:
                await message.answer("Напишите ваш возраст.",
                                     reply_markup=kb_worker.kb_cancel_back_worker.as_markup(resize_keyboard=True))
            else:
                await message.answer("Напишите ваш возраст.",
                                     reply_markup=kb_worker.kb_cancel_back_skip_worker.as_markup(resize_keyboard=True))
        await state.set_state(RegistrationWorker.age_worker)

    except Exception as error:
        print(error)
        await message.answer(f"Ошибка:{str(error)}\nВы ввели недопустимые значения!\nНапишите вашу Фамилию!",
                             reply_markup=kb_worker.kb_cancel_back_worker.as_markup(resize_keyboard=True))


# Отлавливает сообщение написанное в режиме "age_worker" и сохраняет. Отправляет сообщение "Напишите ваш опыт работы.".
# Становится в состояние "work_experience"
@worker_authorization_router.message(StateFilter(RegistrationWorker.age_worker))
async def add_age_worker(message: types.Message, state: FSMContext):
    try:
        if 16 > int(message.text) or int(message.text) > 80:
            raise ValueError
        if message.text == "Пропустить":
            await state.update_data(age_worker=int(RegistrationWorker.worker_data_for_change.age_worker))
            await message.answer("Напишите ваш опыт работы.",
                                 reply_markup=kb_worker.kb_cancel_back_skip_worker.as_markup(resize_keyboard=True))
        else:
            await state.update_data(age_worker=int(message.text))
            if RegistrationWorker.worker_data_for_change is None:
                await message.answer("Напишите ваш опыт работы.",
                                     reply_markup=kb_worker.kb_cancel_back_worker.as_markup(resize_keyboard=True))
            else:
                await message.answer("Напишите ваш опыт работы.",
                                     reply_markup=kb_worker.kb_cancel_back_skip_worker.as_markup(resize_keyboard=True))
        await state.set_state(RegistrationWorker.work_experience)

    except Exception as error:
        print(error)
        await message.answer(f"Ошибка:{str(error)}\nВы ввели недопустимые значения!\nНапишите ваш возраст!",
                             reply_markup=kb_worker.kb_cancel_back_worker.as_markup(resize_keyboard=True))


# Отлавливает сообщение написанное в режиме "work_experience" и сохраняет.
# Отправляет сообщение "Напишите ваш номер телефона.". Становится в состояние "phone_number_worker"
@worker_authorization_router.message(StateFilter(RegistrationWorker.work_experience))
async def add_work_experience(message: types.Message, state: FSMContext):
    try:
        if len(message.text) < 2:
            raise ValueError
        if message.text == "Пропустить":
            await state.update_data(work_experience=str(RegistrationWorker.worker_data_for_change.work_experience))
            await message.answer("Напишите ваш номер телефона в формате 89001112233.",
                                 reply_markup=kb_worker.kb_cancel_back_skip_worker.as_markup(resize_keyboard=True))
        else:
            await state.update_data(work_experience=str(message.text))
            if RegistrationWorker.worker_data_for_change is None:
                await message.answer("Напишите ваш номер телефона в формате 89001112233.",
                                     reply_markup=kb_worker.kb_cancel_back_worker.as_markup(resize_keyboard=True))
            else:
                await message.answer("Напишите ваш номер телефона в формате 89001112233.",
                                     reply_markup=kb_worker.kb_cancel_back_skip_worker.as_markup(resize_keyboard=True))
        await state.set_state(RegistrationWorker.phone_number_worker)

    except Exception as error:
        print(error)
        await message.answer(f"Ошибка:{str(error)}\nВы ввели недопустимые значения!\nНапишите ваш опыт работы!",
                             reply_markup=kb_worker.kb_cancel_back_worker.as_markup(resize_keyboard=True))


# Отлавливает сообщение написанное в режиме "phone_number_worker" и сохраняет.
# Отправляет сообщение "Напишите ваш опыт работы.". Становится в состояние "phone_number_worker"
@worker_authorization_router.message(StateFilter(RegistrationWorker.phone_number_worker))
async def add_phone_number_worker(message: types.Message, state: FSMContext):
    try:
        if message.text == "Пропустить":
            await state.update_data(phone_number_worker=RegistrationWorker.worker_data_for_change.phone_number_worker)
            await message.answer("Пришлите фото паспорта.",
                                 reply_markup=kb_worker.kb_cancel_back_skip_worker.as_markup(resize_keyboard=True))
        else:
            int_phone_number = message.text
            if len(message.text) != 11:
                raise ValueError
            await state.update_data(phone_number_worker=message.text[1:])
            if RegistrationWorker.worker_data_for_change is None:
                await message.answer("Пришлите фото паспорта.",
                                     reply_markup=kb_worker.kb_cancel_back_worker.as_markup(resize_keyboard=True))
            else:
                await message.answer("Пришлите фото паспорта.",
                                     reply_markup=kb_worker.kb_cancel_back_skip_worker.as_markup(resize_keyboard=True))
        await state.set_state(RegistrationWorker.passport_photo_worker)

    except Exception as error:
        print(error)
        await message.answer(f"Ошибка:{str(error)}\nВы ввели недопустимые значения!\n"
                             f"Напишите ваш номер телефона в формате 89001112233!",
                             reply_markup=kb_worker.kb_cancel_back_worker.as_markup(resize_keyboard=True))


# Отлавливает сообщение написанное в режиме "passport_photo_worker" и сохраняет.
# Отправляет сообщение "Ваша анкета отправлена на рассмотрение, ожидайте."
# Сохраняет данные в БД, выходит из режима FSM. Формирует сообщение и отправляет менеджерам.
@worker_authorization_router.message(StateFilter(RegistrationWorker.passport_photo_worker), or_f(F.photo))
async def add_passport_photo_worker(message: types.Message, state: FSMContext, bot: Bot, session: AsyncSession):
    print(f"add_passport_photo_worker - {message.text}")
    try:
        if message.text == "Пропустить":
            await state.update_data(passport_photo_worker=RegistrationWorker.worker_data_for_change.passport_photo_worker)
            await state.update_data(access_worker=RegistrationWorker.worker_data_for_change.access_worker)
        else:
            await state.update_data(passport_photo_worker=message.photo[-1].file_id)
            await state.update_data(access_worker=False)
        worker_data = await state.get_data()
        print(worker_data)

        if RegistrationWorker.worker_data_for_change:
            await orm_update_worker(session, RegistrationWorker.worker_data_for_change.id, worker_data)
            await message.answer("Ваши данные изменены",
                                 reply_markup=kb_worker.kb_start.as_markup(resize_keyboard=True))
        else:
            await orm_add_worker(session, worker_data)
            await message.answer("Ваша анкета отправлена на рассмотрение, ожидайте.",
                                 reply_markup=kb_worker.kb_contact_manager_view_worker.as_markup(resize_keyboard=True))

            admin_list = await orm_get_all_tg_id_admin(session)
            if admin_list:
                for tg_id_admin in admin_list:
                    await bot.send_photo(int(tg_id_admin), worker_data["passport_photo_worker"],
                                         caption=f"Анкета для приема на работу:\n"
                                                 f"-Телегам id: {worker_data["tg_id_worker"]}\n"
                                                 f"-Имя: {worker_data["name_worker"]}\n"
                                                 f"-Фамилия: {worker_data["surname_worker"]}\n"
                                                 f"-Возраст: {worker_data["age_worker"]}\n"
                                                 f"-Опыт работы: {worker_data["work_experience"]}\n"
                                                 f"-Номер тел-а: +7{worker_data["phone_number_worker"]}",
                                         reply_markup=get_callback_buts(buts={"✅Принять":
                                                                                  f"acceptworker_{worker_data["tg_id_worker"]}",
                                                                              "❌Отклонить":
                                                                                  f"notacceptworker_{worker_data["tg_id_worker"]}"},
                                                                        sizes=(2, ))
                                         )
            else:
                print("Админов нет")
        await state.clear()
        RegistrationWorker.worker_data_for_change = None
    except Exception as error:
        print(error)
        await message.answer(f"Ошибка:{str(error)}\nВы ввели недопустимые значения!\nПришлите фото паспорта!",
                             reply_markup=kb_worker.kb_contact_manager_view_worker.as_markup(resize_keyboard=True))
