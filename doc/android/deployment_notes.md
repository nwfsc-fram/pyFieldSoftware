Notes: PyQt Android Deployment
----

# WORK IN PROGRESS

* https://riverbankcomputing.com/software/pyqtdeploy/intro
* https://plashless.wordpress.com/2014/05/16/using-pyqtdeploy/

Target Device:
---
* http://business.panasonic.com/toughpad/us/5-inch-tablet-fz-x1.html
* Toughpad FZ-X1
* Android 4.2.2
* 1280x720


Install environment:
---
* Installed Qt 5.8.0, selected x64 MSVC and Android

* Installed Android Developer Studio (admin access required) 

* In SDK Manager, install API 17 (4.2) and under SDK Tools: LLDB, CMake, and NDK
via https://developer.android.com/ndk/guides/index.html
http://pyqt.sourceforge.net/Docs/pyqtdeploy/static_builds.html#sip

* Build http://pyqt.sourceforge.net/Docs/pyqtdeploy/static_builds.html
* https://plashless.wordpress.com/2014/05/16/using-pyqtdeploy/
* https://plashless.wordpress.com/2014/08/19/using-pyqtdeploy0-5-on-linux-to-cross-compile-a-pyqt-app-for-android/



`Errors: 
WARNING: Failure to find: ..\$SYSROOT\src\Python-3.6.0\Modules\_winapi.c
WARNING: Failure to find: ..\$SYSROOT\src\Python-3.6.0\PC\msvcrtmodule.c
WARNING: Failure to find: ..\$SYSROOT\src\Python-3.6.0\Modules\selectmodule.c
...`
* To fix this get python source https://www.python.org/ftp/python/3.6.0/Python-3.6.0.tgz
unzip to C:\Python36\src

`Errors:
WARNING: Failure to find: frozen_bootstrap.h
WARNING: Failure to find: frozen_bootstrap_external.h
WARNING: Failure to find: frozen_main.h
WARNING: Failure to find: frozen_bootstrap.h
WARNING: Failure to find: frozen_bootstrap_external.h
...`
* To fix this, TBD - environment issue on Windows?

1. Download Android SDK and NDK, JDK,
  * e.g. `C:\Android\NDK\android-ndk-r14b-windows-x86_64\android-ndk-r14b`
  * Apache Ant 1.10 zip http://ant.apache.org/bindownload.cgi
  * SDK 25.3 doesn't support Qt 5.8, so need to drop back - TBD

1. Set up QtCreator
  * Tools, Options, Devices - Android Tab, set up JDK, SDK, NDK locations
  C:\Android\NDK\android-ndk-r14b-windows-x86_64\android-ndk-r14b
  * Point to ant.bat
  * Now under Options, Build & Run, should have no warnings for Android versions 

### ADB Driver for Toughpad
http://pc-dl.panasonic.co.jp/itn/drivers/d_menu_en.html#Toughpad

## Set up cmd environment
* Start Dev Environment CMD - VS2015
* start optecs-python36 virtualenv
* Run C:\Qt5.8\5.8\msvc2015_64\bin\qtenv2.bat
* Run VS 2015 vars "C:\Program Files (x86)\Microsoft Visual Studio 14.0\VC\vcvarsall.bat"
  
* make directory <sandbox>\pyqtdeploy\sysroot-android
* set ENV:
  * `set SYSROOT=C:\Qt5.8\5.8\android_armv7\C:\Will.Smith\git\pyqt5-framdata\sandbox\will.smith\pyqtdeploy\sysroot-android`
  * `set path=%PATH%;C:\Android\Sdk\tools;C:\Android\Sdk\platform-tools`
  * `set JAVA_HOME="C:\Program Files\Java\jdk1.8.0_131"`


http://pyqt.sourceforge.net/Docs/pyqtdeploy/build_sysroot.html

1. Launch AVD at 720x1280 resolution, running API 17 (Jelly Bean)


### Using Python 3.6 virtualenv:

1. `pip install pyqtdeploy==1.3.2`

1. Created `android_deploy_test` test application (basic QML and .py file)

1. `pyqtdeploycli --package pyqt5 --target android-32 configure` 

1. `pyqtdeploy android_test.pdy` which opens UI configuration. 
(File->Save before trying Build. Build crashed until I installed Qt 5.8 and followed env setup above.) 
)
* see screenshots, config TBD
* Change Locations Source Drectory $SYSROOT to C:/Python36
1.  Patched 2 functions in `builder.py` - See Will for details 

