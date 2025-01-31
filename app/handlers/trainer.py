from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.dao.main import AppointmentDAO, UserDAO, ScheduleWorkDAO
from app.forms import ChangeSchedule, ChangeFreeDays
from app.keyboards.main import back_to_main_menu, client_list_keyboard, choice_remove_client_keyboard, \
    delete_client_confirmation_keyboard, change_schedule_keyboard, change_max_user_per_hour_keyboard
from app.models import User
from app.utils import get_user, schedule_pars
from app.config import settings

router = Router()




@router.callback_query(F.data == "change_schedule")
async def change_schedule(callback: CallbackQuery):
    await callback.message.edit_text("Что будем менять? ", reply_markup=change_schedule_keyboard())


@router.callback_query(F.data == "change_max_user_per_hour")
async def change_max_user_per_hours(callback: CallbackQuery):
    await callback.message.edit_text("Выберите кол-во человек: ", reply_markup=change_max_user_per_hour_keyboard())


@router.callback_query(F.data.startswith("change_max_user_per_hour"))
@get_user
async def change_max_user_per_hour_apply(callback: CallbackQuery, user: User):
    max_user_per_hour = int(callback.data.split(":")[1])
    schedule = await ScheduleWorkDAO.find_one_or_none(trainer_id=user.user_id)
    if not schedule:
        schedule = await ScheduleWorkDAO.add(trainer_id=user.user_id)
    await ScheduleWorkDAO.patch(schedule, max_user_per_hour=max_user_per_hour)
    await callback.message.edit_text(f"Максимальное кол-во человек в час теперь {max_user_per_hour}",
                                     reply_markup=back_to_main_menu())


@router.callback_query(F.data.startswith("change_free_days"))
async def change_max_user_per_hour_apply(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChangeFreeDays.days)

    message_text = (f"Напишите числа дней недели через запятую.\n"
                    f"Например: 3,6,7 - это выходные среда, суббота, воскресенье.\n"
                    f"Дни недели:\t")
    for key, value in settings.WEEKDAY_TO_STR.items():
        message_text += f"{key} {value};\t"
    message_text += "\nОтправь 0 для работы без выходных."
    await callback.message.edit_text(message_text, reply_markup=back_to_main_menu())



@router.message(ChangeFreeDays.days)
@get_user
async def set_free_days(message: Message, user: User):
    try:
        free_days = []
        for day_number in message.text.split(","):
            day_number = int(day_number)
            if day_number > 7:
                raise ValueError("Больше 7")
            free_days.append(day_number)
    except ValueError:
        await message.answer(f"Не смог распознать дни. Повторите ввод:", reply_markup=back_to_main_menu())
        return

    free_days = list(set(free_days))
    free_days.sort()

    schedule = await ScheduleWorkDAO.find_one_or_none(trainer_id=user.user_id)
    await ScheduleWorkDAO.patch(schedule, free_days=free_days)
    message_text = f"Теперь выходные дни - это {', '.join([settings.WEEKDAY_TO_STR[day] for day in free_days])}"
    await message.answer(message_text, reply_markup=back_to_main_menu())



@router.callback_query(F.data == "change_work_hours")
async def change_schedule(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Пришли мне промежутки часов, в которые ты работаешь!\n"
                                     "Пример: 8-12,13-17,18-22\n"
                                     "Если хотите указать любое время - пришлите 0\n", reply_markup=back_to_main_menu())
    await state.set_state(ChangeSchedule.hours)


@router.message(ChangeSchedule.hours)
@get_user
async def set_schedule_work_hours(message: Message, user: User):
    try:
        hours = schedule_pars(message.text.strip())
    except (IndexError, ValueError):
        await message.reply("Не смог разобрать часы, либо указанные часы не корректны!\nПовторите ввод:",
                            reply_markup=back_to_main_menu())
        return

    schedule = await ScheduleWorkDAO.find_one_or_none(trainer_id=user.user_id)
    if not schedule:
        await ScheduleWorkDAO.add(
            trainer_id=user.user_id,
            hours=hours
        )
    else:
        await ScheduleWorkDAO.patch(schedule, hours=hours)

    await message.answer(f"Расписание работы успешно обновлено!", reply_markup=back_to_main_menu())



