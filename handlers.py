from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import logging

from keyboards import main_menu_kb, world_menu_kb, cancel_kb, lang_selection_kb
from server_manager import ServerManager
import config
from db import get_user_lang, set_user_lang
from locales import t

router = Router()

# Simple FSM for waiting for manual command input
class RconInput(StatesGroup):
    waiting_for_command = State()

def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS

@router.message(Command("start", "menu", "help", "status"))
async def cmd_menu(message: types.Message):
    """Displays main menu, help, or bot status for admins"""
    uid = message.from_user.id
    if not is_admin(uid):
        await message.reply(t("en", "access_denied")) # Default fallback
        return

    lang = get_user_lang(uid)
    if not lang:
        await message.answer(t("en", "choose_lang"), reply_markup=lang_selection_kb())
        return

    if message.text.startswith("/help"):
        await message.answer(t(lang, "help_text"), parse_mode="Markdown")
        return

    if message.text.startswith("/status"):
        running = await ServerManager.is_running()
        rcon = await ServerManager.is_rcon_alive()
        status_str = "🟢" if running else "🔴"
        rcon_str = "🟢" if rcon else "🔴"
        await message.answer(t(lang, "act_status", status_str=status_str, rcon=rcon_str), parse_mode="Markdown")
        return

    running = await ServerManager.is_running()
    status_str = t(lang, "status_running") if running else t(lang, "status_stopped")
    
    text = t(lang, "menu_title", status=status_str)
    await message.answer(text, reply_markup=main_menu_kb(running, lang), parse_mode="Markdown")

@router.message(Command("lang", "language"))
async def cmd_lang(message: types.Message):
    """Change interface language"""
    if not is_admin(message.from_user.id):
        return
    await message.answer(t("en", "choose_lang"), reply_markup=lang_selection_kb())

@router.callback_query(F.data.startswith("setlang_"))
async def handle_lang_selection(call: types.CallbackQuery):
    if not is_admin(call.from_user.id):
        return

    lang = call.data.split("_")[1]
    set_user_lang(call.from_user.id, lang)
    
    await call.answer()
    await call.message.edit_text(t(lang, "lang_selected"))

    running = await ServerManager.is_running()
    status_str = t(lang, "status_running") if running else t(lang, "status_stopped")
    text = t(lang, "menu_title", status=status_str)
    await call.message.answer(text, reply_markup=main_menu_kb(running, lang), parse_mode="Markdown")


