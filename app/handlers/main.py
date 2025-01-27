import logging

from aiogram.filters import CommandStart, Command
from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram import F

from app.dao.main import UserDAO, AppointmentDAO, ScheduleWorkDAO
from app.utils import get_user
from app.keyboards.main import gender_keyboard, registration_apply_keyboard, main_menu_client_keyboard, \
    settings_keyboard, change_FIO_confirmation_keyboard, choice_trainer_keyboard, my_appointments_keyboard, \
    back_to_main_menu, choice_remove_appointments_keyboard
from app.forms import RegistrationForm, ChangeFIOForm
from app.models import User, Appointment
from app.config import settings

router = Router()

@router.message(Command("help"))
async def help(message: Message):
    await message.answer("Если вы столкнулись с трудностями при работе с ботом, "
                         "тогда попробуйте вызвать /menu и повторить свои действия. "
                         "Если трудности повторяются тогда необходимо обратиться к @PozharAlex "
                         "и описать цикл ваших действий приводимых к ошибкам работы. "
                         "Это необходимо для дальнейшего устранения и улучшения работы бота.")

async def choice_trainer(callback: CallbackQuery):
    trainers = await UserDAO.find_all(is_trainer=True)
    await callback.message.edit_text("Выберите тренера", reply_markup=choice_trainer_keyboard(trainers))


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    client = await UserDAO.find_one_or_none(user_id=message.from_user.id)
    if client:
        await message.reply("Рад видеть вас снова!")
    else:
        await state.set_state(RegistrationForm.FIO)
        await message.reply(f"Привет 👋😊\n"
                            f"Ты у нас новенький, давай познакомимся.\n"
                            f"Напишите свое ФИО:")


@router.callback_query(F.data == "register_edit")
async def register_edit(callback: CallbackQuery, state: FSMContext):
    await state.set_state(RegistrationForm.FIO)
    await callback.message.edit_text(f"Напишите свое ФИО:")


@router.message(RegistrationForm.FIO)
async def register_FIO(message: Message, state: FSMContext):
    await state.update_data(FIO=message.text)
    await state.set_state(RegistrationForm.gender)
    await message.reply("Выберите пол:", reply_markup=gender_keyboard())


@router.callback_query(F.data.in_(["male", "female"]))
async def register_gender(callback: CallbackQuery, state: FSMContext):
    form = await state.update_data(gender=callback.data)
    await callback.message.edit_text(f"Ваша форма:\nФИО: {form['FIO']}\n"
                                     f"Пол: {'Мужской' if form['gender'] == 'male' else 'Женский'}\nВсе верно?",
                                     reply_markup=registration_apply_keyboard())


@router.callback_query(F.data == "registration_apply")
async def register_apply(callback: CallbackQuery, state: FSMContext):
    form = await state.get_data()
    await UserDAO.add(
        user_id=callback.from_user.id,
        username=form['FIO'],
        gender=form['gender'],
    )
    await choice_trainer(callback)


@router.callback_query(F.data == "main_menu")
@router.message(Command("menu"))
@get_user
async def main_menu(callback: CallbackQuery | Message, user: User, state: FSMContext):
    await state.clear()

    menu = main_menu_client_keyboard(is_admin=user.is_admin, is_trainer=user.is_trainer)
    if isinstance(callback, CallbackQuery):
        await callback.message.edit_text("Главное меню!", reply_markup=menu)
    else:
        await callback.answer("Главное меню!", reply_markup=menu)


@router.callback_query(F.data == "settings")
@get_user
async def settings_handler(callback: CallbackQuery, user: User):
    message_text = (f"🪪 Профиль\n\t"
                    f"{'🧑' if user.gender.value == 'Мужской' else '👩'} ФИО: {user.username}\n\t")
    if user.is_trainer:
        schedule_work = await ScheduleWorkDAO.find_one_or_none(trainer_id=user.user_id)
        if not schedule_work:
            schedule_work = await ScheduleWorkDAO.add(trainer_id=user.user_id)

        if schedule_work.hours != [0] :
            work_hours_str = schedule_work.hours
        else:
            work_hours_str = "любые"

        if schedule_work.free_days != [0]:
            free_days_str = ", ".join(settings.WEEKDAY_TO_STR[day_num] for day_num in schedule_work.free_days)
        else:
            free_days_str = "нет"

        if schedule_work.max_user_per_hour != 0:
            user_per_hour = schedule_work.max_user_per_hour
        else:
            user_per_hour = "любое"

        message_text += (f"🕑 Часы работы: {work_hours_str}\n\t"
                         f"🏃‍♂️ Кол-во клиентов в час: {user_per_hour}\n\t"
                         f"🔄 Автоподтверждение: {'Вкл' if schedule_work.auto_confirmation else 'Выкл'}\n\t"
                         f"🆓️ Выходные: {free_days_str}\n\t")
    else:
        trainer = await UserDAO.find_one_or_none(user_id=user.trainer_id)
        if trainer:
            message_text += f"🏋️‍♂️ Тренер: {trainer.username}\n\t"
        else:
            message_text += f"🏋️‍♂️ Тренер: не выбран\n\t"

    await callback.message.edit_text(message_text, reply_markup=settings_keyboard(user.is_trainer))


