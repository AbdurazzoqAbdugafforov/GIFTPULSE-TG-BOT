"""FSM States for creating and managing price alerts."""

from aiogram.fsm.state import State, StatesGroup


class CreateAlertSG(StatesGroup):
    waiting_for_symbol = State()
    waiting_for_type = State()
    waiting_for_target = State()
    waiting_for_mode = State()
