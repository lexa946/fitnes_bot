import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.bot import bot
from app.dao.main import AppointmentDAO


async def check_active_appointments():
    overdue_appointments = await AppointmentDAO.get_overdue()
    await AppointmentDAO.many_patch(overdue_appointments, is_active=False)
    log_message = "Overdue appointments ["
    for appointment in overdue_appointments:
        log_message += f"{appointment.start_at} {appointment.user_id};"
    log_message += "] now don't active"
    logging.info(log_message)


async def check_confirmation():
    check_confirmation_appointments = await AppointmentDAO.get_check_confirmation()
    for appointment in check_confirmation_appointments:
        await bot.send_message(
            appointment.user_id,
            text=f"Тренер не подтвердил тренировку - {appointment.start_at_str} - запись отменяется ❌"
        )
        await AppointmentDAO.patch(appointment, is_active=False)


scheduler = AsyncIOScheduler()
scheduler.add_job(check_active_appointments, CronTrigger.from_crontab("0 8-22 * * *"))
scheduler.add_job(check_confirmation, CronTrigger.from_crontab("0 8-22 * * *"))
