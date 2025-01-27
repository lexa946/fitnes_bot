from pydantic import model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    BOT_TOKEN: str
    DB_USERNAME: str
    DB_PASSWORD: str
    DB_NAME: str
    DB_HOST: str
    DB_PORT: str
    DATABASE_URL: str
    MAX_USER_APPOINTMENTS: int
    WEEKDAY_TO_STR: dict


    @model_validator(mode="before")
    def set_more_field(cls, values):
        values["DATABASE_URL"] = (f"postgresql+asyncpg://{values['DB_USERNAME']}:{values['DB_PASSWORD']}"
                                  f"@{values['DB_HOST']}:{values['DB_PORT']}/{values['DB_NAME']}")
        values['WEEKDAY_TO_STR'] = {
            1: "Пн", 2: "Вт", 3: "Ср", 4: "Чт", 5: "Пт", 6: "Сб", 7: "Вс"
        }
        return values

    class Config:
        env_file = '.env'


settings = Settings()