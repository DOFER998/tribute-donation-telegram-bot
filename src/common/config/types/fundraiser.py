from .base import BaseTypeConfig


class FundraiserTypeConfig(BaseTypeConfig):
    target: int  # копейки
    title: str = 'Сбор'
