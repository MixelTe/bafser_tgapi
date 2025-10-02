from __future__ import annotations

from typing import Any, Optional

from bafser import IdMixin, Log, SqlAlchemyBase, Undefined, UserBase
from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, Session, mapped_column

from ..types import Message


class MsgBase(SqlAlchemyBase, IdMixin):
    __abstract__ = True

    message_id: Mapped[int] = mapped_column()
    message_thread_id: Mapped[Optional[int]] = mapped_column()
    chat_id: Mapped[int] = mapped_column(BigInteger)
    text: Mapped[Optional[str]] = mapped_column(String(512))

    @classmethod
    def new(cls, creator: UserBase, message_id: int, chat_id: int, text: str | None = None, message_thread_id: int | None = None,
            *_: Any, **kwargs: Any):
        db_sess = creator.db_sess
        msg, add_changes = cls._new(db_sess, message_id, chat_id, text, message_thread_id, **kwargs)

        db_sess.add(msg)
        Log.added(msg, creator, add_changes)

        return msg

    @classmethod
    def _new(cls, db_sess: Session, message_id: int, chat_id: int, text: str | None, message_thread_id: int | None, **kwargs: Any):
        user = cls(message_id=message_id, chat_id=chat_id, text=text, message_thread_id=message_thread_id)
        changes = [
            ("message_id", user.message_id),
            ("chat_id", user.chat_id),
            ("text", user.text),
            ("message_thread_id", user.message_thread_id),
        ]
        return user, changes

    @classmethod
    def new_from_data(cls, creator: UserBase, data: Message):
        return cls.new(creator, data.message_id, data.chat.id, data.text, Undefined.default(data.message_thread_id))

    def delete(self, actor: UserBase, commit=True):
        db_sess = self.db_sess
        db_sess.delete(self)
        Log.deleted(self, actor, commit=commit)
