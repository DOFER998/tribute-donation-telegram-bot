from aiogram import Router

from . import export, fundraiser


def get_admin_router() -> Router:
    router = Router(name='admin')
    router.include_router(fundraiser.router)
    router.include_router(export.router)
    return router
