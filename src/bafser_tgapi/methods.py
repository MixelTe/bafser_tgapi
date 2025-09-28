from typing import List, Union

from .types import *
from .utils import call


# https://core.telegram.org/bots/api#getupdates
def getUpdates(offset: int = 0, timeout: int = 0):
    ok, r = call("getUpdates", {"offset": offset, "timeout": timeout}, timeout=timeout + 5)
    if not ok:
        return False, r
    return True, list(map(lambda x: Update.new(x).valid(), r["result"]))


# https://core.telegram.org/bots/api#getwebhookinfo
def getWebhookInfo():
    ok, r = call("getWebhookInfo")
    if not ok:
        return False, r
    return True, WebhookInfo.new(r["result"]).valid()


# https://core.telegram.org/bots/api#setwebhook
def setWebhook(url: str, secret_token: str | None = None, allowed_updates: list[str] | None = None):
    return call("setWebhook", {"url": url, "secret_token": secret_token, "allowed_updates": allowed_updates})


# https://core.telegram.org/bots/api#deletewebhook
def deleteWebhook(drop_pending_updates: bool | None = None):
    return call("deleteWebhook", {"drop_pending_updates": drop_pending_updates})


# https://core.telegram.org/bots/api#sendmessage
def sendMessage(chat_id: str | int, text: str, message_thread_id: int | None = None, use_markdown: bool = False,
                reply_markup: InlineKeyboardMarkup | None = None, reply_parameters: ReplyParameters | None = None,
                entities: List[MessageEntity] | None = None):
    ok, r = call("sendMessage", {
        "chat_id": chat_id,
        "message_thread_id": message_thread_id,
        "text": text,
        "parse_mode": "MarkdownV2" if use_markdown else None,
        "reply_markup": reply_markup,
        "reply_parameters": reply_parameters,
        "entities": entities,
    })
    if not ok:
        return False, r
    return True, Message.new(r["result"]).valid()


# https://core.telegram.org/bots/api#editmessagetext
def editMessageText(chat_id: Union[int, str], message_id: int, text: str, use_markdown: bool = False,
                    reply_markup: InlineKeyboardMarkup | None = None, entities: List[MessageEntity] | None = None):
    ok, r = call("editMessageText", {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "MarkdownV2" if use_markdown else None,
        "reply_markup": reply_markup,
        "entities": entities,
    })
    if not ok:
        return False, r
    return True, Message.new(r["result"]).valid()


# https://core.telegram.org/bots/api#editmessagetext
def editMessageText_inline(inline_message_id: str, text: str, use_markdown: bool = False, reply_markup: InlineKeyboardMarkup | None = None):
    ok, r = call("editMessageText", {
        "inline_message_id": inline_message_id,
        "text": text,
        "parse_mode": "MarkdownV2" if use_markdown else None,
        "reply_markup": reply_markup,
    })
    if not ok:
        return False, r
    return True, Message.new(r["result"]).valid()


# https://core.telegram.org/bots/api#editmessagereplymarkup
def editMessageReplyMarkup(chat_id: Union[int, str], message_id: int, reply_markup: InlineKeyboardMarkup):
    ok, r = call("editMessageReplyMarkup", {
        "chat_id": chat_id,
        "message_id": message_id,
        "reply_markup": reply_markup,
    })
    if not ok:
        return False, r
    return True, Message.new(r["result"]).valid()


# https://core.telegram.org/bots/api#editmessagereplymarkup
def editMessageReplyMarkup_inline(inline_message_id: str, reply_markup: InlineKeyboardMarkup):
    ok, r = call("editMessageReplyMarkup", {
        "inline_message_id": inline_message_id,
        "reply_markup": reply_markup,
    })
    if not ok:
        return False, r
    return True, Message.new(r["result"]).valid()


# https://core.telegram.org/bots/api#deletemessage
def deleteMessage(chat_id: Union[int, str], message_id: int):
    ok, r = call("deleteMessage", {
        "chat_id": chat_id,
        "message_id": message_id,
    })
    if not ok:
        return False, r
    return True, r["result"]


# https://core.telegram.org/bots/api#answerinlinequery
def answerInlineQuery(
    inline_query_id: str,
    results: list[InlineQueryResult],
    cache_time: int = 300,
    is_personal: bool = False,
    next_offset: str | None = None,
    # button: InlineQueryResultsButton = None,
):
    ok, r = call("answerInlineQuery", {
        "inline_query_id": inline_query_id,
        "results": results,
        "cache_time": cache_time,
        "is_personal": is_personal,
        "next_offset": next_offset,
    })
    if not ok:
        return False, r
    return True, r["result"]


# https://core.telegram.org/bots/api#answercallbackquery
def answerCallbackQuery(
    callback_query_id: str,
    text: str | None = None,
    show_alert: bool = False,
    url: str | None = None,
    cache_time: int = 0,
):
    ok, r = call("answerCallbackQuery", {
        "callback_query_id": callback_query_id,
        "text": text,
        "show_alert": show_alert,
        "url": url,
        "cache_time": cache_time,
    })
    if not ok:
        return False, r
    return True, r["result"]


# https://core.telegram.org/bots/api#setmycommands
def setMyCommands(commands: list[BotCommand], scope: BotCommandScope | None = None, language_code: str | None = None):
    ok, r = call("setMyCommands", {
        "commands": commands,
        "scope": scope,
        "language_code": language_code,
    })
    if not ok:
        return False, r
    return True, r["result"]


# https://core.telegram.org/bots/api#getchatmember
def getChatMember(chat_id: Union[str, int], user_id: int):
    ok, r = call("getChatMember", {
        "chat_id": chat_id,
        "user_id": user_id,
    })
    if not ok:
        return False, r
    return True, ChatMember.new(r["result"]).valid()


