from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.utils.keyboard import ReplyKeyboardBuilder

del_kb = ReplyKeyboardRemove()


start_kb_admin = ReplyKeyboardBuilder()
start_kb_admin.add(
    KeyboardButton(text="Добавить смену🆕"),
    KeyboardButton(text="Посмотреть смены🛠"),
    KeyboardButton(text="🔎Посмотреть мои данные"),
    KeyboardButton(text="Посмотреть работников‍👷‍♂️"),
    KeyboardButton(text="Выход"),
)
start_kb_admin.adjust(2, 2, 1)


start_kb_main_admin = ReplyKeyboardBuilder()
start_kb_main_admin.attach(start_kb_admin)
start_kb_main_admin.row(KeyboardButton(text="Посмотреть адин-в"),
                        KeyboardButton(text="Изменить пароль"),)


kb_cancel_admin = ReplyKeyboardBuilder()
kb_cancel_admin.add(
    KeyboardButton(text="_Отменить_"),
)
kb_cancel_admin.adjust(1,)


kb_cancel_back_admin = ReplyKeyboardBuilder()
kb_cancel_back_admin.attach(kb_cancel_admin)
kb_cancel_back_admin.row(KeyboardButton(text="_Назад_"),)


kb_cancel_back_skip_admin = ReplyKeyboardBuilder()
kb_cancel_back_skip_admin.attach(kb_cancel_back_admin)
kb_cancel_back_skip_admin.row(KeyboardButton(text="_Пропустить_"),)
