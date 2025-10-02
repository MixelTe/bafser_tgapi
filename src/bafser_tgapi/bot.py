import re
from functools import wraps
from logging import Logger
from typing import Callable, Iterable, Self, Type, TypeVar, cast

from bafser import ParametrizedLogger, add_file_logger
from typing_extensions import Protocol

import bafser_config

from .methods import *
from .types import *
from .utils import call_async, get_bot_name

T = TypeVar("T", bound="Bot")
type tcmd_dsc_text = str
type tcmd_dsc_usage = str
re_param = re.compile("<[a-z]+>", re.IGNORECASE)


class Bot:
    class tcmd_fn[T: "Bot"](Protocol):
        __name__: str

        def __call__(self, bot: T, args: "BotCmdArgs", **kwargs: str) -> str | None:
            ...
    type tcmd_dsc = tcmd_dsc_text | tuple[tcmd_dsc_text, tcmd_dsc_usage | list[tcmd_dsc_usage]]
    type tcallback[T: "Bot"] = Callable[[T], None]
    _tcommand = tuple[tcmd_fn[Self], tuple[tcmd_dsc | None, tcmd_dsc | None]]

    update: Update
    message: Message | None = None
    callback_query: CallbackQuery | None = None
    inline_query: InlineQuery | None = None
    chosen_inline_result: ChosenInlineResult | None = None

    _commands: dict[str, _tcommand] = {}
    _callback: dict[Callable[..., Any], tcallback[Self]] = {}
    _sender: User | None = None
    chat: Chat | None = None
    TextWrongCommand = "Wrong command"
    TextCmdForAdmin = "Эта команда только для админов"
    logger: "BotLogger"
    _logger: Logger

    @property
    def sender(self):
        return self._sender

    @sender.setter
    def sender(self, value: User | None):
        self._sender = value
        self.logger.user = value

    def __init__(self):
        self.logger = BotLogger(self._logger)

    def __enter__(self):
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any):
        pass

    @classmethod
    def init(cls):
        fmt = "%(asctime)s;%(levelname)s;%(module)s;%(uid)-10s;%(uname)-15s;%(cmd)-15s;%(message)s"
        cls._logger = add_file_logger(bafser_config.log_bot_path, "bot", fmt, ["uid", "uname", "cmd"])

        def get_desc(v: Bot.tcmd_dsc):
            return v if isinstance(v, str) else v[0]

        for_all: list[BotCommand] = []
        for_adm: list[BotCommand] = []
        for cmd in cls._commands.keys():
            pub = cls._commands[cmd][1][0]
            adm = cls._commands[cmd][1][1]
            if not adm:
                adm = pub
            cmd = re_param.sub("", cmd)
            if pub:
                for_all.append(BotCommand(command=cmd, description=get_desc(pub)))
            if adm:
                for_adm.append(BotCommand(command=cmd, description=get_desc(adm)))

        call_async(lambda: setMyCommands(for_all))
        call_async(lambda: setMyCommands(for_adm, BotCommandScope.all_chat_administrators()))

    def get_my_commands(self, for_admin: bool = False):
        i = 1 if for_admin else 0
        r: list[tuple[str, Bot.tcmd_dsc]] = []
        for key in self._commands.keys():
            v = self._commands[key][1][i]
            if v:
                r.append((key, v))
        return r

    @classmethod
    def add_command(cls: Type[T], name: str | None = None, *, desc: tcmd_dsc | None = None, desc_adm: tcmd_dsc | None = None):
        def wrapper(fn: Bot.tcmd_fn[T]):
            command = name if name else fn.__name__
            if "<" in command:
                parts: list[tuple[str, bool]] = []
                param = None
                for ch in command:
                    if ch == "<":
                        param = ""
                    elif ch == ">":
                        if param:
                            parts.append((param, True))
                        param = None
                    elif param is not None:
                        param += ch
                    else:
                        if not parts or parts[-1][1]:
                            parts.append(("", False))
                        parts[-1] = (parts[-1][0] + ch, False)
                res = ""
                varnames: list[str] = []
                for part, isvar in parts:
                    if isvar:
                        res += "(.*)"
                        varnames.append(part)
                    else:
                        res += part
                reg = re.compile(res, re.IGNORECASE)
                fn.regex = reg  # type: ignore

                def comparer(cmd: str):
                    regex = cast(re.Pattern[str], fn.regex)  # type: ignore
                    m = regex.match(cmd)
                    if not m or len(m.groups()) != len(varnames):
                        return None
                    return dict(zip(varnames, m.groups()))
                fn.comparer = comparer  # type: ignore

            cls._commands[command] = (fn, (desc, desc_adm))
            return fn
        return wrapper

    @classmethod
    def cmd_for_admin(cls: Type[T], fn: tcmd_fn[T]):
        @wraps(fn)
        def wrapped(bot: T, args: BotCmdArgs, **kwargs: str):
            if bot.chat is None or bot.sender is None:
                return "403(500!)"
            ok, r = getChatMember(bot.chat.id, bot.sender.id)
            if not ok:
                return "403(500)"
            if r.status != "creator" and r.status != "administrator":
                return cls.TextCmdForAdmin
            return fn(bot, args, **kwargs)
        return wrapped

    def _process_update(self, update: Update):
        self.update = update
        self.message = Undefined.default(update.message)
        self.callback_query = Undefined.default(update.callback_query)
        self.inline_query = Undefined.default(update.inline_query)
        self.chosen_inline_result = Undefined.default(update.chosen_inline_result)
        self.sender = None
        self.chat = None
        self.logger._reset()
        if self.message:
            self.sender = Undefined.default(self.message.sender)
            self.chat = self.message.chat
            self._on_message()
        if self.callback_query:
            self.sender = self.callback_query.sender
            self.chat = self.callback_query.message.chat if Undefined.defined(self.callback_query.message) else None
            self._on_callback_query()
        if self.inline_query:
            self.sender = self.inline_query.sender
            self._call_callback(self.on_inline_query)
        if self.chosen_inline_result:
            self.sender = self.chosen_inline_result.sender
            self._call_callback(self.on_chosen_inline_result)

    def _call_callback(self, key: Callable[..., Any]):
        fn = self._callback.get(key)
        if fn:
            fn(self)

    @classmethod
    def on_message(cls: Type[T], fn: tcallback[T]):
        cls._callback[cls.on_message] = fn
        return fn

    @classmethod
    def on_inline_query(cls: Type[T], fn: tcallback[T]):
        cls._callback[cls.on_inline_query] = fn
        return fn

    @classmethod
    def on_chosen_inline_result(cls: Type[T], fn: tcallback[T]):
        cls._callback[cls.on_chosen_inline_result] = fn
        return fn

    def _on_message(self):
        assert self.message
        if self.message.text.startswith("/"):
            r = self._on_command(self.message.text[1:])
            if r:
                if isinstance(r, str):
                    self.sendMessage(r)
            elif r is False and self.message.chat.type == "private":
                self.sendMessage(self.TextWrongCommand)
        else:
            self._call_callback(self.on_message)

    def _on_command(self, input: str):
        args = BotCmdArgs(input)
        if args.command == "":
            return False
        cmd, kwargs = self._find_command(args.command)
        if not cmd:
            return False
        fn, _ = cmd
        self.logger.cmd = args.command
        r = fn(self, args, **kwargs)
        if r:
            return r
        return True

    def _find_command(self, cmd: str) -> tuple[_tcommand | None, dict[str, str]]:
        c = self._commands.get(cmd, None)
        if c:
            return c, {}
        for c in self._commands.values():
            if hasattr(c[0], "comparer"):
                kwargs = cast(dict[str, str] | None, c[0].comparer(cmd))  # type: ignore
                if kwargs:
                    return c, kwargs
        return None, {}

    def _on_callback_query(self):
        assert self.callback_query
        r = self._on_command(Undefined.default(self.callback_query.data, ""))
        if r:
            self.answerCallbackQuery(r if isinstance(r, str) else None)
        else:
            self.answerCallbackQuery(self.TextWrongCommand)

    def get_cur_chat_and_thread_id(self, chat_id: str | int | None = None, message_thread_id: int | None = None):
        if self.message:
            if chat_id is None:
                chat_id = self.message.chat.id
            if message_thread_id is None and self.message.is_topic_message and Undefined.defined(self.message.message_thread_id):
                message_thread_id = self.message.message_thread_id
        elif self.callback_query and Undefined.defined(self.callback_query.message):
            if chat_id is None:
                chat_id = self.callback_query.message.chat.id
            if message_thread_id is None and Undefined.defined(self.callback_query.message.message_thread_id):
                message_thread_id = self.callback_query.message.message_thread_id
        return chat_id, message_thread_id

    def sendMessage(self, text: str, *, message_thread_id: int | None = None, use_markdown: bool = False,
                    reply_markup: InlineKeyboardMarkup | None = None, reply_parameters: ReplyParameters | None = None,
                    entities: List[MessageEntity] | None = None, chat_id: str | int | None = None):
        chat_id, message_thread_id = self.get_cur_chat_and_thread_id(chat_id, message_thread_id)
        if chat_id is None:
            raise Exception("tgapi: cant send message without chat id")
        return sendMessage(chat_id, text, message_thread_id, use_markdown, reply_markup, reply_parameters, entities)

    def sendPhoto(self, photo: str, *, caption: str | None = None, message_thread_id: int | None = None, use_markdown: bool = False,
                  reply_markup: InlineKeyboardMarkup | None = None, reply_parameters: ReplyParameters | None = None,
                  caption_entities: List[MessageEntity] | None = None, chat_id: str | int | None = None,
                  show_caption_above_media: bool | None = None, has_spoiler: bool | None = None,
                  disable_notification: bool | None = None, protect_content: bool | None = None):
        chat_id, message_thread_id = self.get_cur_chat_and_thread_id(chat_id, message_thread_id)
        if chat_id is None:
            raise Exception("tgapi: cant send photo without chat id")
        return sendPhoto(chat_id, message_thread_id, photo, caption, caption_entities, use_markdown,
                         show_caption_above_media, has_spoiler, disable_notification, protect_content,
                         reply_parameters, reply_markup)

    def sendChatAction(self, action: ChatAction, *, message_thread_id: int | None = None, chat_id: str | int | None = None):
        chat_id, message_thread_id = self.get_cur_chat_and_thread_id(chat_id, message_thread_id)
        if chat_id is None:
            raise Exception("tgapi: cant send chat action without chat id")
        return sendChatAction(chat_id, message_thread_id, action)

    def sendSticker(self, sticker: str, *, message_thread_id: int | None = None, chat_id: str | int | None = None):
        chat_id, message_thread_id = self.get_cur_chat_and_thread_id(chat_id, message_thread_id)
        if chat_id is None:
            raise Exception("tgapi: cant send sticker without chat id")
        return sendSticker(chat_id, message_thread_id, sticker)

    def answerCallbackQuery(self, text: str | None = None, *, show_alert: bool = False, url: str | None = None, cache_time: int = 0):
        if self.callback_query is None:
            raise Exception("tgapi: Bot.answerCallbackQuery is avaible only inside on_callback_query")
        return answerCallbackQuery(self.callback_query.id, text, show_alert, url, cache_time)

    def answerInlineQuery(self, results: list[InlineQueryResult], *, cache_time: int = 300,
                          is_personal: bool = False, next_offset: str | None = None):
        if self.inline_query is None:
            raise Exception("tgapi: Bot.answerInlineQuery is avaible only inside on_inline_query")
        return answerInlineQuery(self.inline_query.id, results, cache_time, is_personal, next_offset)


