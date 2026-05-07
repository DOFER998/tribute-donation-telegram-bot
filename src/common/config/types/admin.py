from .base import BaseTypeConfig


class AdminTypeConfig(BaseTypeConfig):
    ids: list[int]

    @property
    def admin_ids(self) -> list[int]:
        return self.ids
