import bafser_tgapi as tgapi
from typing_extensions import assert_type

from bafser_tgapi import (Bot, BotCmdArgs, BotWithDB, MsgBase, TgUserBase, build_msg, call_async, call_async_daemon,
                          check_webhook_token, configure_webhook, get_bot_name, get_url, process_update, raiseBotAnswer,
                          reply_markup, run_long_polling, set_webhook, setup, url_for)
from bafser_tgapi.helpers import MsgBuilder
from bafser_tgapi.types import InlineKeyboardMarkup, MessageEntity

__all__ = [
    "Bot", "BotCmdArgs", "BotWithDB", "MsgBase", "TgUserBase", "build_msg", "reply_markup", "call_async",
    "call_async_daemon", "check_webhook_token", "configure_webhook", "get_bot_name", "get_url", "process_update",
    "raiseBotAnswer", "run_long_polling", "set_webhook", "setup", "url_for",
]


def check_helpers() -> None:
    assert_type(build_msg(), MsgBuilder)
    assert_type(tgapi.build_msg("Hello ").bold("world"), MsgBuilder)
    assert_type(tgapi.build_msg("Hello ").bold("world").build(), tuple[str, list[MessageEntity]])
    assert_type(reply_markup([("Continue", "next")]), InlineKeyboardMarkup)
    assert_type(tgapi.reply_markup([("Continue", "next")]), InlineKeyboardMarkup)
