from __future__ import annotations

from typing import Any, Optional, TypeVar

from bafser import IdMixin, JsonOpt, Log, SqlAlchemyBase, Undefined, UserBase, get_db_session
from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, Session, declared_attr, mapped_column, relationship

from ..types import Message

T = TypeVar("T", bound="MsgBase")


class MsgBase(SqlAlchemyBase, IdMixin):
    __abstract__ = True

    message_id: Mapped[int] = mapped_column()
    message_thread_id: Mapped[Optional[int]] = mapped_column()
    chat_id: Mapped[int] = mapped_column(BigInteger)
    text: Mapped[Optional[str]] = mapped_column(String(512))

    @declared_attr
    def reply_to_id(cls) -> Mapped[Optional[int]]:
        return mapped_column(ForeignKey(f"{cls.__tablename__}.id"), default=None)

    @declared_attr
    def reply_to(cls: T) -> Mapped[Optional[T]]:
        return relationship(
            cls.__name__,
            remote_side=f"{cls.__name__}.id",
            foreign_keys=f"{cls.__name__}.reply_to_id",
            init=False,
        )

    @classmethod
    def new(cls, creator: UserBase, message_id: int, chat_id: int, text: str | None = None, message_thread_id: int | None = None,
            reply_to_id: int | None = None, *_: Any, **kwargs: Any):
        db_sess = creator.db_sess
        msg, add_changes = cls._new(db_sess, message_id, chat_id, text, message_thread_id, reply_to_id, **kwargs)

        db_sess.add(msg)
        Log.added(msg, creator, add_changes)

        return msg

    @classmethod
    def _new(cls, db_sess: Session, message_id: int, chat_id: int, text: str | None,
             message_thread_id: int | None, reply_to_id: int | None, **kwargs: Any):
        msg = cls(message_id=message_id, chat_id=chat_id, text=text, message_thread_id=message_thread_id)
        msg.reply_to_id = reply_to_id
        changes = [
            ("message_id", msg.message_id),
            ("chat_id", msg.chat_id),
            ("text", msg.text),
            ("message_thread_id", msg.message_thread_id),
        ]
        return msg, changes

    @classmethod
    def new_from_data(cls, creator: UserBase, data: Message, reply_to_id: int | None = None):
        return cls.new(creator, data.message_id, data.chat.id, data.text, Undefined.default(data.message_thread_id), reply_to_id)

    @classmethod
    def new_from_data2(cls, data: Message, reply_to_id: int | None = None):
        """Calls cls.new_from_data with UserBase.current as actor"""
        return cls.new_from_data(UserBase.current, data, reply_to_id)

    @classmethod
    def get_by_message_id(cls, db_sess: Session, message_id: int):
        return cls.query(db_sess).filter(cls.message_id == message_id).first()

    @classmethod
    def get_by_message_id2(cls, message_id: int):
        """Calls cls.get_by_message_id with db session from global context"""
        return cls.get_by_message_id(get_db_session(), message_id)

    @classmethod
    def all_by_chat_id(cls, db_sess: Session, chat_id: int, message_thread_id: JsonOpt[int | None] = Undefined):
        query = cls.query(db_sess).filter(cls.chat_id == chat_id)
        if Undefined.defined(message_thread_id):
            query = query.filter(cls.message_thread_id == message_thread_id)
        return query.all()

    @classmethod
    def all_by_chat_id2(cls, chat_id: int, message_thread_id: JsonOpt[int | None] = Undefined):
        """Calls cls.all_by_chat_id with db session from global context"""
        return cls.all_by_chat_id(get_db_session(), chat_id, message_thread_id)

    def delete(self, actor: UserBase, commit=True):
        db_sess = self.db_sess
        db_sess.delete(self)
        Log.deleted(self, actor, commit=commit)

    def delete2(self, commit=True):
        """Calls self.delete with UserBase.current as actor"""
        self.delete(UserBase.current, commit)
