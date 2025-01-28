import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select, func

from app.database import async_session
from app.models import User, Appointment, ScheduleWork
from app.dao.base import BaseDAO


class UserDAO(BaseDAO):
    model = User


class AppointmentDAO(BaseDAO):
    model = Appointment

    @classmethod
    async def get_all_on_date(cls, date: str | datetime.date, is_active=True):
        if isinstance(date, str):
            date = datetime.date.fromisoformat(date)

        async with async_session() as session:
            stmt = (
                select(Appointment)
                .where(func.date(Appointment.start_at) == date)
                .where(Appointment.is_active == is_active)
            )
            result = await session.scalars(stmt)
            return result.all()

    @classmethod
    async def get_overdue(cls):
        async with async_session() as session:
            stmt = (
                select(Appointment)
                .where(Appointment.start_at < datetime.datetime.now(ZoneInfo("Europe/Moscow")).replace(tzinfo=None))
                .where(Appointment.is_active == True)
            )
            result = await session.scalars(stmt)
            return result.all()

    @classmethod
    async def get_check_confirmation(cls):
        async with async_session() as session:
            dttm_now = datetime.datetime.now(ZoneInfo("Europe/Moscow")).replace(tzinfo=None)
            stmt = (
                select(Appointment)
                .where(func.extract('epoch', Appointment.start_at - dttm_now) / 3600 <= 2.5)
                .where(Appointment.is_active == True)
                .where(Appointment.is_confirmation == False)
            )
            result = await session.scalars(stmt)
            return result.all()


class ScheduleWorkDAO(BaseDAO):
    model = ScheduleWork
