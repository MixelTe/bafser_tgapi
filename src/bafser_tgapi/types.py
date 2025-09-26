from datetime import datetime
from typing import Any, Literal, Union, override

from bafser import JsonObj, JsonOpt, Undefined


class WebhookInfo(JsonObj):
    # https://core.telegram.org/bots/api#webhookinfo
    url: str


class User(JsonObj):
    # https://core.telegram.org/bots/api#user
    id: int
    is_bot: bool
    first_name: str
    last_name: str = ""
    username: str = ""
    language_code: str = ""


class Chat(JsonObj):
    # https://core.telegram.org/bots/api#chat
    id: int
    type: Literal["private", "group", "supergroup", "channel"]
    title: str = ""
    is_forum: bool = False


class MessageEntity(JsonObj):
    class _User(JsonObj):
        id: int

    Type = Literal["mention", "hashtag", "cashtag", "bot_command", "url", "email", "phone_number", "bold", "italic", "underline",
                   "strikethrough", "spoiler", "blockquote", "expandable_blockquote", "code", "pre", "text_link", "text_mention", "custom_emoji"]
    # https://core.telegram.org/bots/api#messageentity
    type: Type
    offset: int
    length: int
    url: JsonOpt[str] = Undefined
    user: JsonOpt[_User] = Undefined
    language: JsonOpt[str] = Undefined
    custom_emoji_id: JsonOpt[str] = Undefined

    @staticmethod
    def text_mention(offset: int, length: int, user_id: int):
        return MessageEntity(type="text_mention", offset=offset, length=length, user=MessageEntity._User(id=user_id))

    @staticmethod
    def blockquote(offset: int, length: int):
        return MessageEntity(type="blockquote", offset=offset, length=length)

    @staticmethod
    def spoiler(offset: int, length: int):
        return MessageEntity(type="spoiler", offset=offset, length=length)

    @staticmethod
    def bold(offset: int, length: int):
        return MessageEntity(type="bold", offset=offset, length=length)

    @staticmethod
    def italic(offset: int, length: int):
        return MessageEntity(type="italic", offset=offset, length=length)

    @staticmethod
    def underline(offset: int, length: int):
        return MessageEntity(type="underline", offset=offset, length=length)

    @staticmethod
    def len(text: str):
        return len(MessageEntity.encode_text(text)) // 2

    @staticmethod
    def encode_text(text: str):
        return text.encode("utf-16-le")

    @staticmethod
    def decode_text(text: bytes):
        return text.decode("utf-16-le")

    def get_msg_text(self, msg: str):
        text = MessageEntity.encode_text(msg)
        s = self.offset * 2 - 2
        e = s + self.length * 2
        return MessageEntity.decode_text(text[s:e])


class Message(JsonObj):
    # https://core.telegram.org/bots/api#message
    __datetime_parser__ = datetime.fromtimestamp
    message_id: int
    message_thread_id: JsonOpt[int]
    sender: JsonOpt[User]
    chat: Chat
    reply_to_message: JsonOpt["Message"]
    is_topic_message: bool = False
    text: str = ""
    date: datetime
    entities: list[MessageEntity] = []

    @override
    def _parse(self, key: str, v: Any, json: dict[str, Any]):
        if key == "from":
            return "sender", v


class InaccessibleMessage(JsonObj):
    # https://core.telegram.org/bots/api#inaccessiblemessage
    __datetime_parser__ = datetime.fromtimestamp
    message_id: int
    chat: Chat
    date: datetime
    message_thread_id = Undefined


class InlineQuery(JsonObj):
    # https://core.telegram.org/bots/api#inlinequery
    id: str
    sender: User
    query: str
    offset: str
    chat_type: JsonOpt[Literal["sender", "private", "group", "supergroup", "channel"]]

    @override
    def _parse(self, key: str, v: Any, json: dict[str, Any]):
        if key == "from":
            return "sender", v


type MaybeInaccessibleMessage = Message | InaccessibleMessage


class CallbackQuery(JsonObj):
    # https://core.telegram.org/bots/api#callbackquery
    id: str
    sender: User
    message: JsonOpt[MaybeInaccessibleMessage]
    inline_message_id: JsonOpt[str]
    chat_instance: str
    data: JsonOpt[str]
    game_short_name: JsonOpt[str]

    @override
    def _parse(self, key: str, v: Any, json: dict[str, Any]):
        if key == "from":
            return "sender", v


class ChosenInlineResult(JsonObj):
    # https://core.telegram.org/bots/api#choseninlineresult
    result_id: str
    sender: User
    # location: Location
    inline_message_id: JsonOpt[str]
    query: str

    @override
    def _parse(self, key: str, v: Any, json: dict[str, Any]):
        if key == "from":
            return "sender", v


class Update(JsonObj):
    # https://core.telegram.org/bots/api#update
    update_id: int
    message: JsonOpt[Message]
    inline_query: JsonOpt[InlineQuery]
    callback_query: JsonOpt[CallbackQuery]
    chosen_inline_result: JsonOpt[ChosenInlineResult]


