import json
import os
import sqlite3
from pathlib import Path
from typing import NamedTuple

import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

DBusGMainLoop(set_as_default=True)

objpath = "/vscode"

iface = "org.kde.krunner1"


VSCODE_DIRS = [
    "Code",
    "Code - OSS",
    "VSCodium"
]


class Match(NamedTuple):
    data: str
    display_text: str
    icon: str
    type: int
    relevance: float
    properties: dict


# Read path_list from database
def get_path_list():
    paths = {}

    for vscode_dir in VSCODE_DIRS:
        state_file = os.path.join(
            os.environ["HOME"], ".config", vscode_dir, "User/globalStorage/state.vscdb"
        )

        if not os.path.exists(state_file):
            continue

        con = sqlite3.connect(state_file)
        cur = con.cursor()
        rows = cur.execute(
            "SELECT value FROM ItemTable WHERE key = 'history.recentlyOpenedPathsList'"
        )
        data = json.loads(rows.fetchone()[0])
        con.close()
        paths.update(
            {
                "~" + path[len(os.environ["HOME"]) :] if os.environ["HOME"] in path else path
                for path in [i["folderUri"][7:] for i in data["entries"] if "folderUri" in i]
            }
        )


class Runner(dbus.service.Object):
    def __init__(self):
        dbus.service.Object.__init__(
            self,
            dbus.service.BusName(
                "com.github.j1g5awi.vscode", dbus.SessionBus()  # type:ignore
            ),
            objpath,
        )

    @dbus.service.method(iface, in_signature="s", out_signature="a(sssida{sv})")
    def Match(self, query: str):
        # data, display text, icon, type (Plasma::QueryType), relevance (0-1), properties (subtext, category and urls)
        return [
            Match(
                path,
                Path(path).name,
                "com.visualstudio.code.oss",
                100,
                1.0,
                {"subtext": path},
            )
            for path in get_path_list()
            if query.lower() in Path(path).name.lower()
        ]

    @dbus.service.method(iface, out_signature="a(sss)")
    def Actions(self):
        # id, text, icon
        return [("id", "Open Folder", "document-open-folder")]

    @dbus.service.method(iface, in_signature="ss")
    def Run(self, data: str, action_id: str):
        if not action_id:
            os.system("code " + data)
        else:
            os.system("xdg-open  " + data)


runner = Runner()
loop = GLib.MainLoop()
loop.run()
