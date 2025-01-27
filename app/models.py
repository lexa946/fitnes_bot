import enum
from datetime import datetime

from sqlalchemy import ForeignKey, text, Enum, ARRAY, Column, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BASE
from app.config import settings


class User(BASE):
    __tablename__ = "users"

    class GenderEnum(enum.Enum):
        male = "Мужской"
        female = "Женский"

    user_id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    gender: Mapped[GenderEnum] = mapped_column(Enum(GenderEnum), nullable=False)
    is_trainer: Mapped[bool] = mapped_column(default=False)
    is_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(server_default=text("NOW()"))

    trainer_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    trainer: Mapped["User"] = relationship(remote_side=user_id)

    schedule_work: Mapped["ScheduleWork"] = relationship(back_populates="trainer")


class Appointment(BASE):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(primary_key=True)
    start_at: Mapped[datetime]
    is_confirmation: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    comment: Mapped[str] = mapped_column(default=None, nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))

    trainer_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))

    @property
    def start_at_str(self):
        return self.start_at.strftime(f'{settings.WEEKDAY_TO_STR[self.start_at.weekday()+1]} %d.%m %H:%M')


class ScheduleWork(BASE):
    __tablename__ = "schedule_works"

    id: Mapped[int] = mapped_column(primary_key=True)

    hours: Mapped[list[int]] = Column(ARRAY(Integer), default=[0])
    free_days: Mapped[list[int]] = Column(ARRAY(Integer), default=[0])
    max_user_per_hour: Mapped[int] = mapped_column(default=3)
    auto_confirmation: Mapped[bool] = mapped_column(default=False)

    trainer_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    trainer: Mapped["User"] = relationship(back_populates="schedule_work")
