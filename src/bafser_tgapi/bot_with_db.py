from functools import wraps
from typing import Any, Type, TypeVar

from bafser import Log, db_session
from sqlalchemy.orm import Session

from .bot import Bot, BotCmdArgs
from .db.user import TgUserBase
from .types import User

T = TypeVar("T", bound="BotWithDB[Any]", covariant=True)


class BotWithDB[TUser: TgUserBase](Bot):
    _userCls: Type[TUser]
    db_sess: Session | None = None
    user: TUser | None = None

    def get_user(self, db_sess: Session, sender: User) -> TUser:
        user = self._userCls.get_by_id_tg(db_sess, sender.id)
        if user is None:
            user = self._userCls.new_from_data(db_sess, sender)
        if user.username != sender.username:
            old_username = user.username
            user.username = sender.username
            Log.updated(user, user, [("username", old_username, user.username)])
        return user

    @classmethod
    def cmd_connect_db(cls: Type[T], fn: Bot.tcmd_fn[T]):
        @wraps(fn)
        def wrapped(bot: T, args: BotCmdArgs, **kwargs: str):
            assert bot.sender
            with db_session.create_session() as db_sess:
                bot.db_sess = db_sess
                bot.user = bot.get_user(db_sess, bot.sender)
                return fn(bot, args, **kwargs)
        return wrapped

    @classmethod
    def connect_db(cls: Type[T], fn: Bot.tcallback[T]):
        @wraps(fn)
        def wrapped(bot: T):
            assert bot.sender
            with db_session.create_session() as db_sess:
                bot.db_sess = db_sess
                bot.user = bot.get_user(db_sess, bot.sender)
                return fn(bot)
        return wrapped
