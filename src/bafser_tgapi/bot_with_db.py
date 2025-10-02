from typing import Any, Type, TypeVar

from bafser import Log, db_session
from sqlalchemy.orm import Session

from .bot import Bot
from .db.user import TgUserBase
from .types import User

T = TypeVar("T", bound="BotWithDB[Any]", covariant=True)


class BotWithDB[TUser: TgUserBase](Bot):
    _userCls: Type[TUser]
    __db_sess: Session | None = None
    __user: TUser | None = None

    @property
    def db_sess(self) -> Session:
        if not self.__db_sess:
            self._create_session()
        assert self.__db_sess
        return self.__db_sess

    @property
    def user(self) -> TUser:
        if not self.__user:
            self._create_session()
        assert self.__user
        return self.__user

    def get_user(self, db_sess: Session, sender: User) -> TUser:
        user = self._userCls.get_by_id_tg(db_sess, sender.id)
        if user is None:
            user = self._userCls.new_from_data(db_sess, sender)
        if user.username != sender.username:
            old_username = user.username
            user.username = sender.username
            Log.updated(user, user, [("username", old_username, user.username)])
        return user

    def _create_session(self):
        assert self.sender
        self.__db_sess = db_session.create_session()
        self.__user = self.get_user(self.__db_sess, self.sender)

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        if self.__db_sess:
            self.__db_sess.close()
