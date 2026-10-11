import logging
import unittest
from datetime import datetime
from unittest.mock import patch

from bafser import Log, Role, SqlAlchemyBase, UserBase, UserRole
from flask import Flask, g
from flask_jwt_extended import JWTManager
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from werkzeug.exceptions import HTTPException

from bafser_tgapi import BotCmdArgs, BotWithDB, MsgBase, TgUserBase, Update, User, utils


class DbUser(TgUserBase):
    _default_role = 2


class DbMsg(MsgBase):
    __tablename__ = "Msg"


class DbBot(BotWithDB[DbUser]):
    _userCls = DbUser
    _logger = logging.getLogger("test.bot")


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        self.addCleanup(self.engine.dispose)

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(connection, record):
            connection.execute("PRAGMA foreign_keys=ON")

        SqlAlchemyBase.metadata.create_all(self.engine)
        self.session = Session(self.engine)
        self.addCleanup(self.session.close)
        role = Role(name="User")
        role.id = DbUser._default_role
        self.session.add(role)
        self.session.commit()
        self.sender = User(id=12345, is_bot=False, first_name="Test", username="Example")
        self.user = DbUser.new_from_data(self.sender, db_sess=self.session)
        self.message = Update.new({
            "update_id": 1,
            "message": {"message_id": 10, "date": 0, "chat": {"id": 100, "type": "private"}},
        }).valid().message

    def test_user_creation_saves_role_and_audit_record(self):
        self.assertIsNotNone(UserRole.get(self.session, self.user.id, DbUser._default_role))
        log = self.session.query(Log).filter_by(tableName="User", recordId=self.user.id).one()
        self.assertEqual(log.actionCode, "added")
        self.assertEqual(self.user.id_tg, self.sender.id)

    def test_user_lookups_use_explicit_session_and_include_deleted(self):
        self.user.deleted = True
        self.session.commit()
        for for_update in (False, True):
            with self.subTest(for_update=for_update):
                self.assertIs(DbUser.get_by_id_tg(self.sender.id, for_update=for_update, db_sess=self.session), self.user)
                self.assertIs(DbUser.get_by_username("@EXAMPLE", for_update=for_update, db_sess=self.session), self.user)
        self.assertIsNone(DbUser.get_by_id_tg(-1, db_sess=self.session))
        self.assertIsNone(DbUser.get_by_username("missing", db_sess=self.session))

    def test_message_lookups_filter_chat_and_thread(self):
        first = DbMsg.new(self.user, 10, 100, "First")
        threaded = DbMsg.new(self.user, 11, 100, "Thread", message_thread_id=5, reply_to_id=first.id)
        DbMsg.new(self.user, 12, 200, "Other chat")
        self.assertIs(DbMsg.get_by_message_id(10, db_sess=self.session), first)
        self.assertIsNone(DbMsg.get_by_message_id(-1, db_sess=self.session))
        self.assertEqual(DbMsg.all_by_chat_id(100, db_sess=self.session), [first, threaded])
        self.assertEqual(DbMsg.all_by_chat_id(100, None, db_sess=self.session), [first])
        self.assertEqual(DbMsg.all_by_chat_id(100, 5, db_sess=self.session), [threaded])
        self.assertIs(threaded.reply_to, first)

    def test_bot_context_lookups_and_username_update(self):
        self.sender.username = "Renamed"
        with patch("bafser_tgapi.bot_with_db.db_session.create_session", return_value=self.session), DbBot() as bot:
            bot.sender = self.sender
            with patch.object(utils.thread_local, "bot", bot, create=True):
                self.assertIs(bot.user, self.user)
                self.assertEqual(self.user.username, "Renamed")
                self.assertIs(DbUser.get_by_id_tg(self.sender.id), self.user)
                self.assertIs(DbUser.get_by_username("@RENAMED"), self.user)
                msg = DbMsg.new_from_data(self.message)
                self.assertIs(DbMsg.get_by_message_id(10), msg)
                self.assertEqual(DbMsg.all_by_chat_id(100, None), [msg])
                msg.delete()
                self.assertIsNone(DbMsg.get_by_message_id(10))
        log = self.session.query(Log).filter_by(tableName="User", actionCode="updated").one()
        self.assertIn(["username", "Example", "Renamed"], log.changes)

    def test_request_context_provides_session_and_actor(self):
        with Flask(__name__).test_request_context():
            g.db_session = self.session
            g.user = self.user
            user = DbUser.new(12346, False, "Other", "", "Other", "en")
            sender = User(id=12347, is_bot=False, first_name="New")
            created = DbUser.new_from_data(sender)
            self.assertIs(DbUser.get_by_id_tg(created.id_tg), created)
            self.assertIs(DbUser.get_by_username("@OTHER"), user)
            msg = DbMsg.new_from_data(self.message)
            self.assertIs(DbMsg.get_by_message_id(10), msg)
            self.assertEqual(DbMsg.all_by_chat_id(100), [msg])
            msg.delete()
            self.assertIsNone(DbMsg.get_by_message_id(10))

    def test_bot_creates_missing_user_without_current_user_recursion(self):
        sender = User(id=12346, is_bot=False, first_name="New", username="New")
        with patch("bafser_tgapi.bot_with_db.db_session.create_session", return_value=self.session), DbBot() as bot:
            bot.sender = sender
            with patch.object(utils.thread_local, "bot", bot, create=True):
                created = bot.user
                self.assertEqual(created.id_tg, sender.id)
                self.assertIs(DbUser.get_by_id_tg(sender.id), created)
                self.assertIsNotNone(UserRole.get(self.session, created.id, DbUser._default_role))
                msg = DbMsg.new_from_data(self.message)
                log = self.session.query(Log).filter_by(tableName="Msg", recordId=msg.id, actionCode="added").one()
                self.assertEqual(log.userId, created.id)

    def test_explicit_session_overrides_request_session(self):
        with Session(self.engine) as other_session, Flask(__name__).test_request_context():
            g.db_session = other_session
            g.user = self.user
            self.assertIs(DbUser.get_by_id_tg(self.sender.id, db_sess=self.session), self.user)
            contextual = DbUser.get_by_id_tg(self.sender.id)
            self.assertIsNot(contextual, self.user)
            self.assertIs(Session.object_session(contextual), other_session)

    def test_explicit_message_actor_and_session_work_without_context(self):
        actor = UserBase.get_fake_system()
        with patch.object(UserBase, "get_current", side_effect=AssertionError("unexpected context lookup")):
            msg = DbMsg.new_from_data(self.message, creator=actor, db_sess=self.session)
            msg_id = msg.id
            added = self.session.query(Log).filter_by(tableName="Msg", recordId=msg_id, actionCode="added").one()
            self.assertEqual(added.userName, "System")
            msg.delete(commit=False, actor=actor, db_sess=self.session)
            self.assertIsNone(DbMsg.get_by_message_id(10, db_sess=self.session))
            self.assertEqual(self.session.query(Log).filter_by(tableName="Msg", actionCode="deleted").count(), 1)
            self.session.rollback()
            self.assertIsNotNone(self.session.get(DbMsg, msg_id))
            self.assertEqual(self.session.query(Log).filter_by(tableName="Msg", actionCode="deleted").count(), 0)
            msg.delete(actor=actor, db_sess=self.session)
            self.assertIsNone(DbMsg.get_by_message_id(10, db_sess=self.session))


