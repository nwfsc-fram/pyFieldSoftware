 # SEE SQLite Encryption Extension
 * https://www.hwaci.com/sw/sqlite/see.html
 * https://www.sqlite.org/see
 
 # Installing sqlite3 dll, apsw+SEE for OPTECS development 
 * Get wheel from `bin\SQLite Encryption Extension` in source control
 * Get and run newest observer_keyinstaller_20170829.zip from `\\NWCFile\FRAM\Users\Todd.Hay\Observer\`
 * `pip install apsw-3.20.1.post1-cp36-none-win_amd64.whl`
 * Test via `pyqt5-framdata\test\sqlite_encryption_test\encryption_test.py`. You should see:
 ```commandline
[(1,)]
Success - apsw encryption functional.
```
 
 # Compiling and Testing SEE (Dev Notes)
 
 ### Compiling public domain SQLite
 * https://sqlite.org/howtocompile.html
 * 100+ files rolled into a single amalgamation:
   * https://sqlite.org/amalgamation.html
   * https://sqlite.org/download.html
   
   * For initial testing, downloaded https://sqlite.org/2017/sqlite-amalgamation-3190300.zip and the prerelease snapshot
   * For SEE compilation, downloaded https://see-sources.zip from https://sqlite.org/see/zip/see-sources.zip?uuid=release
      
   
  ### Building with MSVC 2015 Community - 64-bit DLL
  * Open MSBuild Command Prompt for Visual Studio 2015
  * To build SQLite+SEE:
  ```commandline
    cd VC
    vcvarsall amd64
    cd <git directory>\see-sources
    buildmsvc.bat
    builddlls.bat
    cd bld
    cl /Fesee.exe -DSQLITE_HAS_CODEC=1 shell.c see-sqlite3.c
     
    verify exports exist with:
    DUMPBIN /exports see.dll
  ```
  * To build the SQLitesnapshot build (Not needed - for SQlite without SEE)
    * Note that the documentation says `nmake/f makefile.msc sqlite3.c` which doesn't do anything useful
  ```commandline  
    cd VC
    vcvarsall amd64  (or just vcvarsall for 32-bit)
    cd \...git directory\sqlite-snapshot-xyz
    nmake /f Makefile.msc sqlite3.exe    
  ```  
  * To build the amalgamation (CLI, and DLL) (Not needed - for SQlite without SEE)
  ```commandline
    cd \...git directory\sqlite-amalgamation-xyz
    cl shell.c sqlite3.c -Fesee.exe
    REM cl /LD sqlite3.c - doesn't create exports!
    Instead (from https://protyposis.net/blog/compiling-sqlite-as-dll-with-msvc/) use: 
    cl sqlite3.c -DSQLITE_API=__declspec(dllexport) -link -dll -out:sqlite3.dll
    
    verify exports exist with:
    DUMPBIN /exports sqlite3.dll    
  ```
  ### Test with CLI
  ```commandline
    see.exe test_unencrypted.db
        
SQLite version 3.20.0 2017-08-01 13:24:15 with the Encryption Extension
Copyright 2016 Hipp, Wyrick & Company, Inc.
Enter ".help" for usage hints.
sqlite> create table TEST(INTEGER TEST);
sqlite>.quit
  ```
  * Verify can open in a SQLite browser
  * Now test encryption
```commandline
see.exe -key testing123 test_encrypted.db
        
SQLite version 3.20.0 2017-08-01 13:24:15 with the Encryption Extension
Copyright 2016 Hipp, Wyrick & Company, Inc.
Enter ".help" for usage hints.
sqlite> create table TEST(INTEGER TEST);
sqlite>.quit
  ```
  * Verify DB is encrypted (this is for a new DB)
  * Also, can test this on existing DB:
 ```
 see.exe test_to_be_encrypted.db
 sqlite> .rekey OLD NEW NEW
 ```
 
 * Note that OPTECS actually uses PRAGMA
 * For OPTECS compat, use this:
 ```
 see.exe test_to_be_encrypted.db
 sqlite> PRAGMA rekey = SomeKey
 ```
 
  ### Deploy + Test
  * Copy see.dll, renamed to sqlite3.dll to C:\python36\DLLs (back up existing first)
  * Copy to <virtualenv>\DLLs\sqlite3.dll (for cxFreeze)
  * Open Python 3.6 virtualenv, verify import sqlite3 works
```commandline
python
>>> import sqlite3
```
  * If you get an error (e.g. invalid executable) then you probably built a 32-bit DLL for 64-bit python (or vice versa)
  * Test functionality via pyqt5-framdata\test\sqlite_encryption_test
    * Be sure to run the new key installer
```commandline
[(1,)]
Success - sqlite encryption functional.
```

# Build APSW 3.20.1
 * from your virtualenv:
 * Check that the build works:(note we omit `--user` flag
```commandline
pip install https://github.com/rogerbinns/apsw/releases/download/3.20.1-r1/apsw-3.20.1-r1.zip --global-option=fetch --global-option=--version --global-option=3.20.1 --global-option=--all --global-option=build --global-option=--enable-all-extensions
```
* Download https://github.com/rogerbinns/apsw/releases/download/3.20.1-r1/apsw-3.20.1-r1.zip
  * extract to `(virtualenv)\`
* https://rogerbinns.github.io/apsw/build.html#finding-sqlite-3
* Copy `sqlite-see.c` and `sqlite.h` from `see-sources\bld` into `apsw-3.20.1-r1\sqlite3`)
  * Rename `sqlite-see.c` to `sqlite.c`
  * "When compiling the library, you will need to add command-line options to your compiler to set the SQLITE_HAS_CODEC #define"
  * Modify setup.py, add line 652:
``` 
ext.define_macros.append(("SQLITE_HAS_CODEC", 1))
```
  * Compile:
```commandline
python setup.py build --enable-all-extensions install
```
  * Convert egg to wheel:        
```commandline
pip install wheel
cp (venv)\apsw-3.20.1-r1\apsw-3.20.1-r1\dist\apsw-3.20.1.post1-py3.6-win-amd64.egg .
python -m wheel convert apsw-3.20.1.post1-py3.6-win-amd64.egg
```
  * Do not rename wheel