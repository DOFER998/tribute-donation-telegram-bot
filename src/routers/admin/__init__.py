from aiogram import Router

from . import fundraiser


def get_admin_router() -> Router:
    router = Router(name='admin')
    router.include_router(fundraiser.router)
    return router
