# playlibraryhtml
Fetches launcher icons and screenshots of downloaded Play Store apps 

## Requirements:

Python 3.10.6 (may work with other versions too)
Library.json file from [Google takeout](https://takeout.google.com/)

## How-to


1.	Download the newest [release](https://github.com/Pave99/playlibraryhtml/releases/)
2.	Extract it somewhere
3.	Go to [Google takeout](https://takeout.google.com/) and check only Google Play Store, and wait for Google to process it, wont take long.
4.	Extract the zip file and copy Library.json to the same folder
5.	Open cmd or Terminal, navigate to the folder and execute _pip install -r requirements.txt_
6.	After installing the requirements, run _python library.py_ 
7.	Sit back and wait for it to complete. (For my 1200 apps, it took around an hour)
8.	After it has finished, open apps_with_icons.html, and enjoy.
