import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from keyboards import main_menu_kb
from locales import t

router = Router()
logger = logging.getLogger(__name__)

class RconInput(StatesGroup):
    waiting_for_command = State()

@router.message(RconInput.waiting_for_command, F.text)
async def process_custom_command(message: types.Message, state: FSMContext, lang: str, registry, server=None):
    """Handles manual command input from admin"""
    if not server:
        await message.answer("❌ Error: Active server not found.")
        await state.clear()
        return

    uid = message.from_user.id
    command = message.text.strip()
    if command.startswith("/"):
        command = command[1:]  # RCON accepts commands without slash

    logger.info(f"[{server.server_id}] Admin {uid} custom RCON: {command}")
    
    res = await server.run_command(command)
    is_running = await server.is_running()
    
    await message.answer(
        t(lang, "custom_cmd_sent", cmd=command, res=res), 
        parse_mode="Markdown", 
        reply_markup=main_menu_kb(is_running, lang, registry.is_single_server())
    )
    await state.clear()
