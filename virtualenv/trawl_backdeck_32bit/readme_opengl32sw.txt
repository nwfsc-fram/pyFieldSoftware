Windows 7, 32-bit version has a D3D incompatibility with PyQt 5.7+

To fix, we use software rendering.
* System->Advanced Properties->Environment Variables, add QT_OPENGL=software
(log off and log on to set it)
* Copy opengl32sw.dll to the same directory as trawl_backdeck.exe


