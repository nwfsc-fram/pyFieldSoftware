# Old README - obsolete, for future reference



## NOTE: Notes below are outdated

## Python 3.4, PyQt5.5 Installation Instructions

- Install Python 3.4 - https://www.python.org/downloads/
- Add PYTHON and PYTHON\scripts paths to your system PATH
- Install Qt 5.5 - http://www.qt.io/download-open-source/#section-2
- Install PyQt5 - https://riverbankcomputing.com/software/pyqt/download5
- Install PyCharm - https://www.jetbrains.com/pycharm/download

# Common Configuration Instructions
- Create PyCharm Run Configuration - see screenshot in doc/RunConfigurationScreen.png
  - You will need separate "external tool" entries for each of the projects you require, e.g. qml/observer.qrc etc.
  - When you add new files to a project, remember to also add them to the corresponding .qrc file (easy to forget.)
- Configure PyCharm external tools to run pyrrc.exe to compile the Qt resources to a python script - see screenshot in doc/ExternalToolsConfiguration.png
- Python Libraries - Install the following python libraries that are used as part of this application
    - PyInstaller - pip install pyinstaller
    - APSW - http://www.lfd.uci.edu/~gohlke/pythonlibs/
    - PySerial - pip install pyserial

## Building the Deployable Package
- Navigate to the build folder, run the appropriate cmd file (e.g. build_trawl_backdeck.cmd)
- The output package will be available in build/dist/main_trawl_backdeck


## Notes - trying to get Python 3.5, PyQt5.6, and virtualenv via PyCharm configuration working
## This is not working completely yet
- Install Python 3.5.1 - https://www.python.org/downloads/release/python-351/ Windows x86-64 executable installer
   - Customize installation, install to C:\Python35\ (Check Add Python 3.5 to PATH)
   - Logout or reboot
- Install Qt 5.5 - http://www.qt.io/download-open-source/#section-2
- Install PyCharm - https://www.jetbrains.com/pycharm/download
- Configure PyCharm virtualenv
   - File->Settings, Project -> Project Interpreter-> Click Gear Icon -> Add Local -> c:\python35\python.exe
     - Should create base interpreter with just pip and setuptools
- Remove c:\python34\scripts\ from PATH in System Environment Variables if it's there
- Set [clear?] QT_QPA_PLATFORM_PLUGIN_PATH Sys Env Variable to C:\Python35\Lib\site-packages\PyQt5\plugins\platforms
    - Fixes "[Qt]This application failed to start because it could not find or load the Qt platform plugin "windows" 
- OPTIONAL - Uninstall PyQt5.5 from Programs and Features
- OPTIONAL - Uninstall old Qt from Programs and Features

- Repeat gear icon step, this time create VirtualEnv called PyQt56 (or whatever) 
  based on python 3.5, don't import global packages, make avail to all
  - Open cmd prompt, run C:\Will.Smith\git\virtualenv\PyQt56\Scripts\activate.bat
  
  - Download apsw-3.12.2.post1-cp35-cp35m-win_amd64.whl, copy to Scripts dir (or wherever is handy)
  - Run (note pip3 install of pyqt5)
python -m pip install --upgrade pip
pip3 install pyqt5
pip install apsw-3.12.2.post1-cp35-cp35m-win_amd64.whl
pip install pyinstaller
pip install pyserial
pip install peewee
pip install python-dateutil

- (?) NOW run the PyQt5.6 Windows installer (x64), install to c:\python35, copy Lib\site-packages\PyQt5 to
  corresponding dir in your virtualenv

- Not working - QtQuick.Controls is not installed etc

- Edit External Tools pyrcc to point to c:\python35\...PyQt5\pyrcc5.exe

- Copy PyQt5 from c:\python35\Lib\site-packages\ to your virtualenv site-packages dir
  - Fixes "QtQuick" is not installed


