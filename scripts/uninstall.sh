#!/bin/bash

# Exit if something fails
set -e

pip uninstall krunner_vscode -y

rm ~/.local/share/kservices5/plasma-runner-vscode.desktop
rm ~/.local/share/dbus-1/services/com.github.j1g5awi.vscode.service
kquitapp5 krunner
