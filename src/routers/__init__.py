from aiogram import Dispatcher

from .admin import get_admin_router
from .group import get_group_router
from .private import get_private_router


def include_routers(dispatcher: Dispatcher) -> None:
    dispatcher.include_router(get_admin_router())
    dispatcher.include_router(get_private_router())
    dispatcher.include_router(get_group_router())
