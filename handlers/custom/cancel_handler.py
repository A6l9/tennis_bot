from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from loader import logger
from state_storage.states import UploadStat, MakePrediction


router = Router(name="cancel_handler")


@router.callback_query(F.data == "cancel-event", StateFilter(UploadStat.take_file,
                                                             MakePrediction.write_first_player,
                                                             MakePrediction.write_second_player))
async def cancel_event(call: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    try:
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.answer("Вы отменили предыдущее действие 🙅‍♂️")
    except TelegramBadRequest as exc:
        logger.debug(exc)
