from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

del_kb = ReplyKeyboardRemove()


kb_start_worker = ReplyKeyboardBuilder()
kb_start_worker.add(
    KeyboardButton(text="❗Посмотреть смены❗"),
    KeyboardButton(text="♻Посмотреть мои данные♻"),
    KeyboardButton(text="☎Связаться с менеджером☎"),
)
kb_start_worker.adjust(1, 1, 1)


kb_cancel_worker = ReplyKeyboardBuilder()
kb_cancel_worker.add(
    KeyboardButton(text="Отмена"),
)
kb_cancel_worker.adjust(1, )

kb_cancel_back_worker = ReplyKeyboardBuilder()
kb_cancel_back_worker.attach(kb_cancel_worker)
kb_cancel_back_worker.row(KeyboardButton(text="Назад"),)


kb_cancel_back_skip_worker = ReplyKeyboardBuilder()
kb_cancel_back_skip_worker.attach(kb_cancel_back_worker)
kb_cancel_back_skip_worker.row(KeyboardButton(text="Пропустить_"),)


kb_contact_manager_view_worker = ReplyKeyboardBuilder()
kb_contact_manager_view_worker.add(
    KeyboardButton(text="☎Связаться с менеджером☎"),
    KeyboardButton(text="♻Посмотреть мои данные♻"),
    )
kb_contact_manager_view_worker.adjust(1, 1)


kb_contact_manager = ReplyKeyboardBuilder()
kb_contact_manager.add(
    KeyboardButton(text="☎Связаться с менеджером☎"),)
kb_contact_manager.adjust(1, )


kb_start = ReplyKeyboardBuilder()
kb_start.add(
    KeyboardButton(text="/start"),
)
kb_start.adjust(1, )