@router.callback_query(F.data.startswith("action_"))
async def handle_server_actions(call: types.CallbackQuery, state: FSMContext):
    """Handles basic server actions: start, stop, players, and logs"""
    uid = call.from_user.id
    if not is_admin(uid):
        await call.answer("🚫", show_alert=True)
        return

    lang = get_user_lang(uid) or "en"
    action = call.data.split("_")[1]

    # Lock for concurrent start/stop actions
    if action in ["start", "stop", "restart"]:
        if ServerManager.is_busy:
            await call.answer(t(lang, "server_busy"), show_alert=True)
            return

        ServerManager.is_busy = True
        try:
            if action == "start":
                await call.answer(t(lang, "act_start"))
                success = await ServerManager.start_server()
                if not success:
                    await call.message.edit_text(t(lang, "act_start_fail"), reply_markup=main_menu_kb(True, lang))
                    return

                # Dynamic loading (until RCON is available)
                await call.message.edit_text(t(lang, "server_starting", sec=0), reply_markup=None, parse_mode="Markdown")
                
                is_online = False
                import asyncio
                for i in range(1, 40): # Wait up to 120 seconds
                    await asyncio.sleep(3)
                    # Update every 3rd cycle to avoid Telegram API spam (every 9 sec)
                    if i % 3 == 0:
                        try:
                            await call.message.edit_text(t(lang, "server_starting", sec=i*3), reply_markup=None, parse_mode="Markdown")
                        except Exception:
                            pass

                    if await ServerManager.is_rcon_alive():
                        is_online = True
                        break
                        
                if is_online:
                    await call.message.edit_text(t(lang, "server_online"), reply_markup=main_menu_kb(True, lang), parse_mode="Markdown")
                else:
                    await call.message.edit_text(t(lang, "server_start_timeout"), reply_markup=main_menu_kb(True, lang), parse_mode="Markdown")

            elif action == "stop":
                await call.answer(t(lang, "act_stop"))
                res = await ServerManager.stop_server()
                await call.message.edit_text(t(lang, "act_stop_resp", res=res), reply_markup=main_menu_kb(False, lang), parse_mode="Markdown")

            elif action == "restart":
                await call.answer(t(lang, "act_restart"))
                if not await ServerManager.is_running():
                    await call.message.edit_text(t(lang, "act_restart_fail"), reply_markup=main_menu_kb(False, lang))
                    return
                res = await ServerManager.stop_server()
                await call.message.edit_text(t(lang, "act_restart_ok"), reply_markup=main_menu_kb(False, lang), parse_mode="Markdown")
        finally:
            ServerManager.is_busy = False

    elif action == "status":
        await call.answer()
        running = await ServerManager.is_running()
        rcon = await ServerManager.is_rcon_alive()
        status_str = "🟢" if running else "🔴"
        rcon_str = "🟢" if rcon else "🔴"
        
        main_text = t(lang, "act_status", status_str=status_str, rcon=rcon_str)
        try:
            await call.message.edit_text(main_text, reply_markup=main_menu_kb(running, lang), parse_mode="Markdown")
        except Exception:
            pass # Ignore MessageNotModified if text hasn't changed

    elif action == "players":
        await call.answer(t(lang, "btn_players") + "...")
        res = await ServerManager.run_command("list")
        await call.message.edit_text(t(lang, "act_players", res=res), reply_markup=main_menu_kb(True, lang), parse_mode="Markdown")

    elif action == "logs":
        await call.answer(t(lang, "btn_logs") + "...")
        logs = await ServerManager.get_logs(20)
        logs_safe = logs.replace("`", "")[-3900:]
        await call.message.answer(t(lang, "act_logs", logs=logs_safe), reply_markup=main_menu_kb(await ServerManager.is_running(), lang), parse_mode="Markdown")

    elif action == "custom":
        if call.data == "action_custom_cmd":
            await call.answer()
            await state.set_state(RconInput.waiting_for_command)
            await call.message.edit_text(
                t(lang, "cmd_prompt"), 
                reply_markup=cancel_kb(lang), parse_mode="Markdown"
            )

@router.callback_query(F.data.startswith("cmd_"))
async def handle_rcon_commands(call: types.CallbackQuery):
    """Executes predefined RCON commands (time/weather)"""
    uid = call.from_user.id
    if not is_admin(uid):
        await call.answer("🚫", show_alert=True)
        return

    lang = get_user_lang(uid) or "en"
    command = call.data.replace("cmd_", "").replace("_", " ")
    
    await call.answer(t(lang, "cmd_executing", cmd=command))
    res = await ServerManager.run_command(command)
    
    await call.message.answer(t(lang, "cmd_result", cmd=command, res=res), parse_mode="Markdown")

@router.callback_query(F.data.startswith("menu_"))
async def handle_menus(call: types.CallbackQuery, state: FSMContext):
    """Switch between submenus"""
    uid = call.from_user.id
    if not is_admin(uid):
        await call.answer("🚫", show_alert=True)
        return

    lang = get_user_lang(uid) or "en"
    await state.clear()  # Reset if user was waiting for command input

    menu = call.data.split("_")[1]
    running = await ServerManager.is_running()

    if menu == "main":
        status_str = t(lang, "status_running") if running else t(lang, "status_stopped")
        await call.message.edit_text(
            t(lang, "menu_title", status=status_str), 
            reply_markup=main_menu_kb(running, lang), parse_mode="Markdown"
        )
    elif menu == "world":
        await call.message.edit_text(t(lang, "world_title"), reply_markup=world_menu_kb(lang), parse_mode="Markdown")

@router.message(RconInput.waiting_for_command, F.text)
async def process_custom_command(message: types.Message, state: FSMContext):
    """Handles manual command input from admin"""
    uid = message.from_user.id
    if not is_admin(uid):
        return
        
    lang = get_user_lang(uid) or "en"
    command = message.text.strip()
    if command.startswith("/"):
        command = command[1:] # RCON accepts commands without slash

    logging.info(f"Admin {message.from_user.id} Executing RCON: {command}")
    
    res = await ServerManager.run_command(command)
    await message.answer(t(lang, "custom_cmd_sent", cmd=command, res=res), parse_mode="Markdown", reply_markup=main_menu_kb(await ServerManager.is_running(), lang))
    await state.clear()
