from aiogram.fsm.state import State, StatesGroup


class MakePrediction(StatesGroup):
    write_first_player = State()
    write_second_player = State()
    write_first_rating = State()
    write_second_rating = State()
    court_select = State()


class UploadStat(StatesGroup):
    take_file = State()
