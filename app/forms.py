from aiogram.fsm.state import StatesGroup, State


class RegistrationForm(StatesGroup):
    FIO = State()
    gender = State()


class ChangeFIOForm(StatesGroup):
    FIO = State()


class RegisterAppointment(StatesGroup):
    comment = State()

class ClientComment(StatesGroup):
    comment = State()

class ChangeSchedule(StatesGroup):
    hours = State()


class ChangeFreeDays(StatesGroup):
    days = State()


class Training(StatesGroup):
    program = State()

class Nutritionist(StatesGroup):
    products = State()