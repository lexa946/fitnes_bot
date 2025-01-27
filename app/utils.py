import datetime
from collections import Counter
from functools import wraps
from zoneinfo import ZoneInfo

from aiogram.types import CallbackQuery, Message

from app.dao.main import UserDAO
from app.models import Appointment




def get_user(func):
    @wraps(func)
    async def wrapper(data: CallbackQuery | Message, *args, **kwargs):
        user = await UserDAO.find_one_or_none(user_id=data.from_user.id)
        if not user:
            await data.answer("Кажется мы с вами еще не знакомы. Отправьте мне комманду /start\n")
            raise NameError(f"Пользователь (id={data.from_user.id}) не зарегистрирован.")

        return await func(data, *args, user, **kwargs)

    return wrapper


def schedule_pars(hours_str: str) -> list[int]:
    if hours_str == "0":
        return [0]

    hours = []

    gaps = hours_str.split(",")
    for gap in gaps:
        start_end = gap.split("-")
        start = int(start_end[0])
        end = int(start_end[1])
        if start > 22 or end > 22:
            raise ValueError("WorkTime > 22,  it's wrong! ")
        elif start > end:
            raise ValueError("Start time > end time,  it's wrong! ")

        for i in range(start, end+1):
            hours.append(i)
    hours = sorted(list(set(hours)))
    return hours


def get_free_hours(appointment_date: str | datetime.date,
                   trainer_work_hours: list[int],
                   max_client_per_hour: int,
                   all_appointment_on_date: list[Appointment],
                   ):
    if isinstance(appointment_date, str):
        appointment_date = datetime.date.fromisoformat(appointment_date)

    dt_now = datetime.datetime.now(ZoneInfo("Europe/Moscow"))
    if appointment_date == dt_now.date():
        start_time = dt_now.hour + 2
    else:
        start_time = 8

    if trainer_work_hours and trainer_work_hours != [0]:
        hours = list(filter(lambda i: i >= start_time, trainer_work_hours))
    else:
        hours = list(range(start_time, 22))

    all_appointments__hours = [appointment.start_at.hour for appointment in all_appointment_on_date]
    counter_busy_hours = Counter(all_appointments__hours)
    all_busy_hours = [key for key, value in counter_busy_hours.items() if value >= max_client_per_hour]

    free_hours = set(hours) - set(all_busy_hours)
    return free_hours
