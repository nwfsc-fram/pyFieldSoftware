#!/usr/bin/env bash

echo Enabling OPTECS python venv...
cd /c/git/pyFieldSoftware/virtualenv/optecs-python36/venv/Scripts/
source activate

cd /c/git/pyFieldSoftware/build
echo "Running initial build to set fullscreen."
python build_observer.py --mode ifqadmin

echo "Running pyrcc5 manually to update the observer_qrc file"
cd /c/git/pyFieldSoftware/
./virtualenv/optecs-python36/venv/Scripts/pyrcc5.exe qrc/observer.qrc -o py/observer/observer_qrc.py

read -p "Check ObserverConfig manually, then continue..."

echo Running All Builds...
cd /c/git/pyFieldSoftware/build

python build_observer.py --mode ifqadmin && python build_observer.py --mode prod && python build_observer.py --mode training

echo Opening Build Folder...
start dist