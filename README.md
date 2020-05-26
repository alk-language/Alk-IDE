# ALKA-47

![ALKA-47 image](https://github.com/alk-language/Alk-IDE/blob/master/img.png)

## ALKA-47 is an open source IDE for the alk programming language. ALKA-47 was made using the WxWidgets module for python(wxpython).

#### Available features right now(checked):
- [x] syntax highlighting
- [x] auto indentation
- [x] file manager
- [x] multiple projects handler
- [x] basic text editor functionaltities (find, replace, keyboard shortcuts, configureable window, etc.)
- [x] list of arguments
- [ ] debugger
- [ ] code completion
- [ ] themes

## How to set up

#### Since ALKA-47 is still a work in-progress there are still no available executable to download, that means you will have to compile the source code by yourself or run directly the python script.


## (Windows/MacOS)

Download ALKA-47(Windows) directory.

First of all you have to install Python 3.x in your computer (recommended the latest version).  You can do that [here](https://www.python.org/downloads/).

Next step you'll have to get the wxPython module. Just open your command prompt and type the command bellow:

`pip -install -U wxPython`

Now you should be able to run ALKA-47.py script directly using the PYTHON interpretor.

#### How to compile to executable

For that you will have to get pyinstaller with the following command in the command prompt:

`pip install pyinstaller`

Then go into your ALKA-47 folder and open command prompt there(or any other shell terminal) and add the following command:

`pyinstaller -w --exclude _tkinter --exclude _ssl --exclude _sqlite3 --exclude tk85.dll --exclude tcl85.dll --exclude sqlite3.dll --exclude _testcapi --exclude _lzma --exclude _bz2 -i bitmaps\icon.ico ALKA-47.py`

When compiled successfully copy `/bitmaps` , `/Preferences` and `/tmp` to `/dist/ALKA-47/` directory.
Now the directory `/dist/Alka-47/` should contain the standalone application. You can now move it to any location you want.

## Linux
Download ALKA-47(Linux) directory.
Make sure that your Linux python version is >= 3.6 (type `python --version` in terminal).

If not , type the following in the terminal:

`sudo apt-get update && sudo apt-get upgrade`

`sudo apt-get install python3.7`

Make sure you have `pip3` installed (type `pip3 --version`). If not type the following:

`sudo apt update`

`sudo apt install python3-pip`

Once installation is complete install the required packages for wxpython:

`sudo apt install make gcc libgtk-3-dev libwebkitgtk-dev libwebkitgtk-3.0-dev libgstreamer-gl1.0-0 freeglut3 freeglut3-dev python-gst-1.0 python3-gst-1.0 libglib2.0-dev ubuntu-restricted-extras libgstreamer-plugins-base1.0-dev`

Note that this might take a while since it will compile the source code of the library.

After completion get wxpython with : `pip3 install --user wxPython`

Now you should be able to run the editor's script with the PYTHON interpretor ( `python3 %SCRIPT%` ).

#### How to compile to binary

Get pyinstaller : `pip3 install pyinstaller`

Then go into your ALKA-47 folder and open command prompt there(or any other shell terminal) and add the following command:

`pyinstaller -w --exclude _tkinter --exclude _ssl --exclude _sqlite3 --exclude tk85.dll --exclude tcl85.dll --exclude sqlite3.dll --exclude _testcapi --exclude _lzma --exclude _bz2 -i bitmaps\icon.ico ALKA-47.py`

When compiled successfully copy `/bitmaps` , `/Preferences` and `/tmp` to `/dist/ALKA-47/` directory.
Now the directory `/dist/Alka-47/` should contain the standalone application. You can now move it to any location you want.
