import urllib3

from g4f import ChatCompletion


MAIN_PROMPT = (
        "Ты мой персональный диетолог."
        "Я буду консультироваться у тебя по поводу калорийности какой-либо еды."
        "Ты должен мне ответить сколько калорий на 100 грамм продукта и содержание БЖУ."
        "Ответ должен быть краткий и лаконичный. Структура ответа должна быть следующей: "
        "Название продукта: {новая строка}"
        " граммовка | калорийность | белки/жиры/углеводы."
        "Если я указываю граммовку, тогда необходимо пересчитать калории и БЖУ на указанные мною граммы "
        "и не нужно указывать калорийность и БЖУ на 100 грамм."
        "Если будет разброс по калорийности, то бери среднее значение."
        "Расскажи мне про: {product}"
    )

async def get_gpt_answer(request: str, model="gpt-4", image=None) -> str:

    # Отключаем предупреждения, связанные с SSL
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    response = await ChatCompletion.create_async(
        model=model,
        messages=[
            {
                "role": "user",
                "content": MAIN_PROMPT.replace("{product}", request)
            }
        ],
    )

    return response



if __name__ == '__main__':
    import asyncio
    message = asyncio.run(get_gpt_answer("тушеная говядина 150г", "gpt-4o-mini"))
    print(message)