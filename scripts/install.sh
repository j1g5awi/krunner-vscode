#!/bin/bash

# Exit if something fails
set -e

pip install .

mkdir -p ~/.local/share/kservices5/
mkdir -p ~/.local/share/dbus-1/services/

cp ./package/plasma-runner-vscode.desktop ~/.local/share/kservices5/
cp ./package/com.github.j1g5awi.vscode.service ~/.local/share/dbus-1/services/

kquitapp5 krunner
