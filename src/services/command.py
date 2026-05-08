from aiogram import Bot
from aiogram.types import (
    BotCommand,
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
)


def get_admin_commands() -> list[BotCommand]:
    return [
        BotCommand(command='fundraiser_create', description='Создать сбор'),
        BotCommand(command='fundraiser_close', description='Закрыть текущий сбор'),
        BotCommand(command='donations_csv', description='Выгрузка взносов CSV'),
    ]


class CommandService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def set_commands_all_private_chats(self, commands: list[BotCommand]) -> None:
        await self.bot.set_my_commands(commands=commands, scope=BotCommandScopeAllPrivateChats())

    async def set_commands_for_admins(
        self, *, admin_ids: list[int], commands: list[BotCommand]
    ) -> None:
        for admin_id in admin_ids:
            await self.bot.set_my_commands(
                commands=commands, scope=BotCommandScopeChat(chat_id=admin_id)
            )

    async def delete_commands_all_private_chats(self) -> None:
        await self.bot.delete_my_commands(scope=BotCommandScopeAllPrivateChats())

    async def delete_commands_for_admins(self, admin_ids: list[int]) -> None:
        for admin_id in admin_ids:
            await self.bot.delete_my_commands(scope=BotCommandScopeChat(chat_id=admin_id))
