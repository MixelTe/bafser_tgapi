# bafser tgapi


## usage
init project: `bafser init_project`
set webhook: `bafser configure_webhook set`
delete webhook: `bafser configure_webhook delete`

main.py
```py
import sys

import bafser_tgapi as tgapi
from bafser import AppConfig, create_app

from bot.bot import Bot
from scripts.init_db import init_db

app, run = create_app(__name__, AppConfig(DEV_MODE="dev" in sys.argv))
tgapi.setup(botCls=Bot, app=app)

DEVSERVER = "devServer" in sys.argv
if DEVSERVER:
    tgapi.set_webhook()
run(DEVSERVER, init_db)

if not DEVSERVER:
    if __name__ == "__main__":
        tgapi.run_long_polling()
    else:
        tgapi.set_webhook()

```

init_db.py
```py
from bafser import AppConfig
from sqlalchemy.orm import Session

from data.user import Roles, User


def init_db(db_sess: Session, config: AppConfig):
    u = User.new(db_sess, 12345, False, "Admin", "", "username", "en")
    u.add_role(u, Roles.admin)

    db_sess.commit()

```

data.user.py
```py
from bafser_tgapi import TgUserBase

from data import Roles


class User(TgUserBase):
    _default_role = Roles.user

```

data.msg.py
```py
from bafser_tgapi import MsgBase

from data import Tables


class Msg(MsgBase):
    __tablename__ = Tables.Msg

```

bot.py
```py
import bafser_tgapi as tgapi

from data.user import User


class Bot(tgapi.BotWithDB[User]):
    _userCls = User

```


## call other method
```py
import json

import bafser_tgapi as tgapi

ok, r = tgapi.call("getStickerSet", {
    "name": "AnimatedEmojies",
})
with open("r.json", "w") as f:
    json.dump(r, f)

```