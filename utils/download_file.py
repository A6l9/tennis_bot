import os

from aiogram import types
from pathlib import Path
import aiohttp

from loader import logger, bot


async def download_file(message: types.Message):
    document = message.document
    file_id = document.file_id

    file_info = await bot.get_file(file_id)
    file_path = file_info.file_path

    file_url = f"https://api.telegram.org/file/bot{os.getenv("BOT_TOKEN")}/{file_path}"
    
    save_path = Path(__file__).parent.parent
    save_path = save_path / document.file_name

    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as response:
            if response.status == 200:
                with save_path.open("wb") as f:
                    f.write(await response.read())

    logger.debug("The file was successfuly received")
    return save_path
