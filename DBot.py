import os
import discord
import asyncio
import random
from datetime import datetime, timedelta
from discord.ext import commands
from dotenv import load_dotenv
import openai
import logging
from collections import deque

# === ЛОГИ ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("bot.log", mode="w", encoding="utf-8"),
        logging.StreamHandler()  # дублирует в консоль
    ]
)

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED_CHANNELS = [int(ch) for ch in os.getenv("ALLOWED_CHANNELS").split(",")]
ACTIVE_HOURS = [int(h) for h in os.getenv("ACTIVE_HOURS").split("-")]

openai.api_key = OPENAI_API_KEY
bot = commands.Bot(command_prefix="!", self_bot=True)

last_response_time = None
hourly_timestamps = deque()

MAX_MESSAGES_PER_HOUR = 30
MIN_TIME_BETWEEN_MESSAGES = timedelta(seconds=60)

@bot.event
async def on_ready():
    logging.info(f"Бот вошёл как {bot.user}")

@bot.event
async def on_message(message):
    global last_response_time

    if message.author.id != bot.user.id:
        return

    now = datetime.now()

    if now.hour < ACTIVE_HOURS[0] or now.hour > ACTIVE_HOURS[1]:
        logging.info("Вне активных часов, сообщение проигнорировано.")
        return

    if message.channel.id not in ALLOWED_CHANNELS:
        logging.info(f"Канал {message.channel.id} не разрешён.")
        return

    if message.content.startswith("!"):
        return

    if last_response_time and now - last_response_time < MIN_TIME_BETWEEN_MESSAGES:
        logging.info("Превышен лимит по времени (1 сообщение в минуту)")
        return

    hourly_timestamps.append(now)
    while hourly_timestamps and now - hourly_timestamps[0] > timedelta(hours=1):
        hourly_timestamps.popleft()

    if len(hourly_timestamps) > MAX_MESSAGES_PER_HOUR:
        logging.warning("Превышен лимит сообщений в час")
        return

    await asyncio.sleep(random.uniform(2, 5))

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "_описание_здесь_"},
                {"role": "user", "content": message.content}
            ]
        )
        reply = response.choices[0].message.content
        await message.channel.send(reply)
        last_response_time = now
        logging.info(f"Ответ отправлен: {reply[:60]}...")

    except Exception as e:
        logging.error(f" Ошибка при обращении к OpenAI: {e}")

