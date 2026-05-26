from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, TelegramObject
from typing import Callable, Dict, Any, Awaitable

class AdminMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)
            
        import config
        from locales import t

        if user.id not in config.ADMIN_IDS:
            if isinstance(event, Message):
                await event.reply(t("en", "access_denied"))
            elif isinstance(event, CallbackQuery):
                await event.answer("🚫", show_alert=True)
            return

        return await handler(event, data)

class ActiveServerMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        from db import get_user_lang, get_last_server
        from keyboards import server_picker_kb
        from locales import t
        
        # 1. Resolve language and inject it for convenience
        lang = get_user_lang(user.id) or "en"
        data["lang"] = lang

        # 2. Get the server registry passed from main.py
        registry = data.get("registry")
        if not registry:
            return await handler(event, data)

        # 3. Check for single-server shortcut
        if registry.is_single_server():
            default_sid = registry.default_server_id()
            server = registry.get(default_sid)
            data["server"] = server
            return await handler(event, data)

        # 4. Exclude certain actions from active server redirection
        is_bypass_action = False
        if isinstance(event, Message) and event.text:
            text = event.text.strip()
            is_bypass_action = (
                text.startswith("/switch") or 
                text.startswith("/start") or 
                text.startswith("/lang") or 
                text.startswith("/help") or
                text.startswith("/servers")
            )
        elif isinstance(event, CallbackQuery) and event.data:
            cdata = event.data
            is_bypass_action = (
                cdata.startswith("select_server_") or 
                cdata.startswith("setlang_") or 
                cdata.startswith("menu_picker")
            )

        if is_bypass_action:
            return await handler(event, data)

        # 5. Resolve active server
        active_server_id = get_last_server(user.id)
        server = registry.get(active_server_id) if active_server_id else None

        if not server:
            # Prompt the user to select an active server
            servers_list = registry.list_all()
            statuses = await registry.status_all()
            servers_with_status = [(sid, name, statuses.get(sid, False)) for sid, name in servers_list]
            
            kb = server_picker_kb(servers_with_status, lang)
            
            if isinstance(event, Message):
                await event.answer(t(lang, "no_server_selected"), reply_markup=kb, parse_mode="Markdown")
            elif isinstance(event, CallbackQuery):
                await event.message.answer(t(lang, "no_server_selected"), reply_markup=kb, parse_mode="Markdown")
                await event.answer()
            return

        # 6. Inject the resolved ServerManager instance
        data["server"] = server
        return await handler(event, data)
