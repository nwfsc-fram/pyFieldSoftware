@echo off
echo RUNNING KEY INSTALLER AND DELETING IF SUCCESSFUL

observer_keyinstaller\observer_keyinstaller.exe

if %ERRORLEVEL% NEQ 0 goto done

echo Successful run, deleting key installer.
RMDIR /S /Q observer_keyinstaller
echo Completed deleting keyinstaller. 
pushd ..
DEL observer_keyinstaller*.zip
popd
echo Deleting self (script)
DEL RUN_ME_INSTALL_KEYS.bat
dir
:done
