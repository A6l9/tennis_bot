import asyncio

from aiogram.types import BotCommandScopeDefault

from loader import bot, dp, logger
from handlers.custom.make_prediction import router as make_prediction
from handlers.custom.cancel_handler import router as cancel_router
from handlers.custom.upload_stat import router as upload_stat_router
from set_commands import set_commands


async def main() -> None:
    bot_info = await bot.get_me()
    await bot.delete_my_commands(scope=BotCommandScopeDefault())
    await set_commands()
    logger.debug(f"Bot {bot_info.username} starts working")
    dp.include_routers(make_prediction, cancel_router, upload_stat_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main=main())
