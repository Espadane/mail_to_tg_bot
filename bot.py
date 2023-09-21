import os
import asyncio
import aioschedule
from aiogram import Bot, Dispatcher, executor, types
from dotenv import load_dotenv
from mail import get_mails
from aiogram.types import InputFile



load_dotenv()
bot = Bot(token=os.getenv("BOT_TOKEN"))
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def start_command(msg: types.Message):
    await msg.answer('Доступ к боту только через администратора. Он сам напишет когда будет нужно.')
    users_to_send = await get_users_to_send()
    user_id = msg.from_user.id
    user_name = msg.from_user.username
    if str(user_id) not in users_to_send:
        admin_id = os.getenv("ADMIN_ID")
        await bot.send_message(int(admin_id), f'Пользователь @{user_name} с id {user_id} хочет получить доступ к боту.')
    else:
        await msg.answer('У вас есть доступ, теперь вы будете получать сообщения об ошибках.')

async def get_users_to_send():
    users = []
    with open('./confirmed_users.txt', 'r') as file:
        for line in file:
            users.append(line.strip())
        
    return users

async def send_mails():
    users_to_send = await get_users_to_send()
    mails = await get_mails()
    for user in users_to_send:
        for mail in mails:
            message = f"Тема: {mail['mail_subject']}\nТекст: {mail['mail_text']}"
            await bot.send_message(int(user), message)
            for attach in mail["mail_attachments"]:
                file_path = f"./attach/{mail['now_date']}/{attach}"
                await bot.send_document(int(user), InputFile(file_path))

async def scheduler() -> None:
    minutes = os.getenv("CHECK_MINUTES")
    aioschedule.every(int(minutes)).minutes.do(send_mails)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)
        
async def on_startup(_) -> None:
    asyncio.create_task(scheduler())


if __name__=='__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)