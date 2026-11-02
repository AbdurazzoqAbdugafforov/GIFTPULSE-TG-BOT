"""FSM States for administrative actions (broadcast, price edits)."""

from aiogram.fsm.state import State, StatesGroup


class AdminBroadcastSG(StatesGroup):
    waiting_for_message = State()
    confirm_broadcast = State()


class AdminEditPlanSG(StatesGroup):
    waiting_for_plan_code = State()
    waiting_for_new_price = State()
