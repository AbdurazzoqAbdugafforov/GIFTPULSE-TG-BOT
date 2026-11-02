"""FSM States for submitting manual subscription payments."""

from aiogram.fsm.state import State, StatesGroup


class SubmitPaymentSG(StatesGroup):
    waiting_for_plan = State()
    waiting_for_proof = State()
