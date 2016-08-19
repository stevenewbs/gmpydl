# gmpydl
Google Music Python Downloader
-----

Basic idea is a command line downloader thing that can sit on a raspberry pi or server and auto-grab any new music I buy.

Uses this library to interact with the googs:

https://github.com/simon-weber/Unofficial-Google-Music-API

http://unofficial-google-music-api.readthedocs.org/en/latest/index.html


Requirements
-----
* Python2
* gmusicapi (see above for installation via pip)
* A Google account with some music


Usage
-----
    git clone https://github.com/stevenewbs/gmpydl
    cd gmpydl
    ./gmpydl

If ~/.gmpydl/.gmpydl.conf does not exist (first run), you will be asked to confirm your Google account details and the directory you want your music to end up in.


Options
-----
* -d, --debug      : Debug mode. Redirects log to terminal and limits downloads to 10 at a time.
* -n, --nodl       : Don't download, just synchronise the file lists. Effectively marks all songs as "downloaded".
* -s, --search     : Run in search mode - allows you to find a particular artist, song or album to download.
* -o, --overwrite  : Force overwrite of songs that already exist in the destination.
* -a, --addaccount : Add a second Google account to download music from (The "partner" solution - I got married!)
* --otheraccount   : Use the second Google account (if configured)


Changes
-----
* 1.6 - Added the "otheraccount" feature because my wife wants her music on the NAS as well. As a result "all_store" is now not a shelf (stored in file). This way, library is dynamically loaded depending on account used to log in. Oauth credentials for both accounts can be stored so you still only need to Oauth once per account.
* 1.5 - Added the overwrite check to prevent download of songs that already exist. Added Overwrite flag to allow you to force through the check. Added the search feature. 


ToDo
-----
As a result of hacking in the 1.6 feature the code is now super ugly - sorry! When I have time I am going to tidy it up and possibly add a GUI option.
