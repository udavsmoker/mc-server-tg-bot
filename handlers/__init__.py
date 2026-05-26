from aiogram import Router
from .menu import router as menu_router
from .switch import router as switch_router
from .server_actions import router as actions_router
from .world import router as world_router
from .rcon import router as rcon_router

router = Router()
router.include_router(menu_router)
router.include_router(switch_router)
router.include_router(actions_router)
router.include_router(world_router)
router.include_router(rcon_router)