1. `pyqtdeploycli --project android_test.pdy --output test_output/ --package pyqt5 --target android-32 --android-api 17 build`

1. `C:\Will.Smith\git\pyqt5-framdata\virtualenv\optecs\Lib\site-packages\PyQt5\qmake.exe main.pro`

C:\Qt5.8\5.8\android_armv7\bin\qmake.exe
C:\Qt5.8\5.8\android_armv7\


#### misc
got https://dl-ssl.google.com/android/repository/android-19_r04.zip

got older SDK Tools:
https://dl.google.com/android/repository/tools_r24.4.1-windows.zip

### Build Static Binaries
http://pyqt.sourceforge.net/Docs/pyqtdeploy/static_builds.html#sip
pip install pyinstaller (?)

set ANDROID_NDK_PLATFORM=android-17
`pyqtdeploycli --package pyqt5 --target android-32 configure`


* Uninstalled Build Tools from SDK manager, unpacked tools_r24xx.zip in android\sdk
* Projects ICON on left for apk options - broken?

* Close Qt Creator
* Modify `C:\Will.Smith\git\pyqt5-framdata\sandbox\will.smith\qt_creator_test\AndroidQtTest\AndroidQtTest.pro.user`
  * fix line to be `<value type="QString" key="BuildTargetSdk">android-17</value>`
  
 * Fix `Cannot find template directory C:/Android/SDK/tools/templates/gradle/wrapper`
   * Copy them from `<SDK Tools>\plugins\android\lib\templates`
   to
   `C:\Android\SDK\tools\templates`
   
   Copy C:\Android\SDK\tools_r24.4.1-windows\tools to C:\Android\SDK\tools



### Build and Deploy
1. Build app for Android
1. Install to device (or drag APK onto emulator)
```
C:\Android\SDK\platform-tools>adb devices
List of devices attached
6GKSA06937      device
emulator-5554   device
```

`C:\Android\SDK\platform-tools>adb -s 6GKSA06937 install C:/Will.Smith/git/pyqt5-framdata/sandbox/will.smith/qt_creator_test/build-AndroidQtTest-Android_for_armeabi_v7a_GCC_4_9_Qt_5_8_0_for_Android_armv7-Debug/android-build//build/outputs/ap
k/android-build-debug.apk
`

## CONFIGURE VM
* Followed guide for python 2.7 kivy default build, broke
* Had do this, still broke
  *    `export ANDROIDAPI="14"`
* follow python 3 guide https://github.com/kivy/buildozer, nope
* follow Developers.txt android instructions

`wget https://github.com/GreatFruitOmsk/pyqtdeploy.git`

doc.qt.io/qt-5/androidgs.html

out of space, so expand
`"c:\Program Files\Oracle\VirtualBox\VBoxManage.exe" clonehd "Buildozer VM-disk001.vmdk" "Bu
ildozer VM-disk001.vdi" --format vdi`
`"c:\Program Files\Oracle\VirtualBox\VBoxManage.exe" modifyhd "Buildozer VM-disk001.vdi" --resize 5100`
reattach
gparted to resize
resize lvm
https://serverfault.com/questions/631355/how-to-resize-drive-that-is-out-of-space-on-dev-mapper
pvresize /dev/sda1
sudo lvextend -l +100%FREE /dev/mapper/whateveritis-root
sudo resize2fs /dev/mapper/cloudraker--vg-root 

`unrecognized -fstack-protector-strong for arm g++`
*  Installed need newer android-ndk-14c

Cannot for GL for Desktop build
* `apt-get install libgl1-mesa-dev`

* start venv
* Fix MemoryError on pip install on virtual environment
  * `pip install PyQt5 --no-cache-dir`

export ANDROID_NDK_ROOT=(14c)
export ANDROID_NDK_PLATFORM=android-19
export ANDROID_NDK_TOOLCHAIN_VERSION=4.9
export ANDROID_SDK_ROOT=(20)

cd $SYSPATCH/src
wget https://sourceforge.net/projects/pyqt/files/sip/sip-4.19.2/sip-4.19.2.tar.gz
wget https://

internal compiler error
* increased base memory
no qt_lib_charts.pri, just commented out building charts, data vis, scintilla from build-sysroot.py

log2 compile error, check plashless blog, modify pyconfig.h 
`#undef HAVE_LOG2`
getsid compile error, do the same, but still getting an error... giving up
`#undef HAVE_GETSID` doesn't work

install NDK 10e - WORKS!!!


