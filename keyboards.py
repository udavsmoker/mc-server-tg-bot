from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Tuple
from locales import t

def lang_selection_kb() -> InlineKeyboardMarkup:
    """Keyboard for language selection"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Русский", callback_data="setlang_ru"),
            InlineKeyboardButton(text="English", callback_data="setlang_en")
        ]
    ])

def main_menu_kb(is_running: bool, lang: str = "en", is_single_server: bool = False) -> InlineKeyboardMarkup:
    """Main bot menu, adapts to server status and multi-server config"""
    
    status_btn = (
        InlineKeyboardButton(text=t(lang, "btn_stop"), callback_data="action_stop")
        if is_running else
        InlineKeyboardButton(text=t(lang, "btn_start"), callback_data="action_start")
    )

    inline_keyboard = [
        [status_btn],
        [
            InlineKeyboardButton(text=t(lang, "btn_restart"), callback_data="action_restart"),
            InlineKeyboardButton(text=t(lang, "btn_status"), callback_data="action_status")
        ],
        [InlineKeyboardButton(text=t(lang, "btn_players"), callback_data="action_players")],
        [InlineKeyboardButton(text=t(lang, "btn_world"), callback_data="menu_world")],
        [InlineKeyboardButton(text=t(lang, "btn_logs"), callback_data="action_logs")],
        [InlineKeyboardButton(text=t(lang, "btn_custom_cmd"), callback_data="action_custom_cmd")]
    ]

    # Add Switch Server button if managing multiple servers
    if not is_single_server:
        inline_keyboard.append([InlineKeyboardButton(text=t(lang, "btn_switch"), callback_data="menu_picker")])

    return InlineKeyboardMarkup(inline_keyboard=inline_keyboard)

def world_menu_kb(lang: str = "en") -> InlineKeyboardMarkup:
    """Submenu: Weather and Time"""
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t(lang, "btn_day"), callback_data="cmd_time_set_day"),
            InlineKeyboardButton(text=t(lang, "btn_night"), callback_data="cmd_time_set_night")
        ],
        [
            InlineKeyboardButton(text=t(lang, "btn_clear"), callback_data="cmd_minecraft:weather_clear"),
            InlineKeyboardButton(text=t(lang, "btn_rain"), callback_data="cmd_minecraft:weather_rain"),
            InlineKeyboardButton(text=t(lang, "btn_thunder"), callback_data="cmd_minecraft:weather_thunder")
        ],
        [InlineKeyboardButton(text=t(lang, "btn_back"), callback_data="menu_main")]
    ])
    return kb

def cancel_kb(lang: str = "en") -> InlineKeyboardMarkup:
    """Cancel button for custom command input"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_cancel"), callback_data="menu_main")]
    ])

def server_picker_kb(servers_with_status: List[Tuple[str, str, bool]], lang: str = "en") -> InlineKeyboardMarkup:
    """Keyboard for selecting active server with live status indicators"""
    buttons = []
    for sid, display_name, is_running in servers_with_status:
        status_indicator = " 🟢" if is_running else " 🔴"
        buttons.append([
            InlineKeyboardButton(
                text=f"{display_name}{status_indicator}",
                callback_data=f"select_server_{sid}"
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
