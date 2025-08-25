#states/user_states.py

from aiogram.fsm.state import State, StatesGroup


class UserState(StatesGroup):
    selecting_subject = State()
    selecting_class = State()
    selecting_theme = State()
    selecting_paragraph = State()
    testing = State()
    taking_test = State()
