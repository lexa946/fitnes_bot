import datetime

from aiogram import Router
from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.dao.main import UserDAO, AppointmentDAO, ScheduleWorkDAO
from app.forms import RegisterAppointment
from app.handlers.main import choice_trainer
from app.keyboards.main import choice_appointment_date_keyboard, \
    choice_appointment_time_keyboard, appointment_confirmation_keyboard, main_menu_client_keyboard, back_to_main_menu, \
    trainer_confirmation_appointment_keyboard
from app.models import User, Appointment
from app.utils import get_user, get_free_hours

router = Router()


@router.callback_query(F.data.startswith("trainer_choice_id:"))
@get_user
async def set_trainer_to_user(callback: CallbackQuery, user: User):
    trainer_id = int(callback.data.split(":")[1])
    await UserDAO.patch(user, trainer_id=trainer_id)
    trainer = await UserDAO.find_one_or_none(user_id=trainer_id)
    await callback.message.edit_text(
        f"Ваш новый тренер - {trainer.username}",
        reply_markup=main_menu_client_keyboard(is_admin=user.is_admin, is_trainer=user.is_trainer)
    )
    await callback.bot.send_message(trainer.user_id,
                                    f"У вас новый клиент: {user.username}")


@router.callback_query(F.data == "trainer_appointment")
@get_user
async def register_appointment_start(callback: CallbackQuery, user: User):
    trainer_id = user.trainer_id
    if not trainer_id:
        await choice_trainer(callback)
        return



    appointments: list[Appointment] = await AppointmentDAO.find_all(user_id=user.user_id, is_active=True)
    if len(appointments) >= settings.MAX_USER_APPOINTMENTS:
        await callback.message.edit_text(f"У вас уже максимум ({settings.MAX_USER_APPOINTMENTS}) записей.",
                                         reply_markup=back_to_main_menu())
    else:
        trainer_schedule = await ScheduleWorkDAO.find_one_or_none(trainer_id=trainer_id)
        if trainer_schedule:
            trainer_free_days = trainer_schedule.free_days
        else:
            trainer_free_days = [0]
        await callback.message.edit_text("Выберите дату записи:",
                                         reply_markup=choice_appointment_date_keyboard(trainer_free_days))


@router.callback_query(F.data.startswith("appointment_date"))
@get_user
async def register_appointment_date(callback: CallbackQuery, user: User, state: FSMContext):
    appointment_date = callback.data.split(":")[1]
    await state.update_data(date=appointment_date)
    schedule = await ScheduleWorkDAO.find_one_or_none(trainer_id=user.trainer_id)
    if schedule:
        work_hours = schedule.hours
        max_user_per_hour = schedule.max_user_per_hour
    else:
        work_hours = [0]
        max_user_per_hour = 3
    appointments_on_date = await AppointmentDAO.get_all_on_date(appointment_date)
    free_hours = get_free_hours(appointment_date, work_hours, max_user_per_hour, appointments_on_date)
    keyboard = choice_appointment_time_keyboard(free_hours)
    await callback.message.edit_text("Выберите время:",
                                     reply_markup=keyboard)


@router.callback_query(F.data.startswith("appointment_time"))
@get_user
async def register_appointment_confirmation(callback: CallbackQuery, user: User, state: FSMContext):
    appointment_time = callback.data.split(":")[1]

    trainer = await UserDAO.find_one_or_none(user_id=user.trainer_id)

    await state.update_data(time=appointment_time)
    await state.update_data(user_id=user.user_id)
    await state.update_data(trainer_id=user.trainer_id)
    await state.update_data(trainer_username=trainer.username)

    form = await state.get_data()

    appointment = await AppointmentDAO.find_one_or_none(
        start_at=datetime.datetime.fromisoformat(form['date']).replace(hour=int(form['time'])),
        user_id=form['user_id'],
        trainer_id=form['trainer_id'],
        is_active=True,
    )

    if appointment:
        await callback.message.edit_text(f"Вы уже записаны на это время!", reply_markup=back_to_main_menu())
        return


    message_text = f"""
    Регистрация на занятие
    Тренер: {form['trainer_username']}
    Дата и время: {form['date']} {form['time']}:00
    """

    await callback.message.edit_text(message_text, reply_markup=appointment_confirmation_keyboard())

@router.callback_query(F.data == "appointment_confirmation_add_comment")
async def appointment_confirmation_add_comment(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RegisterAppointment.comment)
    await callback.message.edit_text("Пришлите комментарий:")


@router.message(RegisterAppointment.comment)
async def appointment_confirmation_set_comment(message: Message, state: FSMContext):
    await state.update_data(comment=message.text)
    form = await state.get_data()

    message_text = f"""
    Регистрация на занятие
🏋️‍♂️ Тренер: {form['trainer_username']}
🕑 Дата и время: {form['date']} {form['time']}:00
💬 Комментарий: {form['comment']}
    """

    await message.answer(message_text, reply_markup=appointment_confirmation_keyboard())


@router.callback_query(F.data == "appointment_confirmation")
@get_user
async def register_appointment_add(callback: CallbackQuery, user: User, state: FSMContext):
    form = await state.get_data()
    appointment = await AppointmentDAO.add(
        start_at=datetime.datetime.fromisoformat(form['date']).replace(hour=int(form['time'])),
        user_id=form['user_id'],
        trainer_id=form['trainer_id'],
        comment=form.get("comment", None)
    )
    trainer = await UserDAO.find_one_or_none(user_id=user.trainer_id)

    message_text = f"""
    Регистрация на занятие успешно проведена.
🏋️‍♂️ Тренер: {trainer.username}
🕑 Дата и время: {form['date']} {form['time']}:00
{'💬 Комментарий: ' + form['comment'] if form.get('comment', None) else ''}
    """

    await callback.message.edit_text(message_text,
                                     reply_markup=main_menu_client_keyboard(user.is_admin, user.is_trainer))

    message_text_for_trainer = (f"К вам новая запись на тренировку:\n"
                                f"\t🧍 Клиент: {user.username}\n"
                                f"\t🕑 Дата и время: {appointment.start_at_str}\n"
                                f"{'💬 Комментарий: ' + form['comment'] if form.get('comment', None) else ''}")
    trainer_schedule_work = await ScheduleWorkDAO.find_one_or_none(trainer_id=trainer.user_id)
    if not trainer_schedule_work or not trainer_schedule_work.auto_confirmation:
        await callback.bot.send_message(trainer.user_id, message_text_for_trainer,
                                        reply_markup=trainer_confirmation_appointment_keyboard(appointment.id))
    else:
        await callback.bot.send_message(trainer.user_id, message_text_for_trainer)
        await AppointmentDAO.patch(appointment, is_confirmation=True)
        await callback.bot.send_message(user.user_id, f"✅ Тренер подтвердил тренировку {appointment.start_at_str}")
    await state.clear()


@router.callback_query(F.data == "change_trainer")
async def change_trainer(callback: CallbackQuery):
    await choice_trainer(callback)
