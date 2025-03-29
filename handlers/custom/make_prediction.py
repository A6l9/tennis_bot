import asyncio

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.filters.command import Command
from aiogram.filters import StateFilter
from aiogram.exceptions import TelegramBadRequest

from state_storage.states import MakePrediction
from loader import bot, logger
from keyboards.inline.skip_keyboard import create_skip_rating_writing
from keyboards.inline.court_select import create_court_select_keyboard
from keyboards.inline.cancel_keyboard import create_cancel_keyboard
from prediction_functions import make_prediction


router = Router(name="make_prediction")


@router.message(Command("make_prediction"))
async def make_prediction_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Введите имя первого игрока 👇", reply_markup=create_cancel_keyboard())
    await state.set_state(MakePrediction.write_first_player)


@router.message(MakePrediction.write_first_player)
async def take_first_player(message: Message, state: FSMContext) -> None:
    await state.set_data({"first_player": message.text})
    await message.answer("Введите имя второго игрока 👇", reply_markup=create_cancel_keyboard())
    await state.set_state(MakePrediction.write_second_player)


@router.message(MakePrediction.write_second_player)
async def take_second_player(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    data["second_player"] = message.text
    await state.set_data(data)
    await message.answer("Введите рейтинг первого игрока 👇", reply_markup=create_skip_rating_writing())
    await state.set_state(MakePrediction.write_first_rating)


@router.message(MakePrediction.write_first_rating)
async def take_first_rating(message: Message, state: FSMContext) -> None:
    if message.text:
        data = await state.get_data()
        data["first_rating"] = message.text
        await state.set_data(data)
    await bot.send_message(chat_id=message.from_user.id, text="Введите рейтинг второго игрока 👇", reply_markup=create_skip_rating_writing())
    await state.set_state(MakePrediction.write_second_rating)


@router.message(MakePrediction.write_second_rating)
async def take_second_rating(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    data["second_rating"] = message.text
    await state.set_data(data)
    await message.answer(text="Выберите тип корта 👇", reply_markup=create_court_select_keyboard())
    await state.set_state(MakePrediction.court_select)


@router.callback_query(F.data.startswith("court-type"), StateFilter(MakePrediction.court_select))
async def take_court_type(call: CallbackQuery, state: FSMContext) -> None:
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest as exc:
        logger.debug(exc)
    data = await state.get_data()
    result = await asyncio.to_thread(make_prediction(name1=data["first_player"],
                                            name2=data["second_player"],
                                            r1=data.get("first_rating"),
                                            r2=data.get("second_rating"),
                                            court=call.data.split(":")[1]
                                            ))


@router.callback_query(StateFilter(MakePrediction.write_first_rating, MakePrediction.write_second_rating),
                       F.data == "skip-rating-writing")
async def skip_rating(call: CallbackQuery, state: FSMContext) -> None:
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest as exc:
        logger.debug(exc)
    state_name = await state.get_state()
    if state_name == "MakePrediction:write_first_rating":
        await state.set_state(MakePrediction.write_second_rating)
        await take_first_rating(Message(message_id=call.message.message_id,
                                         text=None,
                                         date=call.message.date,
                                         chat=call.message.chat,
                                         from_user=call.from_user), state)
    elif state_name == "MakePrediction:write_second_rating":
        await state.set_state(MakePrediction.court_select)
        await call.message.answer("Выберите тип корта 👇", reply_markup=create_court_select_keyboard())      
