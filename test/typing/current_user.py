from bafser import UserBase
from sqlalchemy.orm import Session
from typing_extensions import assert_type

from bafser_tgapi import BotCmdArgs, BotWithDB, Message, MsgBase, TgUserBase
from bafser_tgapi import User as TelegramUser


class User(TgUserBase):
    __abstract__ = True


class Bot(BotWithDB[User]):
    _userCls = User


class Msg(MsgBase):
    __abstract__ = True


def check_message(bot: Bot, message: Message) -> None:
    assert_type(UserBase.current, UserBase)
    assert_type(User.current, User)
    assert_type(bot.user, User)
    MsgBase.new_from_data(message, creator=UserBase.current)
    MsgBase.new_from_data(message, creator=User.current)


def check_models(sender: TelegramUser, message: Message, session: Session) -> None:
    assert_type(User.new_from_data(sender), User)
    assert_type(User.new_from_data(sender, db_sess=session), User)
    assert_type(User.new(sender.id, sender.is_bot, sender.first_name, sender.last_name, sender.username, sender.language_code), User)
    assert_type(User.get_by_id_tg(sender.id), User | None)
    assert_type(User.get_by_id_tg(sender.id, db_sess=session, for_update=True), User | None)
    assert_type(User.get_by_username(sender.username, db_sess=session), User | None)
    assert_type(Msg.new_from_data(message), Msg)
    assert_type(Msg.new_from_data(message, creator=User.current, db_sess=session), Msg)
    assert_type(Msg.get_by_message_id(message.message_id, db_sess=session), Msg | None)
    assert_type(Msg.all_by_chat_id(message.chat.id), list[Msg])
    assert_type(Msg.all_by_chat_id(message.chat.id, None, db_sess=session), list[Msg])
    Msg.new_from_data(message).delete()
    Msg.new_from_data(message).delete(False, actor=User.current, db_sess=session)


def on_message(bot: Bot) -> None:
    assert_type(bot.user, User)


def command(bot: Bot, args: BotCmdArgs, **kwargs: str) -> str:
    assert_type(bot.user, User)
    return args.raw_args


Bot.on_message(on_message)
Bot.add_command("example")(command)
