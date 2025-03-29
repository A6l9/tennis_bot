from aiogram.types import BotCommand, BotCommandScopeDefault

from loader import bot


async def set_commands():
    commands = [
        BotCommand(command="make_prediction", description="Получить предсказание"),
        BotCommand(command="upload_stat", description="Обновить статистику игроков")
    ]

    return await bot.set_my_commands(commands=commands, scope=BotCommandScopeDefault())
