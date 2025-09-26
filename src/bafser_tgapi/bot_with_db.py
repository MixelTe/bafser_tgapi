from typing import Any, Type, TypeVar

from bafser import db_session
from sqlalchemy.orm import Session

from .bot import Bot, BotCmdArgs
from .types import User

T = TypeVar("T", bound="BotWithDB[Any]", covariant=True)


class BotWithDB[TUser](Bot):
    db_sess: Session | None = None
    user: TUser | None = None

    def get_user(self, db_sess: Session, sender: User) -> TUser:
        raise Exception("tgapi: Method BotWithDB.get_user must be implemented in subclass")

    @classmethod
    def cmd_connect_db(cls: Type[T], fn: Bot.tcmd_fn[T]):
        def wrapped(bot: T, args: BotCmdArgs, **kwargs: str):
            assert bot.sender
            with db_session.create_session() as db_sess:
                bot.db_sess = db_sess
                bot.user = bot.get_user(db_sess, bot.sender)
                return fn(bot, args, **kwargs)
        return wrapped
