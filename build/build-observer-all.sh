#!/usr/bin/env bash

echo Enabling OPTECS python venv...
cd /c/git/pyFieldSoftware/virtualenv/optecs-python36/venv/Scripts/
source activate

cd /c/git/pyFieldSoftware/build
echo "Running initial build to set fullscreen."
python build_observer.py --mode ifqadmin

read -p "Check ObserverConfig manually, then continue..."

echo Running All Builds...

python build_observer.py --mode ifqadmin && python build_observer.py --mode prod && python build_observer.py --mode training
