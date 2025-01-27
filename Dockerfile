FROM python:3.12-slim
LABEL authors="APozhar"

#ENTRYPOINT ["top", "-b"]

RUN mkdir -p /bot
WORKDIR /bot

COPY app app
COPY main.py main.py
COPY requirements.txt requirements.txt
COPY .env .env

RUN python -m pip install --upgrade pip && pip install -r requirements.txt

CMD ["python", "/bot/main.py"]