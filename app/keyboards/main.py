import datetime
from functools import wraps
from zoneinfo import ZoneInfo

from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.models import User, Appointment
from app.config import settings


def create_inline_keyboard(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        kb = InlineKeyboardBuilder()
        func(kb, *args, **kwargs)
        kb.adjust(1)
        return kb.as_markup()

    return wrapper


@create_inline_keyboard
def gender_keyboard(kb: InlineKeyboardBuilder):
    kb.button(text="♂️ Мужской", callback_data="male")
    kb.button(text="♀️ Женский", callback_data="female")


@create_inline_keyboard
def registration_apply_keyboard(kb: InlineKeyboardBuilder):
    kb.button(text="✅ Подтвердить", callback_data="registration_apply")
    kb.button(text="♻ Изменить", callback_data="register_edit")


@create_inline_keyboard
def main_menu_client_keyboard(kb: InlineKeyboardBuilder, is_admin: bool, is_trainer: bool):
    if is_admin:
        kb.button(text="👩🏻‍💻 Администрирование", callback_data="admins_menu")

    kb.button(text="📒 Мои записи", callback_data="my_appointments")

    if is_trainer:
        kb.button(text="✉️ Отправить рассылку", callback_data="send_newsletter")
    else:
        kb.button(text="📝 Запись к тренеру", callback_data="trainer_appointment")

    kb.button(text="⚙ Настройки", callback_data="settings")


@create_inline_keyboard
def back_to_main_menu(kb: InlineKeyboardBuilder):
    kb.button(text="⏪ Назад", callback_data="main_menu")


@create_inline_keyboard
def settings_keyboard(kb: InlineKeyboardBuilder, is_trainer: bool):
    kb.button(text="♻ Изменить ФИО", callback_data="change_FIO")
    if is_trainer:
        kb.button(text="📅 Изменить расписание", callback_data="change_schedule")
        kb.button(text="💼 Список клиентов", callback_data="client_list")
    else:
        kb.button(text="🏋️‍♂️ Сменить тренера", callback_data="change_trainer")
    kb.button(text="⏪ Назад", callback_data="main_menu")


@create_inline_keyboard
def change_schedule_keyboard(kb: InlineKeyboardBuilder):
    kb.button(text="🕑 Рабочие часы", callback_data="change_work_hours")
    kb.button(text="🏃‍♂️ Кол-во человек в час", callback_data="change_max_user_per_hour")
    kb.button(text="🔄 Автоподтверждение", callback_data="change_auto_confirmation")
    kb.button(text="🆓️ Выходные", callback_data="change_free_days")
    kb.button(text="⏪ Назад", callback_data="settings")


@create_inline_keyboard
def change_max_user_per_hour_keyboard(kb: InlineKeyboardBuilder):
    for i in range(1, 6):
        kb.button(text=str(i), callback_data=f"change_max_user_per_hour:{i}")
    kb.button(text="❌ Отмена", callback_data="settings")


@create_inline_keyboard
def change_FIO_confirmation_keyboard(kb: InlineKeyboardBuilder):
    kb.button(text="✅ Подтвердить", callback_data="change_FIO_confirmation")
    kb.button(text="♻ Изменить", callback_data="change_FIO")
    kb.button(text="❌ Отмена", callback_data="settings")


@create_inline_keyboard
def choice_trainer_keyboard(kb: InlineKeyboardBuilder, trainers: list[User]):
    for trainer in trainers:
        kb.button(text=trainer.username, callback_data=f"trainer_choice_id:{trainer.user_id}")
    kb.button(text="⏪ Назад", callback_data="settings")


@create_inline_keyboard
def choice_appointment_date_keyboard(kb: InlineKeyboardBuilder, free_days: list[int]):
    date_now = datetime.datetime.now(ZoneInfo("Europe/Moscow")).date()
    for i in range(7):
        day = date_now + datetime.timedelta(days=i)
        if day.weekday()+1 in free_days: continue
        kb.button(text=f"{settings.WEEKDAY_TO_STR[day.weekday()+1]} {day.strftime("%d.%m.%Y")}", callback_data=f"appointment_date:{day.isoformat()}")
    kb.button(text="❌ Отмена", callback_data=f"main_menu")


@create_inline_keyboard
def choice_appointment_time_keyboard(kb: InlineKeyboardBuilder, hours: list[int]):
    for hour in hours:
        kb.button(text=f"🕑 {hour}:00", callback_data=f"appointment_time:{hour}")
    kb.button(text="❌ Отмена", callback_data=f"main_menu")


@create_inline_keyboard
def appointment_confirmation_keyboard(kb: InlineKeyboardBuilder):
    kb.button(text="✅ Подтвердить", callback_data="appointment_confirmation")
    kb.button(text="💬 Добавить комментарий", callback_data="appointment_confirmation_add_comment")
    kb.button(text="❌ Отменить", callback_data="main_menu")


@create_inline_keyboard
def my_appointments_keyboard(kb: InlineKeyboardBuilder):
    kb.button(text="🗑 Отменить запись", callback_data="choice_remove_appointment")
    kb.button(text="⏪ Назад", callback_data="main_menu")


@create_inline_keyboard
def choice_remove_appointments_keyboard(kb: InlineKeyboardBuilder, appointments: list[tuple[Appointment, User]]):
    for appointment, trainer in appointments:
        text = f"{appointment.start_at_str} {trainer.username}\n"
        kb.button(text=text, callback_data=f"remove_appointment:{appointment.id}")
    kb.button(text="⏪ Назад", callback_data="main_menu")


@create_inline_keyboard
def client_list_keyboard(kb: InlineKeyboardBuilder):
    kb.button(text="🗑 Удалить клиента", callback_data="remove_client")
    kb.button(text="⏪ Назад", callback_data="main_menu")


@create_inline_keyboard
def choice_remove_client_keyboard(kb: InlineKeyboardBuilder, clients: list[User]):
    for client in clients:
        kb.button(text=client.username, callback_data=f"remove_client:{client.user_id}")
    kb.button(text="⏪ Назад", callback_data="main_menu")


@create_inline_keyboard
def delete_client_confirmation_keyboard(kb: InlineKeyboardBuilder, client: User):
    kb.button(text="✅ Подтвердить", callback_data=f"apply_remove_client:{client.user_id}")
    kb.button(text="❌ Отменить", callback_data="main_menu")


@create_inline_keyboard
def trainer_confirmation_appointment_keyboard(kb: InlineKeyboardBuilder, appointment_id: int):
    kb.button(text="✅ Подтвердить", callback_data=f"trainer_confirm_appointment:{appointment_id}")
    kb.button(text="❌ Отменить", callback_data=f"trainer_not_confirm_appointment:{appointment_id}")
