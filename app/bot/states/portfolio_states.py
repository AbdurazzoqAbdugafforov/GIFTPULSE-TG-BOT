"""FSM States for managing portfolio positions."""

from aiogram.fsm.state import State, StatesGroup


class AddPositionSG(StatesGroup):
    waiting_for_symbol = State()
    waiting_for_quantity = State()
    waiting_for_buy_price = State()