@router.callback_query(F.data == "change_FIO")
async def change_FIO(callback: CallbackQuery, state: FSMContext):
    await state.set_state(ChangeFIOForm.FIO)
    await callback.message.edit_text("Напишите новое ФИО:", reply_markup=back_to_main_menu())


@router.message(ChangeFIOForm.FIO)
async def confirm_change_FIO(message: Message, state: FSMContext):
    await state.update_data(FIO=message.text)
    await message.answer(f"Ваше новое ФИО: {message.text}", reply_markup=change_FIO_confirmation_keyboard())


@router.callback_query(F.data == "change_FIO_confirmation")
@get_user
async def apply_change_FIO(callback: CallbackQuery, user: User, state: FSMContext):
    form = await state.get_data()
    await callback.message.edit_text(f"Установлено новое ФИО: {form['FIO']}",
                                     reply_markup=main_menu_client_keyboard(is_admin=user.is_admin,
                                                                            is_trainer=user.is_trainer))
    await UserDAO.patch(user, username=form['FIO'])
    await state.clear()


@router.callback_query(F.data == "my_appointments")
@get_user
async def my_appointments(callback: CallbackQuery, user: User):
    appointments_filter = {
        "trainer_id" if user.is_trainer else "user_id": user.user_id,
        "is_active": True
    }
    appointments: list[Appointment] = await AppointmentDAO.find_all(**appointments_filter)
    appointments.sort(key=lambda ap: ap.start_at)

    if appointments:
        message_text = "Ваши записи:\n"
        for i, appointment in enumerate(appointments):
            trainer: User = await UserDAO.find_one_or_none(user_id=appointment.trainer_id)

            if user.is_trainer:
                client = await UserDAO.find_one_or_none(user_id=appointment.user_id)
                username = client.username
            else:
                username = trainer.username

            message_text += (f"{i + 1}. {appointment.start_at_str} {username} "
                             f"{'Подтверждено ✅' if appointment.is_confirmation else 'Ожидание ⏳'}\n")
        await callback.message.edit_text(message_text, reply_markup=my_appointments_keyboard())
    else:
        message_text = "У вас нету записей."
        await callback.message.edit_text(message_text, reply_markup=back_to_main_menu())


@router.callback_query(F.data == "choice_remove_appointment")
@get_user
async def choice_remove_appointment(callback: CallbackQuery, user: User):
    appointments_filter = {
        "trainer_id" if user.is_trainer else "user_id": user.user_id,
        "is_active": True
    }
    appointments: list[Appointment] = await AppointmentDAO.find_all(**appointments_filter)
    appointments.sort(key=lambda ap: ap.start_at)

    if not appointments:
        await callback.message.answer("У вас нету активных записей!")
    else:
        await callback.message.edit_text("Выберите запись для удаления:",
                                         reply_markup=choice_remove_appointments_keyboard(
                                             [
                                                 (appointment,
                                                  await UserDAO.find_one_or_none(user_id=appointment.trainer_id),
                                                  ) for appointment in appointments]
                                         ))


@router.callback_query(F.data.startswith("remove_appointment"))
@get_user
async def remove_appointment(callback: CallbackQuery, user: User):
    appointment_id = int(callback.data.split(":")[1])
    appointment = await AppointmentDAO.find_one_or_none(id=appointment_id)

    menu = back_to_main_menu()

    if appointment:
        trainer: User = await UserDAO.find_one_or_none(user_id=appointment.trainer_id)

        if appointment.is_active:
            await AppointmentDAO.patch(appointment, is_active=False)
            await callback.message.edit_text(f"Запись - {appointment.start_at_str} {trainer.username} - успешно отменена",
                                             reply_markup=menu)
            if user.is_trainer:
                notification_chat_id = appointment.user_id
                notification_text = f"Тренер {trainer.username} отменил запись - {appointment.start_at_str} "
            else:
                notification_chat_id = appointment.trainer_id
                notification_text = f"Клиент {user.username} отменил запись - {appointment.start_at_str}"
            await callback.bot.send_message(notification_chat_id, notification_text)
        else:
            await callback.message.edit_text(f"Запись - {appointment.start_at_str} {trainer.username} - уже была отменена",
                                             reply_markup=menu)
    else:
        await callback.message.edit_text(f"Не удалось найти данную запсь в базе данных. Попробуйте повторить позже.",
                                         reply_markup=menu)
