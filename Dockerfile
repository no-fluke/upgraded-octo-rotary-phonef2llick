FROM python:3.10.14-slim-bullseye

RUN apt update && apt upgrade -y && apt install git -y && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /requirements.txt
RUN pip3 install -U pip && pip3 install -U -r requirements.txt

RUN mkdir /rexbots
WORKDIR /rexbots
COPY . /rexbots

# Heroku dynamically assigns $PORT — do NOT hardcode EXPOSE
# bot.py reads PORT from environment, so this just works
CMD ["python", "bot.py"]
