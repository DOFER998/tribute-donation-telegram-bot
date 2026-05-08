from aiogram.fsm.state import State, StatesGroup


class FundraiserCreate(StatesGroup):
    title = State()
    target = State()
    end_date = State()
    topic = State()
    confirm = State()
