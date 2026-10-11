from __future__ import annotations

from typing import Any, Optional, TypeVar

from bafser import IdMixin, JsonOpt, Log, SqlAlchemyBase, Undefined, UserBase
from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, Session, declared_attr, mapped_column, relationship
from typing_extensions import Self

from ..types import Message

T = TypeVar("T", bound="MsgBase")


class MsgBase(SqlAlchemyBase, IdMixin):
    __abstract__ = True

    message_id: Mapped[int] = mapped_column(index=True)
    message_thread_id: Mapped[Optional[int]] = mapped_column(index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
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
            reply_to_id: int | None = None, *_: Any, db_sess: Session | None = None, **kwargs: Any) -> Self:
        db_sess = db_sess if db_sess is not None else creator.db_sess
        msg = cls._new(db_sess, message_id, chat_id, text, message_thread_id, reply_to_id, **kwargs)
        Log.added(msg, creator, db_sess=db_sess)
        return msg

    @classmethod
    def _new(cls, db_sess: Session, message_id: int, chat_id: int, text: str | None,
             message_thread_id: int | None, reply_to_id: int | None, **kwargs: Any) -> Self:
        msg = cls(message_id=message_id, chat_id=chat_id, text=text, message_thread_id=message_thread_id)
        msg.reply_to_id = reply_to_id
        return msg

    @classmethod
    def new_from_data(cls, data: Message, reply_to_id: int | None = None, *,
                      creator: UserBase | None = None, db_sess: Session | None = None) -> Self:
        creator = creator if creator is not None else UserBase.current
        return cls.new(creator, data.message_id, data.chat.id, data.text, Undefined.default(data.message_thread_id), reply_to_id, db_sess=db_sess)

    @classmethod
    def get_by_message_id(cls, message_id: int, *, db_sess: Session | None = None) -> Self | None:
        return cls.query(db_sess=db_sess).filter(cls.message_id == message_id).first()

    @classmethod
    def all_by_chat_id(cls, chat_id: int, message_thread_id: JsonOpt[int | None] = Undefined, *, db_sess: Session | None = None) -> list[Self]:
        query = cls.query(db_sess=db_sess).filter(cls.chat_id == chat_id)
        if Undefined.defined(message_thread_id):
            query = query.filter(cls.message_thread_id == message_thread_id)
        return query.all()

    def delete(self, *, actor: UserBase | None = None, commit: bool = True, db_sess: Session | None = None):
        actor = actor if actor is not None else UserBase.current
        db_sess = db_sess if db_sess is not None else actor.db_sess
        db_sess.delete(self)
        Log.deleted(self, actor, commit=commit, db_sess=db_sess)