# https://core.telegram.org/bots/api#pinchatmessage
def pinChatMessage(chat_id: Union[str, int], message_id: int, disable_notification: bool = True):
    ok, r = call("pinChatMessage", {
        "chat_id": chat_id,
        "message_id": message_id,
        "disable_notification": disable_notification,
    })
    if not ok:
        return False, r
    return True, r["result"]


type ChatAction = Literal["typing", "upload_photo", "record_video", "upload_video", "record_voice",
                          "upload_voice", "upload_document", "choose_sticker", "find_location", "record_video_note", "upload_video_note"]


# https://core.telegram.org/bots/api#sendchataction
def sendChatAction(chat_id: Union[str, int], message_thread_id: int | None, action: ChatAction):
    ok, r = call("sendChatAction", {
        "chat_id": chat_id,
        "message_thread_id": message_thread_id,
        "action": action,
    })
    if not ok:
        return False, r
    return True, r["result"]


type ReactionTypeEmoji = Literal[
    "❤", "👍", "👎", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱", "🤬", "😢", "🎉", "🤩", "🤮", "💩",
    "🙏", "👌", "🕊", "🤡", "🥱", "🥴", "😍", "🐳", "❤‍🔥", "🌚", "🌭", "💯", "🤣", "⚡", "🍌", "🏆",
    "💔", "🤨", "😐", "🍓", "🍾", "💋", "🖕", "😈", "😴", "😭", "🤓", "👻", "👨‍💻", "👀", "🎃", "🙈",
    "😇", "😨", "🤝", "✍", "🤗", "🫡", "🎅", "🎄", "☃", "💅", "🤪", "🗿", "🆒", "💘", "🙉", "🦄", "😘",
    "💊", "🙊", "😎", "👾", "🤷‍♂", "🤷", "🤷‍♀", "😡"
]


# https://core.telegram.org/bots/api#setmessagereaction
def setMessageReaction(chat_id: Union[str, int], message_id: int, reaction: list[ReactionTypeEmoji], is_big: bool | None = None):
    ok, r = call("setMessageReaction", {
        "chat_id": chat_id,
        "message_id": message_id,
        "reaction": [{"type": "emoji", "emoji": v} for v in reaction],
        "is_big": is_big,
    })
    if not ok:
        return False, r
    return True, r["result"]


# https://core.telegram.org/bots/api#sendsticker
def sendSticker(chat_id: Union[str, int], message_thread_id: int | None, sticker: str):
    ok, r = call("sendSticker", {
        "chat_id": chat_id,
        "message_thread_id": message_thread_id,
        "sticker": sticker,
    })
    if not ok:
        return False, r
    return True, Message.new(r["result"]).valid()


# https://core.telegram.org/bots/api#sendphoto
def sendPhoto(chat_id: Union[str, int], message_thread_id: int | None, photo: str, caption: str | None = None,
              caption_entities: List[MessageEntity] | None = None, use_markdown: bool = False, show_caption_above_media: bool | None = None,
              has_spoiler: bool | None = None, disable_notification: bool | None = None, protect_content: bool | None = None,
              reply_parameters: ReplyParameters | None = None, reply_markup: InlineKeyboardMarkup | None = None):
    ok, r = call("sendPhoto", {
        "chat_id": chat_id,
        "message_thread_id": message_thread_id,
        "photo": photo,
        "caption": caption,
        "parse_mode": "MarkdownV2" if use_markdown else None,
        "caption_entities": caption_entities,
        "show_caption_above_media": show_caption_above_media,
        "has_spoiler": has_spoiler,
        "disable_notification": disable_notification,
        "protect_content": protect_content,
        "reply_parameters": reply_parameters,
        "reply_markup": reply_markup,
    })
    if not ok:
        return False, r
    return True, Message.new(r["result"]).valid()


# https://core.telegram.org/bots/api#forwardmessage
def forwardMessage(chat_id: Union[str, int], message_thread_id: int | None, from_chat_id: Union[str, int], message_id: int,
                   video_start_timestamp: int | None = None, disable_notification: bool | None = None, protect_content: bool | None = None):
    ok, r = call("forwardMessage", {
        "chat_id": chat_id,
        "message_thread_id": message_thread_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id,
        "video_start_timestamp": video_start_timestamp,
        "disable_notification": disable_notification,
        "protect_content": protect_content,
    })
    if not ok:
        return False, r
    return True, Message.new(r["result"]).valid()


# https://core.telegram.org/bots/api#copymessage
def copyMessage(chat_id: Union[str, int], message_thread_id: int | None, from_chat_id: Union[str, int], message_id: int,
                video_start_timestamp: int | None = None, caption: str | None = None, use_markdown: bool = False,
                caption_entities: List[MessageEntity] | None = None, show_caption_above_media: bool | None = None,
                disable_notification: bool | None = None, protect_content: bool | None = None,
                reply_parameters: ReplyParameters | None = None, reply_markup: InlineKeyboardMarkup | None = None):
    ok, r = call("copyMessage", {
        "chat_id": chat_id,
        "message_thread_id": message_thread_id,
        "from_chat_id": from_chat_id,
        "message_id": message_id,
        "video_start_timestamp": video_start_timestamp,
        "caption": caption,
        "parse_mode": "MarkdownV2" if use_markdown else None,
        "caption_entities": caption_entities,
        "show_caption_above_media": show_caption_above_media,
        "disable_notification": disable_notification,
        "protect_content": protect_content,
        "reply_parameters": reply_parameters,
        "reply_markup": reply_markup,
    })
    if not ok:
        return False, r
    return True, MessageId.new(r["result"]).valid()
