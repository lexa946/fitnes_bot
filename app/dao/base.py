from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from app.database import async_session, BASE


class BaseDAO:
    model = None

    @classmethod
    async def find_one_or_none(cls, **filter_by) -> model:
        async with async_session() as session:
            """
               Асинхронно находит и возвращает один экземпляр модели по указанным критериям или None.

               Аргументы:
                   data_id: Критерии фильтрации в виде идентификатора записи.

               Возвращает:
                   Экземпляр модели или None, если ничего не найдено.
            """
            result = await session.scalar(
                select(cls.model).filter_by(**filter_by)
            )
            return result

    @classmethod
    async def find_all(cls, **filter_by) -> list[model]:
        """
            Асинхронно находит и возвращает все экземпляры модели, удовлетворяющие указанным критериям.

            Аргументы:
                **filter_by: Критерии фильтрации в виде именованных параметров.

            Возвращает:
                Список экземпляров модели.
        """
        async with async_session() as session:
            result = await session.scalars(
                select(cls.model).filter_by(**filter_by)
            )
            return result.all()

    @classmethod
    async def add(cls, **values) -> model:
        """
            Асинхронно создает новый экземпляр модели с указанными значениями.

            Аргументы:
                **values: Именованные параметры для создания нового экземпляра модели.

            Возвращает:
                Созданный экземпляр модели.
        """
        async with async_session() as session:
            new_instance = cls.model(**values)
            session.add(new_instance)
            try:
                await session.commit()
            except SQLAlchemyError as e:
                await session.rollback()
                raise e
        return new_instance

    @classmethod
    async def patch(cls, instance: BASE, **values) -> model:
        """
           Редактируем модель
        """
        for key, value in values.items():
            setattr(instance, key, value)

        primary_keys_map = {
                primary_key.name: getattr(instance, primary_key.name) for primary_key in instance.__mapper__.primary_key
            }
        async with async_session() as session:
            query = (update(cls.model)
                     .filter_by(**primary_keys_map)
                     .values(**values))
            await session.execute(query)
            # session.add(query)
            await session.commit()
        return instance

    @classmethod
    async def many_patch(cls, instances: list[BASE], **values) -> list[model]:

        for key, value in values.items():
            for instance in instances:
                setattr(instance, key, value)

        async with async_session() as session:
            for key, value in values.items():
                for instance in instances:
                    setattr(instance, key, value)
                    session.add(instance)
            await session.commit()
        return instances


    @classmethod
    async def delete(cls, instance: BASE) -> model:
        """
            Удаляет инстанс из БД
        """
        async with async_session() as session:
            await session.delete(instance)
            await session.commit()
