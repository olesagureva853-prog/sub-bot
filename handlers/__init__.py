from aiogram import Router
from .start import router as start_router
from .add_sub import router as add_sub_router
from .list_subs import router as list_subs_router
from .stats import router as stats_router
from .admin import router as admin_router

def setup_routers() -> Router:
    main_router = Router()
    main_router.include_router(start_router)
    main_router.include_router(add_sub_router)
    main_router.include_router(list_subs_router)
    main_router.include_router(stats_router)
    main_router.include_router(admin_router)
    return main_router
