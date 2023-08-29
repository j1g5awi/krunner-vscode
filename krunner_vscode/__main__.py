import difflib
import json
import os
import subprocess
import sqlite3
import sys
from operator import attrgetter
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

HOME = str(Path.home())


class Match(NamedTuple):
    data: str
    display_text: str
    icon: str
    type: int
    relevance: float
    properties: dict


def get_matches(paths, query):
    """
    Equivalent to `difflib.get_close_matches`, but returning the ratio too
    """
    matches = []
    s = difflib.SequenceMatcher()
    s.set_seq2(query)

    for path in paths:
        s.set_seq1(path)
        matches.append((s.ratio(), path))

    return matches


# Read path_list from database
def get_path_list():
    paths = set()

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

        for entry in data["entries"]:
            if "folderUri" not in entry:
                continue

            path = entry["folderUri"].replace("file://", "")

            if not os.path.exists(path):
                continue

            if path.startswith(HOME):
                path = path.replace(HOME, "~", 1)

            paths.add(path)
    return paths


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
                ratio,
                {"subtext": path},
            )
            for ratio, path in get_matches(get_path_list(), query)
        ]

    @dbus.service.method(iface, out_signature="a(sss)")
    def Actions(self):
        # id, text, icon
        return [("id", "Open Folder", "document-open-folder")]

    @dbus.service.method(iface, in_signature="ss")
    def Run(self, data: str, action_id: str):
        subprocess.run([
            "code" if not action_id else "xdg-open",
            str(data)
        ], shell=True)

def main():
    runner = Runner()
    if sys.argv[1:]:
        # Manual search - useful for local testing
        for match in sorted(runner.Match(sys.argv[1]), key=attrgetter("relevance")):
            print(match.data, match.relevance)
    else:
        loop = GLib.MainLoop()
        loop.run()


if __name__ == "__main__":
    main()