@router.callback_query(F.data == "change_auto_confirmation")
@get_user
async def change_auto_confirmation(callback: CallbackQuery, user: User):
    schedule = await ScheduleWorkDAO.find_one_or_none(trainer_id=user.user_id)
    if schedule.auto_confirmation:
        message_text = "Автоподтверждение отключено"
    else:
        message_text = "Автоподтверждение включено"
    await ScheduleWorkDAO.patch(schedule, auto_confirmation=not schedule.auto_confirmation)

    await callback.message.edit_text(message_text, reply_markup=back_to_main_menu())


@router.callback_query(F.data == "client_list")
@get_user
async def client_list(callback: CallbackQuery, user: User):
    clients = await UserDAO.find_all(trainer_id=user.user_id)
    if not clients:
        await callback.message.edit_text(f"У вас нету клиентов!", reply_markup=back_to_main_menu())
        return

    message_text = "Список ваших клиентов:\n"
    for i, client in enumerate(clients):
        message_text += f"\t{i + 1}. {client.username}\n"

    await callback.message.edit_text(message_text, reply_markup=client_list_keyboard())


@router.callback_query(F.data == "remove_client")
@get_user
async def choice_remove_client(callback: CallbackQuery, user: User):
    clients = await UserDAO.find_all(trainer_id=user.user_id)
    if not clients:
        await callback.message.edit_text(f"У вас нету клиентов!", reply_markup=back_to_main_menu())
        return
    await callback.message.edit_text("Выберите клиента для удаления:",
                                     reply_markup=choice_remove_client_keyboard(clients))


@router.callback_query(F.data.startswith("remove_client"))
async def remove_client_confirmation(callback: CallbackQuery):
    client_id = int(callback.data.split(":")[1])
    client = await UserDAO.find_one_or_none(user_id=client_id)
    if not client:
        await callback.message.edit_text("Такого пользователя нет в базе. Повторите попытку позже!",
                                         reply_markup=back_to_main_menu())
        return

    await callback.message.edit_text(f"Вы хотите удалить клиента:\n{client.username}",
                                     reply_markup=delete_client_confirmation_keyboard(client))


@router.callback_query(F.data.startswith("apply_remove_client"))
@get_user
async def remove_client_confirmation(callback: CallbackQuery, user: User):
    client_id = int(callback.data.split(":")[1])
    client = await UserDAO.find_one_or_none(user_id=client_id)
    await UserDAO.patch(client, trainer_id=None)
    client_appointments = await AppointmentDAO.find_all(user_id=client.user_id, trainer_id=user.user_id)
    await AppointmentDAO.many_patch(client_appointments, is_active=False)
    await callback.message.edit_text(f"Клиент {client.username} удален!\nВсе записи от этого клиента анулированы.",
                                     reply_markup=back_to_main_menu())
    await callback.bot.send_message(client.user_id, "Вам нужно выбрать нового тренера!")


@router.callback_query(F.data.startswith("trainer_confirm_appointment"))
@router.callback_query(F.data.startswith("trainer_not_confirm_appointment"))
async def trainer_confirm_appointment(callback: CallbackQuery):
    appointment_id = int(callback.data.split(":")[1])
    appointment = await AppointmentDAO.find_one_or_none(id=appointment_id)

    if not appointment.is_active:
        await callback.message.edit_text("Запись уже была отменена 🤷‍♂️")
        return

    if callback.data.startswith("trainer_confirm_appointment"):
        await AppointmentDAO.patch(appointment, is_confirmation=True)
        message_text = f"✅ Тренер подтвердил тренировку {appointment.start_at_str}"
    else:
        await AppointmentDAO.patch(appointment, is_active=False)
        message_text = f"❌ Тренер не подтвердил тренировку {appointment.start_at_str}"
    await callback.bot.send_message(appointment.user_id, message_text)
    await callback.message.delete()
