import os
import asyncio

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from keyboards.inline.cancel_keyboard import create_cancel_keyboard
from state_storage.states import UploadStat
from utils.download_file import download_file
from loader import logger
from stat_upload import add_batch_matches_and_update_stats


router = Router(name="upload_stat")


@router.message(Command("upload_stat"))
async def upload_stat_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Пришлите документ в формате \".xlsx\"", reply_markup=create_cancel_keyboard())
    await state.set_state(UploadStat.take_file)


@router.message(StateFilter(UploadStat.take_file), F.document)
async def take_file(message: Message, state: FSMContext) -> None:
    if message.document.file_name.endswith(".xlsx"):
        save_path = await download_file(message)
        updated_stats = await asyncio.to_thread(add_batch_matches_and_update_stats, new_matches_xlsx=save_path)
        os.remove(save_path)
        logger.debug("The file was successfuly deleted")
        await state.clear()
    else:
        await message.answer("Этот файл имеет недопустимый формат, пришлите файл в формате \".xlsx\"")
