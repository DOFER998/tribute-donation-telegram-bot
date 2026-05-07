from aiogram import Router

from .messages import start


def get_private_router() -> Router:
    router = Router(name='private')
    router.include_router(start.router)
    return router
