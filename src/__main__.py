from alembic import command
from alembic.config import Config

from src.main import main

if __name__ == '__main__':
    command.upgrade(Config('alembic.ini'), 'head')
    main()
