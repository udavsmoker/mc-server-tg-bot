import asyncio
import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from keyboards import main_menu_kb
from locales import t

router = Router()
logger = logging.getLogger(__name__)

@router.callback_query(F.data.startswith("action_"))
async def handle_server_actions(call: types.CallbackQuery, state: FSMContext, lang: str, registry, server=None):
    """Handles basic server actions: start, stop, restart, status, players, logs"""
    if not server:
        await call.answer("🚫", show_alert=True)
        return

    action = call.data.split("_")[1]

    # Concurrent locks per server for start/stop/restart
    if action in ["start", "stop", "restart"]:
        if server.lock.locked():
            await call.answer(t(lang, "server_busy"), show_alert=True)
            return

        async with server.lock:
            uid = call.from_user.id
            if action == "start":
                logger.info(f"[{server.server_id}] Admin {uid} → Clicked Start")
                await call.answer(t(lang, "act_start"))
                
                success = await server.start_server()
                if not success:
                    await call.message.edit_text(
                        t(lang, "act_start_fail"), 
                        reply_markup=main_menu_kb(True, lang, registry.is_single_server())
                    )
                    return

                # Wait loop for RCON
                await call.message.edit_text(t(lang, "server_starting", sec=0), reply_markup=None, parse_mode="Markdown")
                
                is_online = False
                for i in range(1, 40):  # Wait up to 120 seconds
                    await asyncio.sleep(3)
                    if i % 3 == 0:
                        try:
                            await call.message.edit_text(t(lang, "server_starting", sec=i*3), reply_markup=None, parse_mode="Markdown")
                        except Exception:
                            pass

                    if await server.is_rcon_alive():
                        is_online = True
                        break
                        
                if is_online:
                    await call.message.edit_text(
                        t(lang, "server_online"), 
                        reply_markup=main_menu_kb(True, lang, registry.is_single_server()), 
                        parse_mode="Markdown"
                    )
                else:
                    await call.message.edit_text(
                        t(lang, "server_start_timeout"), 
                        reply_markup=main_menu_kb(True, lang, registry.is_single_server()), 
                        parse_mode="Markdown"
                    )

            elif action == "stop":
                logger.info(f"[{server.server_id}] Admin {uid} → Clicked Stop")
                await call.answer(t(lang, "act_stop"))
                res = await server.stop_server()
                await call.message.edit_text(
                    t(lang, "act_stop_resp", res=res), 
                    reply_markup=main_menu_kb(False, lang, registry.is_single_server()), 
                    parse_mode="Markdown"
                )

            elif action == "restart":
                logger.info(f"[{server.server_id}] Admin {uid} → Clicked Restart (Auto-cycle)")
                await call.answer(t(lang, "btn_restart") + "...")
                
                if not await server.is_running():
                    await call.message.edit_text(
                        t(lang, "act_restart_fail"), 
                        reply_markup=main_menu_kb(False, lang, registry.is_single_server())
                    )
                    return

                # 1. Stop Server
                await call.message.edit_text(
                    t(lang, "restart_stopping", name=server.config.display_name), 
                    reply_markup=None, 
                    parse_mode="Markdown"
                )
                await server.stop_server()

                # 2. Wait for shutdown (poll is_running every 3s)
                shutdown_success = False
                for sec in range(3, 60, 3):
                    await asyncio.sleep(3)
                    await call.message.edit_text(
                        t(lang, "restart_stopping", name=server.config.display_name) + "\n" + t(lang, "restart_waiting", sec=sec),
                        reply_markup=None,
                        parse_mode="Markdown"
                    )
                    if not await server.is_running():
                        shutdown_success = True
                        break

                if not shutdown_success:
                    await call.message.edit_text(
                        t(lang, "restart_fail") + " (Server did not shut down)",
                        reply_markup=main_menu_kb(True, lang, registry.is_single_server()),
                        parse_mode="Markdown"
                    )
                    return

                # 3. Start Server
                await call.message.edit_text(
                    t(lang, "restart_starting"),
                    reply_markup=None,
                    parse_mode="Markdown"
                )
                await server.start_server()

                # 4. Wait for boot (poll is_rcon_alive)
                boot_success = False
                for sec in range(3, 120, 3):
                    await asyncio.sleep(3)
                    await call.message.edit_text(
                        t(lang, "restart_starting") + "\n" + t(lang, "server_starting", sec=sec),
                        reply_markup=None,
                        parse_mode="Markdown"
                    )
                    if await server.is_rcon_alive():
                        boot_success = True
                        break

                if boot_success:
                    await call.message.edit_text(
                        t(lang, "restart_done", name=server.config.display_name),
                        reply_markup=main_menu_kb(True, lang, registry.is_single_server()),
                        parse_mode="Markdown"
                    )
                else:
                    await call.message.edit_text(
                        t(lang, "restart_fail") + " (Server starting too slow)",
                        reply_markup=main_menu_kb(True, lang, registry.is_single_server()),
                        parse_mode="Markdown"
                    )

    elif action == "status":
        await call.answer()
        running = await server.is_running()
        rcon = await server.is_rcon_alive()
        status_str = "🟢" if running else "🔴"
        rcon_str = "🟢" if rcon else "🔴"
        
        main_text = t(lang, "act_status", server_name=server.config.display_name, status_str=status_str, rcon=rcon_str)
        try:
            await call.message.edit_text(
                main_text, 
                reply_markup=main_menu_kb(running, lang, registry.is_single_server()), 
                parse_mode="Markdown"
            )
        except Exception:
            pass # Ignore MessageNotModified if status hasn't changed

    elif action == "players":
        await call.answer(t(lang, "btn_players") + "...")
        res = await server.run_command("list")
        await call.message.edit_text(
            t(lang, "act_players", res=res), 
            reply_markup=main_menu_kb(await server.is_running(), lang, registry.is_single_server()), 
            parse_mode="Markdown"
        )

    elif action == "logs":
        await call.answer(t(lang, "btn_logs") + "...")
        logs = await server.get_logs(20)
        logs_safe = logs.replace("`", "")[-3900:]
        await call.message.answer(
            t(lang, "act_logs", logs=logs_safe), 
            reply_markup=main_menu_kb(await server.is_running(), lang, registry.is_single_server()), 
            parse_mode="Markdown"
        )

    elif action == "custom":
        if call.data == "action_custom_cmd":
            await call.answer()
            from handlers.rcon import RconInput
            await state.set_state(RconInput.waiting_for_command)
            await call.message.edit_text(
                t(lang, "cmd_prompt"), 
                reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[
                    [types.InlineKeyboardButton(text=t(lang, "btn_cancel"), callback_data="menu_main")]
                ]), 
                parse_mode="Markdown"
            )