class InputTextMessageContent(JsonObj):
    # https://core.telegram.org/bots/api#inputtextmessagecontent
    message_text: str
    parse_mode: JsonOpt[Literal["MarkdownV2", "HTML", "Markdown"]] = Undefined
    entities: JsonOpt[list[MessageEntity]] = Undefined
    # link_preview_options: LinkPreviewOptions

    @staticmethod
    def nw(message_text: str, use_markdown: bool = False):
        return InputTextMessageContent(
            message_text=message_text,
            parse_mode="MarkdownV2" if use_markdown else Undefined
        )


type InputMessageContent = InputTextMessageContent


class CallbackGame(JsonObj):
    # https://core.telegram.org/bots/api#callbackgame
    pass


class CopyTextButton(JsonObj):
    # https://core.telegram.org/bots/api#copytextbutton
    text: str


class InlineKeyboardButton(JsonObj):
    # https://core.telegram.org/bots/api#inlinekeyboardbutton
    text: str
    url: JsonOpt[str] = Undefined
    callback_data: JsonOpt[str] = Undefined
    # web_app: WebAppInfo
    # login_url: LoginUrl
    switch_inline_query: JsonOpt[str] = Undefined
    switch_inline_query_current_chat: JsonOpt[str] = Undefined
    # switch_inline_query_chosen_chat: SwitchInlineQueryChosenChat
    copy_text: JsonOpt[CopyTextButton] = Undefined
    callback_game: JsonOpt[CallbackGame] = Undefined
    # pay: bool

    @staticmethod
    def callback(text: str, callback_data: str):
        return InlineKeyboardButton(text=text, callback_data=callback_data)

    @staticmethod
    def inline_query_current_chat(text: str, query: str):
        return InlineKeyboardButton(text=text, switch_inline_query_current_chat=query)

    @staticmethod
    def run_game(text: str):
        return InlineKeyboardButton(text=text, callback_game=CallbackGame())

    @staticmethod
    def open_url(text: str, url: str):
        return InlineKeyboardButton(text=text, url=url)


class InlineKeyboardMarkup(JsonObj):
    # https://core.telegram.org/bots/api#inlinekeyboardmarkup
    inline_keyboard: list[list[InlineKeyboardButton]]


class InlineQueryResult:
    # https://core.telegram.org/bots/api#inlinequeryresult
    pass


class InlineQueryResultArticle(JsonObj, InlineQueryResult):
    # https://core.telegram.org/bots/api#inlinequeryresultarticle
    type: Literal["article"] = JsonObj.field(default="article", init=False)
    id: str
    title: str
    input_message_content: InputMessageContent
    reply_markup: JsonOpt[InlineKeyboardMarkup] = Undefined
    url: JsonOpt[str] = Undefined
    description: JsonOpt[str] = Undefined
    thumbnail_url: JsonOpt[str] = Undefined
    thumbnail_width: JsonOpt[int] = Undefined
    thumbnail_height: JsonOpt[int] = Undefined


class InlineQueryResultGame(JsonObj, InlineQueryResult):
    # https://core.telegram.org/bots/api#inlinequeryresultgame
    type: Literal["game"] = JsonObj.field(default="game", init=False)
    id: str
    game_short_name: str
    reply_markup: JsonOpt[InlineKeyboardMarkup] = Undefined


class BotCommand(JsonObj):
    # https://core.telegram.org/bots/api#botcommand
    command: str  # 1-32 characters. Can contain only lowercase English letters, digits and underscores.
    description: str  # 1-256 characters.


class ChatMember(JsonObj):
    # https://core.telegram.org/bots/api#chatmember
    status: Literal["creator", "administrator", "member", "restricted", "left", "kicked"]
    user: User


BotCommandScopeType = Literal["default", "all_private_chats", "all_group_chats",
                              "all_chat_administrators", "chat", "chat_administrators", "chat_member"]


class BotCommandScope(JsonObj):
    # https://core.telegram.org/bots/api#botcommandscope
    type: BotCommandScopeType
    chat_id: JsonOpt[Union[str, int]] = Undefined
    user_id: JsonOpt[int] = Undefined

    @staticmethod
    def default():
        return BotCommandScope(type="default")

    @staticmethod
    def all_private_chats():
        return BotCommandScope(type="all_private_chats")

    @staticmethod
    def all_group_chats():
        return BotCommandScope(type="all_group_chats")

    @staticmethod
    def all_chat_administrators():
        return BotCommandScope(type="all_chat_administrators")

    @staticmethod
    def chat(chat_id: Union[str, int]):
        return BotCommandScope(type="chat", chat_id=chat_id)

    @staticmethod
    def chat_administrators(chat_id: Union[str, int]):
        return BotCommandScope(type="chat_administrators", chat_id=chat_id)

    @staticmethod
    def chat_member(chat_id: Union[str, int], user_id: int):
        return BotCommandScope(type="chat_member", chat_id=chat_id, user_id=user_id)


class ReplyParameters(JsonObj):
    # https://core.telegram.org/bots/api#replyparameters
    message_id: int
