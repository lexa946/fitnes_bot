from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.dao.main import AppointmentDAO, UserDAO, ScheduleWorkDAO, TrainingProgramDAO
from app.forms import ChangeSchedule, ChangeFreeDays, Training, ClientComment
from app.keyboards.main import back_to_main_menu, client_list_keyboard, \
    delete_client_confirmation_keyboard, change_schedule_keyboard, change_max_user_per_hour_keyboard, \
    training_client_keyboard, end_set_training_keyboard, \
    client_profile_keyboard, back_to_profile_client_keyboard
from app.models import User
from app.utils import get_user, schedule_pars, get_client_profile
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


@router.callback_query(F.data == "clients_list")
@get_user
async def client_list(callback: CallbackQuery, user: User):
    clients = await UserDAO.find_all(trainer_id=user.user_id)
    if not clients:
        await callback.message.edit_text(f"У вас нету клиентов!", reply_markup=back_to_main_menu())
        return

    message_text = "Список ваших клиентов:\n"
    await callback.message.edit_text(message_text, reply_markup=client_list_keyboard(clients))


@router.callback_query(F.data.startswith("client_profile"))
async def client_profile(callback: CallbackQuery):
    client_id = int(callback.data.split(":")[1])
    client = await UserDAO.find_one_or_none(user_id=client_id)
    if not client:
        await callback.message.edit_text(f"Нет такого клиента!", reply_markup=back_to_main_menu())
        return
    profile_text = get_client_profile(client)
    await callback.message.edit_text(profile_text, reply_markup=client_profile_keyboard(client_id))


@router.callback_query(F.data.startswith("change_comment_client"))
async def client_add_comment(callback: CallbackQuery, state: FSMContext):
    client_id = int(callback.data.split(":")[1])
    await state.set_state(ClientComment.comment)
    await state.update_data(client_id=client_id)
    await callback.message.edit_text("Пришлите комментарий:")


@router.message(ClientComment.comment)
async def client_set_comment(message: Message, state: FSMContext):
    form = await state.get_data()
    client = await UserDAO.find_one_or_none(user_id=form['client_id'])
    client = await UserDAO.patch(client, comment=message.text)
    profile_text = get_client_profile(client)
    await message.answer("Комментарий добавлен!")
    await message.answer(profile_text, reply_markup=client_profile_keyboard(form['client_id']))
    await state.clear()



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


@router.callback_query(F.data.startswith("program_training_client"))
async def program_training_client(callback: CallbackQuery):
    client_id = int(callback.data.split(":")[1])

    program = await TrainingProgramDAO.find_one_or_none(user_id=client_id)

    if not program:
        program = await TrainingProgramDAO.add(user_id=client_id)
    if not program.individual:
        await callback.message.edit_text(f"Программа еще не написана",
                                         reply_markup=training_client_keyboard(client_id, []))
        return
    messages = []
    for text in program.individual:
        new_message = await callback.message.answer(text)
        messages.append(new_message)

    await messages[-1].edit_text(messages[-1].text, reply_markup=training_client_keyboard(
        client_id,
        [str(message.message_id) for message in messages]
    ))

@router.callback_query(F.data.startswith("close_program"))
async def close_program(callback: CallbackQuery):
    message_ids = callback.data.split(":")[1].split(",")
    message_ids = [int(message_id) for message_id in message_ids]
    await callback.bot.delete_messages(callback.from_user.id, message_ids)


@router.callback_query(F.data.startswith("set_training"))
async def set_training(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Training.program)

    client_messages_id = callback.data.split(":")[1]
    client_id, messages_id = client_messages_id.split(";")
    client_id = int(client_id)
    if messages_id:
        messages_id = [int(message_id) for message_id in messages_id.split(",")]
        await callback.bot.delete_messages(callback.from_user.id, messages_id)

    client = await UserDAO.find_one_or_none(user_id=client_id)


    # await callback.message.delete()

    await callback.message.answer(f"Напишите программу тренировок для {client.username}.\n\n"
                                     f"Правила оформления:\n"
                                     f"1. Вы можете отправить несколько сообщений. "
                                     f"Они будут приходить в такой же последовательности, как вы отправили.\n"
                                     f"2. Пустые строки будут расцениваться как разделения сообщений. "
                                     f"Если вы вставили пустую строку между абзацами, тогда вам придет несколько сообщений.\n"
                                     f"3. Последним сообщением необходиом отправить \"🏁 Конец\". "
                                     f"Сделать это можно с помощью клавиатуры.", reply_markup=end_set_training_keyboard())
    await state.update_data(client_id=client_id)
    await state.update_data(messages=[])

@router.message(Training.program)
async def set_training_message(message: Message, state: FSMContext):
    form = await state.get_data()

    if message.text != "🏁 Конец":

        messages_text = message.text.split("\n\n")
        for message_text in messages_text:
            form['messages'].append(message_text.strip())
        await state.update_data(messages=form['messages'])
        return

    program = await TrainingProgramDAO.find_one_or_none(user_id=form['client_id'])
    await TrainingProgramDAO.patch(program, individual=form['messages'])
    await message.answer("Программа обновлена!", reply_markup=back_to_profile_client_keyboard(form['client_id']))
    await state.clear()
