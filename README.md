# bafser tgapi


## usage
init project: `bafser init_project`
set webhook: `bafser configure_webhook set`
delete webhook: `bafser configure_webhook delete`

main.py
```py
import sys

from bafser import AppConfig, create_app
import bafser_tgapi as tgapi

from bot.bot import Bot
from scripts.init_db import init_db

app, run = create_app(__name__, AppConfig(DEV_MODE="dev" in sys.argv))

tgapi.setup(
    config_path="config_dev.txt" if __name__ == "__main__" else "config.txt",
    botCls=Bot,
    import_folder="bot",
    app=app,
)

run(False, init_db)

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

from data._roles import Roles


class User(TgUserBase):
    _default_role = Roles.user

```

data.msg.py
```py
from bafser_tgapi import MsgBase

from data._tables import Tables


class Msg(MsgBase):
    __tablename__ = Tables.Msg

```

bot.py
```py
from typing import override

from bafser import Log
import bafser_tgapi as tgapi
from sqlalchemy.orm import Session

from data.user import User


class Bot(tgapi.BotWithDB[User]):
    @override
    def get_user(self, db_sess: Session, sender: tgapi.User) -> User:
        user = User.get_by_id_tg(db_sess, sender.id)
        if user is None:
            user = User.new_from_data(db_sess, sender)
        if user.username != sender.username:
            old_username = user.username
            user.username = sender.username
            Log.updated(user, user, [("username", old_username, user.username)])
        return user
```
