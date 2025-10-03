import os
import webbrowser
from typing import cast

import jinja2
from flask import Flask, render_template

from ..methods import getStickerSet
from ..utils import setup


def stickers():
    setup(dev=True)
    loc = os.path.abspath(os.path.dirname(__file__))
    templateEnv = jinja2.Environment(loader=jinja2.FileSystemLoader(loc))
    template = templateEnv.get_template("stickers.html")

    app = Flask(__name__, static_folder=None)

    @app.route("/")
    def index():
        return render_template(template)

    @app.route("/stickers/<name>")
    def stickers(name):
        ok, r = getStickerSet(name)
        if not ok:
            return cast(dict, r), 400
        return r.json()

    host = "127.0.0.1"
    port = 5005
    webbrowser.open(f"http://{host}:{port}/")
    app.run(port=port, host=host)