@Bot.on_inline_query
def _(bot: Bot):
    bot.answerInlineQuery([])


class BotLogger(ParametrizedLogger):
    user: User | None = None
    cmd = ""

    def _reset(self):
        self.user = None
        self.cmd = ""

    def _get_args(self) -> dict[str, str | int]:
        return {
            "uid": self.user.id if self.user else -1,
            "uname": self.user.username if self.user else "",
            "cmd": self.cmd
        }


class BotCmdArgs(Iterable[str]):
    input: str
    args: list[str]
    raw_args = ""
    raw_argsI = -1
    command = ""

    def __init__(self, input: str):
        self.input = input
        self.args = [str.strip(v) for v in input.split()]

        if len(self.args) == 0:
            return

        command = self.args[0]
        mention = command.find("@")
        if mention > 0:
            bot_name = command[mention:]
            if bot_name != get_bot_name():
                return
            command = command[:mention]
        self.command = command

        self.args = self.args[1:]

        i = input.find(" ")
        if i > 0:
            while i < len(input) and input[i] == " ":
                i += 1
            self.raw_argsI = MessageEntity.len(input[:i])
            self.raw_args = input[i:]

    def __getitem__(self, i: int):
        return self.args[i]

    def __len__(self):
        return len(self.args)

    def __iter__(self):
        for arg in self.args:
            yield arg
