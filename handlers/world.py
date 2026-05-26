import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from keyboards import main_menu_kb, world_menu_kb
from locales import t

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data.startswith("cmd_"))
async def handle_predefined_commands(call: types.CallbackQuery, lang: str, server=None):
    """Executes predefined RCON commands (time/weather)"""
    if not server:
        await call.answer("🚫", show_alert=True)
        return

    uid = call.from_user.id
    command = call.data.replace("cmd_", "").replace("_", " ")
    
    logger.info(f"[{server.server_id}] Admin {uid} Predefined RCON: {command}")
    await call.answer(t(lang, "cmd_executing", cmd=command))
    
    res = await server.run_command(command)
    await call.message.answer(t(lang, "cmd_result", cmd=command, res=res), parse_mode="Markdown")

@router.callback_query(F.data.startswith("menu_"))
async def handle_menus(call: types.CallbackQuery, state: FSMContext, lang: str, registry, server=None):
    """Switch between main menu and world menu"""
    if not server:
        await call.answer("🚫", show_alert=True)
        return

    await state.clear()
    menu = call.data.split("_")[1]
    
    if menu == "main":
        is_running = await server.is_running()
        status_str = t(lang, "status_running") if is_running else t(lang, "status_stopped")
        await call.message.edit_text(
            t(lang, "menu_title", server_name=server.config.display_name, status=status_str),
            reply_markup=main_menu_kb(is_running, lang, registry.is_single_server()),
            parse_mode="Markdown"
        )
    elif menu == "world":
        await call.message.edit_text(
            t(lang, "world_title"),
            reply_markup=world_menu_kb(lang),
            parse_mode="Markdown"
        )
