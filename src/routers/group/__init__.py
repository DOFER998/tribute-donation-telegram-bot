from aiogram import Router

from .messages import stats


def get_group_router() -> Router:
    router = Router(name='group')
    router.include_router(stats.router)
    return router
