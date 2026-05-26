from aiogram import Router, types, F
from aiogram.filters import Command
from keyboards import server_picker_kb, main_menu_kb
from locales import t
from db import set_last_server

router = Router()

async def show_picker(message_or_call, lang: str, registry):
    """Utility to fetch statuses and display picker"""
    servers_list = registry.list_all()
    statuses = await registry.status_all()
    servers_with_status = [(sid, name, statuses.get(sid, False)) for sid, name in servers_list]
    
    kb = server_picker_kb(servers_with_status, lang)
    
    if isinstance(message_or_call, types.Message):
        await message_or_call.answer(t(lang, "pick_server"), reply_markup=kb, parse_mode="Markdown")
    else:
        await message_or_call.message.edit_text(t(lang, "pick_server"), reply_markup=kb, parse_mode="Markdown")

@router.message(Command("switch"))
async def cmd_switch(message: types.Message, lang: str, registry):
    """Command to switch active server"""
    if registry.is_single_server():
        return
    await show_picker(message, lang, registry)

@router.callback_query(F.data == "menu_picker")
async def callback_menu_picker(call: types.CallbackQuery, lang: str, registry):
    """Callback to switch server from main menu"""
    if registry.is_single_server():
        await call.answer()
        return
    await call.answer()
    await show_picker(call, lang, registry)

@router.callback_query(F.data.startswith("select_server_"))
async def handle_server_selection(call: types.CallbackQuery, lang: str, registry):
    """Callback when a server is chosen"""
    server_id = call.data.replace("select_server_", "")
    server = registry.get(server_id)
    if not server:
        await call.answer("❌ Server not found", show_alert=True)
        return
        
    set_last_server(call.from_user.id, server_id)
    await call.answer()
    
    # Notify user of active server change
    await call.message.answer(t(lang, "server_selected", name=server.config.display_name), parse_mode="Markdown")
    
    is_running = await server.is_running()
    status_str = t(lang, "status_running") if is_running else t(lang, "status_stopped")
    text = t(lang, "menu_title", server_name=server.config.display_name, status=status_str)
    
    await call.message.edit_text(
        text,
        reply_markup=main_menu_kb(is_running, lang, registry.is_single_server()),
        parse_mode="Markdown"
    )
