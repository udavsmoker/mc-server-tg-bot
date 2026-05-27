from aiogram import Router, types, F
from aiogram.filters import Command
from keyboards import main_menu_kb, lang_selection_kb
from locales import t
from db import get_user_lang, set_user_lang

router = Router()

@router.message(Command("start", "menu"))
async def cmd_menu(message: types.Message, lang: str, registry, server=None):
    """Displays the main menu or requests language selection"""
    uid = message.from_user.id
    
    # If no language is selected yet
    if not get_user_lang(uid):
        await message.answer(t("en", "choose_lang"), reply_markup=lang_selection_kb())
        return

    if not server:
        # In multi-server mode, try to resolve their last active server
        from db import get_last_server
        active_server_id = get_last_server(uid)
        server = registry.get(active_server_id) if active_server_id else None

    if not server:
        # If still no active server is selected, show the server picker
        from keyboards import server_picker_kb
        servers_list = registry.list_all()
        statuses = await registry.status_all()
        servers_with_status = [(sid, name, statuses.get(sid, False)) for sid, name in servers_list]
        await message.answer(
            t(lang, "no_server_selected"),
            reply_markup=server_picker_kb(servers_with_status, lang),
            parse_mode="Markdown"
        )
        return

    is_running = await server.is_running()
    status_str = t(lang, "status_running") if is_running else t(lang, "status_stopped")
    
    text = t(lang, "menu_title", server_name=server.config.display_name, status=status_str)
    await message.answer(
        text,
        reply_markup=main_menu_kb(is_running, lang, registry.is_single_server()),
        parse_mode="Markdown"
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message, lang: str):
    """Display help information"""
    await message.answer(t(lang, "help_text"), parse_mode="Markdown")

@router.message(Command("status"))
async def cmd_status(message: types.Message, lang: str, server=None):
    """Quick status check for active server"""
    if not server:
        return
        
    running = await server.is_running()
    rcon = await server.is_rcon_alive()
    status_str = "🟢" if running else "🔴"
    rcon_str = "🟢" if rcon else "🔴"
    
    await message.answer(
        t(lang, "act_status", server_name=server.config.display_name, status_str=status_str, rcon=rcon_str),
        parse_mode="Markdown"
    )

@router.message(Command("servers"))
async def cmd_servers(message: types.Message, lang: str, registry):
    """Shows status of all registered servers"""
    if registry.is_single_server():
        return
        
    statuses = await registry.status_all()
    lines = []
    for sid, display_name in registry.list_all():
        is_running = statuses.get(sid, False)
        status_dot = "🟢 ЗАПУЩЕН" if lang == "ru" else "🟢 RUNNING"
        if not is_running:
            status_dot = "🔴 ВЫКЛЮЧЕН" if lang == "ru" else "🔴 STOPPED"
        lines.append(f"- **{display_name}**: {status_dot}")
        
    list_str = "\n".join(lines)
    await message.answer(t(lang, "servers_overview", list=list_str), parse_mode="Markdown")

@router.message(Command("lang", "language"))
async def cmd_lang(message: types.Message):
    """Change interface language prompt"""
    await message.answer(t("en", "choose_lang"), reply_markup=lang_selection_kb())

@router.callback_query(F.data.startswith("setlang_"))
async def handle_lang_selection(call: types.CallbackQuery, registry, server=None):
    """Callback for language selection"""
    lang = call.data.split("_")[1]
    set_user_lang(call.from_user.id, lang)
    
    await call.answer()
    await call.message.edit_text(t(lang, "lang_selected"))

    # If single server or active server exists, show main menu
    if registry.is_single_server():
        default_sid = registry.default_server_id()
        server = registry.get(default_sid)
    
    if server:
        is_running = await server.is_running()
        status_str = t(lang, "status_running") if is_running else t(lang, "status_stopped")
        text = t(lang, "menu_title", server_name=server.config.display_name, status=status_str)
        await call.message.answer(
            text,
            reply_markup=main_menu_kb(is_running, lang, registry.is_single_server()),
            parse_mode="Markdown"
        )
    else:
        # Prompt to select a server in multi-server config
        from keyboards import server_picker_kb
        servers_list = registry.list_all()
        statuses = await registry.status_all()
        servers_with_status = [(sid, name, statuses.get(sid, False)) for sid, name in servers_list]
        await call.message.answer(
            t(lang, "no_server_selected"),
            reply_markup=server_picker_kb(servers_with_status, lang),
            parse_mode="Markdown"
        )
