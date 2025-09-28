import importlib
import logging
import os
from typing import TYPE_CHECKING, Any, Type
from urllib.parse import urlparse, urlunparse

import requests
from bafser import JsonObj, Undefined, get_app_config, response_msg
from flask import Flask, g, request
from flask import url_for as flask_url_for

import bafser_config

from .types import Update

if TYPE_CHECKING:
    from .bot import Bot

bot_token = ""
bot_name = ""
webhook_token = ""
url = ""

bot: "Bot | None" = None
webhook_route = "/webhook"


def setup(botCls: Type["Bot"] | None = None, app: Flask | None = None, dev: bool = False):
    """`dev = app.DEV_MODE if app else dev`"""
    global bot_token, bot_name, webhook_token, url, bot
    if app:
        dev = get_app_config().DEV_MODE
    try:
        data = read_config(bafser_config.config_dev_path if dev else bafser_config.config_path)
        bot_token = data["bot_token"]
        bot_name = data["bot_name"]
        webhook_token = data["webhook_token"]
        url = data["url"].strip("/") + "/"
    except Exception as e:
        logging.error(f"Cant read config\n{e}")
        raise e

    if bafser_config.bot_folder:
        def import_dir(path: str):
            import_module = path.replace("/", ".").replace("\\", ".")
            for file in os.listdir(path):
                fpath = os.path.join(path, file)
                if os.path.isdir(fpath):
                    if not file.startswith("__"):
                        import_dir(fpath)
                    continue
                if not file.endswith(".py"):
                    continue
                module = import_module + "." + file[:-3]
                importlib.import_module(module)

        if os.path.exists(bafser_config.bot_folder):
            import_dir(bafser_config.bot_folder)

    if botCls:
        bot = botCls()
        bot.init()

    if app:
        app.post(webhook_route)(webhook)


def read_config(path: str):
    data: dict[str, str] = {}
    with open(path) as f:
        for line in f:
            if "=" not in line:
                continue
            i = line.index("=")
            key, value = line[:i], line[i + 1:]
            data[key.strip().replace(" ", "_")] = value.strip()
    return data


def check_webhook_token(token: str):
    return token == webhook_token


def get_url(path: str):
    while path.startswith("/"):
        path = path[1:]
    return url + path


def get_bot_name():
    return bot_name


def process_update(update: Update):
    if not bot:
        raise Exception("tgapi: cant process update without Bot specified in setup")
    bot._process_update(update)


def run_long_polling():
    from .methods import getUpdates
    print("listening for updates...")
    update_id = -1
    while True:
        ok, updates = getUpdates(update_id + 1, 60)
        if not ok:
            print("Error!", updates)
            break
        for update in updates:
            update_id = max(update_id, update.update_id)
            print(f"Update(update_id={update.update_id}, {", ".join(k for k, v in update.items() if Undefined.default(v) and k != "update_id")})")
            process_update(update)


def webhook():
    token = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if (not check_webhook_token(token)):
        return response_msg("wrong token", 403)

    values, is_json = g.json
    if not is_json:
        return response_msg("body is not json", 415)

    logging.info(f"webhook: {values}")
    process_update(Update.new(values).valid())
    return "ok"


def call(method: str, data: JsonObj | dict[str, Any] | None = None, timeout: int | None = None):
    if timeout is not None and timeout <= 0:
        timeout = None
    json = None
    if isinstance(data, dict):
        json = __item_to_json__(data)
    elif data:
        json = data.json()
    try:
        r = requests.post(f"https://api.telegram.org/bot{bot_token}/{method}", json=json, timeout=timeout)
        if not r.ok:
            logging.error(f"tgapi: {method} [{r.status_code}]\t{json}; {r.content}")
            return False, r.json()
        rj = r.json()
        logging.info(f"tgapi: {method}\t{json} -> {rj}")
        return True, rj
    except Exception as e:
        logging.error(f"tgapi call error\n{e}")
        raise Exception("tgapi call error")


def __item_to_json__(item: Any) -> Any:
    if isinstance(item, dict):
        r = {}
        for field, v in item.items():
            v = __item_to_json__(v)
            if v is not None:
                r[field] = v
        return r
    if isinstance(item, (list, tuple)):
        return [__item_to_json__(v) for v in item if v is not None]
    if isinstance(item, JsonObj):
        return item.json()
    return item


def set_webhook(allowed_updates: list[str] | None = None):
    from .methods import setWebhook
    ok, r = setWebhook(get_url(webhook_route), webhook_token, allowed_updates)
    if not ok:
        raise Exception(f"tgapi: cant set webhook\n{r}")


def configure_webhook(set: bool, allowed_updates: list[str] | None = None, *, config_path: str | None = None):
    global bot_token, bot_name, webhook_token, url
    from .methods import deleteWebhook, setWebhook
    if config_path:
        try:
            config = read_config(config_path)
            bot_token = config["bot_token"]
            bot_name = config["bot_name"]
            webhook_token = config["webhook_token"]
            url = config["url"].strip("/") + "/"
        except Exception as e:
            print(f"Cant read config\n{e}")
            return

    if set:
        ok, r = setWebhook(get_url(webhook_route), webhook_token, allowed_updates)
    else:
        ok, r = deleteWebhook(True)

    print(f"{ok}\n {r}")


def url_for(endpoint: str, *, _anchor: str | None = None, _scheme: str | None = None, **values: Any):
    new_url = flask_url_for(endpoint, _anchor=_anchor, _scheme=_scheme, **values)
    parsed = list(urlparse(new_url))
    parsed_host = list(urlparse(url))
    parsed[0] = parsed_host[0]
    parsed[1] = parsed_host[1]
    return urlunparse(parsed)
