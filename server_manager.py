import asyncio
from mcrcon import MCRcon
import config
import logging

class ServerManager:
    @staticmethod
    async def run_command(command: str) -> str:
        """Отправляет команду на сервер через RCON"""
        try:
            # mcrcon вызывает signal внутри, что падает в asyncio.to_thread
            # Поэтому выполняем синхронно в основном потоке (блокировка на миллисекунды не страшна)
            with MCRcon(config.RCON_HOST, config.RCON_PASSWORD, config.RCON_PORT) as mcr:
                response = mcr.command(command)
                return response if response else "Команда отправлена (нет вывода)"
        except Exception as e:
            logging.error(f"Ошибка RCON: {e}")
            return f"❌ Ошибка RCON (сервер выключен или не настроен?): {e}"

    @staticmethod
    async def is_rcon_alive() -> bool:
        """Проверяет доступность RCON порта (что сервер полностью загрузился)"""
        def _check():
            import socket
            try:
                # Простейшая проверка открыт ли порт (занимает миллисекунды)
                with socket.create_connection((config.RCON_HOST, config.RCON_PORT), timeout=2):
                    return True
            except Exception:
                return False
        return await asyncio.to_thread(_check)

    @staticmethod
    async def is_running() -> bool:
        """Проверяет, запущен ли сервер (жива ли screen сессия)"""
        process = await asyncio.create_subprocess_shell(
            f"screen -list | grep -q '\\.{config.SCREEN_SESSION_NAME}\\b'",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        await process.communicate()
        return process.returncode == 0

    @staticmethod
    async def start_server() -> bool:
        """Запускает сервер в фоне через screen"""
        if await ServerManager.is_running():
            return False  # Уже запущен
            
        cmd = f"cd {config.SERVER_PATH} && screen -dmS {config.SCREEN_SESSION_NAME} ./start.sh"
        process = await asyncio.create_subprocess_shell(cmd)
        await process.communicate()
        return process.returncode == 0

    @staticmethod
    async def stop_server() -> str:
        """Останавливает сервер штатно через RCON"""
        if not await ServerManager.is_running():
            return "❌ Сервер и так выключен."
            
        response = await ServerManager.run_command("stop")
        return f"Отправлена команда остановки... Ответ: {response}"

    @staticmethod
    async def get_logs(lines: int = 20) -> str:
        """Возвращает последние строчки лога"""
        log_path = f"{config.SERVER_PATH}/logs/latest.log"
        try:
            process = await asyncio.create_subprocess_shell(
                f"tail -n {lines} {log_path}",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, _ = await process.communicate()
            return stdout.decode('utf-8')[-4000:] # Защита от лимитов Telegram (4096 символов)
        except Exception as e:
            return f"❌ Ошибка чтения логов: {e}"
