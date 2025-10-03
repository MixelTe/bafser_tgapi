from .methods import *
from .types import *

type text = str
type cmd = str
ME = MessageEntity


def reply_markup(*btns: list[tuple[text, cmd] | InlineKeyboardButton]):
    return InlineKeyboardMarkup(inline_keyboard=[[
        el if isinstance(el, InlineKeyboardButton) else InlineKeyboardButton.callback(el[0], el[1])
        for el in row
    ] for row in btns])


def build_msg(begining: str = ""):
    return MsgBuilder(begining)


class MsgBuilder:
    _text: str
    _entities: list[MessageEntity] = []

    def __init__(self, text: str = "") -> None:
        self._text = text
        self._entities = []

    def build(self):
        return self._text, self._entities

    def _append(self, type: ME.Type, text: "str | MsgBuilder", *,
                url: JsonOpt[str] = Undefined, user: JsonOpt[ME._User] = Undefined,
                language: JsonOpt[str] = Undefined, custom_emoji_id: JsonOpt[str] = Undefined):
        if isinstance(text, MsgBuilder):
            self._append_builder(text)
            text = text._text
        e = ME(type=type, offset=ME.len(self._text), length=ME.len(text),
               url=url, user=user, language=language, custom_emoji_id=custom_emoji_id)
        self._text += text
        self._entities.append(e)
        return self

    def _append_builder(self, builder: "MsgBuilder"):
        offset = ME.len(self._text)
        for e in builder._entities:
            e.offset += offset
            self._entities.append(e)

    def text(self, text: "str | MsgBuilder"):
        if isinstance(text, MsgBuilder):
            self._append_builder(text)
            text = text._text
        self._text += text
        return self

    def text_mention(self, text: "str | MsgBuilder", user_id: int):
        return self._append("text_mention", text, user=ME._User(id=user_id))

    def blockquote(self, text: "str | MsgBuilder"):
        return self._append("blockquote", text)

    def spoiler(self, text: "str | MsgBuilder"):
        return self._append("spoiler", text)

    def bold(self, text: "str | MsgBuilder"):
        return self._append("bold", text)

    def italic(self, text: "str | MsgBuilder"):
        return self._append("italic", text)

    def underline(self, text: "str | MsgBuilder"):
        return self._append("underline", text)

    def code(self, text: "str | MsgBuilder"):
        return self._append("code", text)

    def text_link(self, text: "str | MsgBuilder", url: str):
        return self._append("text_link", text, url=url)