class CurrentUserTests(unittest.TestCase):
    def setUp(self):
        self.message = Update.new({
            "update_id": 1,
            "message": {"message_id": 10, "date": 0, "chat": {"id": 100, "type": "private"}},
        }).valid().message

    def test_missing_user_outside_request_raises(self):
        with patch.object(UserBase, "get_current", return_value=None):
            with self.assertRaisesRegex(Exception, "No current user"):
                DbMsg.new_from_data(self.message)

    def test_missing_user_in_request_returns_401_and_clears_jwt(self):
        app = Flask(__name__)
        JWTManager(app)
        with app.test_request_context(), patch.object(UserBase, "get_current", return_value=None):
            with self.assertRaises(HTTPException) as caught:
                DbMsg.new_from_data(self.message)
            response = caught.exception.get_response()
            self.assertEqual(response.status_code, 401)
            self.assertEqual(response.get_json(), {"msg": "The JWT has expired"})
            self.assertTrue(any("access_token_cookie=;" in cookie for cookie in response.headers.getlist("Set-Cookie")))


class BotCompatibilityTests(unittest.TestCase):
    def test_command_and_callback_registration(self):
        received = []
        with patch.dict(DbBot._commands, clear=True), patch.dict(DbBot._callback, clear=True), DbBot() as bot:
            @DbBot.add_command("example")
            def command(bot: DbBot, args: BotCmdArgs, **kwargs: str):
                return args.raw_args

            @DbBot.on_message
            def on_message(bot: DbBot):
                received.append(bot)

            self.assertEqual(bot._on_command("example hello"), "hello")
            bot._call_callback(bot.on_message)
            self.assertEqual(received, [bot])


class JsonTests(unittest.TestCase):
    def test_nested_update_parses_sender_dates_and_optional_fields(self):
        update = Update.new({
            "update_id": 1,
            "message": {
                "message_id": 10,
                "date": 0,
                "chat": {"id": 100, "type": "private"},
                "from": {"id": 12345, "is_bot": False, "first_name": "Test"},
                "text": "Hello",
                "entities": [{"type": "bold", "offset": 0, "length": 5}],
                "unknown_field": True,
            },
        }).valid()
        self.assertEqual(update.message.sender.id, 12345)
        self.assertEqual(update.message.sender.username, "")
        self.assertEqual(update.message.date, datetime.fromtimestamp(0))
        self.assertEqual(update.message.entities[0].json(), {"type": "bold", "offset": 0, "length": 5})
        self.assertNotIn("unknown_field", update.message.json())

    def test_callback_query_parses_message_type_alias(self):
        update = Update.new({
            "update_id": 1,
            "callback_query": {
                "id": "callback",
                "from": {"id": 12345, "is_bot": False, "first_name": "Test"},
                "chat_instance": "chat",
                "message": {"message_id": 10, "date": 0, "chat": {"id": 100, "type": "private"}},
                "data": "action",
            },
        }).valid()
        self.assertEqual(update.callback_query.sender.id, 12345)
        self.assertEqual(update.callback_query.message.message_id, 10)


if __name__ == "__main__":
    unittest.main()
