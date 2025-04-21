import asyncio
import os

from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv())

from database.engine import create_db, drop_db, session_maker

from aiogram import Bot, Dispatcher

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from handlers.admin_authorization import admin_login_router
from handlers.admin_commands import admin_commands_router
from handlers.worker_authorization import worker_authorization_router
from handlers.worker_commands import worker_commands_router

from middlewares.db import DataBaseSession
from sqlalchemy.ext.asyncio import AsyncSession

import additional_functions


bot = Bot(token=os.getenv('TOKEN'))
dp = Dispatcher()

dp.include_router(admin_login_router)
dp.include_router(admin_commands_router)
dp.include_router(worker_authorization_router)
dp.include_router(worker_commands_router)


async def main():
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    # scheduler.add_job(additional_functions.mailing_before_the_event,
    #                   trigger="cron", hour="10", minute="00", kwargs={"bot": bot})
    # scheduler.add_job(additional_functions.mailing_after_the_event,
    #                   trigger="cron", hour="20", minute="00", kwargs={"bot": bot})
    scheduler.add_job(additional_functions.sending_reminders_about_work_shifts, trigger="interval", seconds=1800,
                      kwargs={"bot": bot})
    scheduler.start()
    # await drop_db()
    await create_db()
    dp.update.outer_middleware(DataBaseSession(session_pool=session_maker))
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == '__main__':
    asyncio.run(main())

