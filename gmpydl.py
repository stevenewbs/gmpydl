#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2015 Steve Newbury

import argparse
import datetime
import os
import shelve
import sys
import threading
import unicodedata

from gmusicapi import Musicmanager

program_dir = os.path.expanduser("~/.gmpydl")
dl_store_file = os.path.join(program_dir, ".gmpydl_dl_store")
dl2_store_file = os.path.join(program_dir, ".gmpydl_dl2_store")
conf_file = os.path.join(program_dir, ".gmpydl.conf")
log_file = os.path.join(program_dir, "gmpydl.log")
settings = {'email': None, 'first': '1', 'email2': None, 'first2': '1', 'dest': '~/gmusic/MUSIC', 'nodl': False, 'uploader_id': None}

lock = threading.Lock()

def do_args():
  parser = argparse.ArgumentParser(description='GMPYDL - Steve Newbury 2015 - version 1.6')
  parser.add_argument('-n', '--nodl', action='store_true', help="No Download - synchronises a list of existing files.  Handy for initial sync if you dont need all your current music downloaded")
  parser.add_argument('-d', '--debug', action='store_true', help="Debug mode - only downloads 10 tracks")
  parser.add_argument('-s', '--search', action='store_true', help="Search for an album, artist or song to download")
  parser.add_argument('-t', '--threads', default=5, help="Number of multiple threads for downloading tracks (Default: 5)", type=int)
  parser.add_argument('-o', '--overwrite', action='store_true', help="Force overwrite of songs that already exist in the destination.")
  parser.add_argument('-a', '--addaccount', action='store_true', help="Add an extra Google account to download music from.") # i got married!
  parser.add_argument('--otheraccount', action='store_true', help="Use the second Google account (if configured)")
  args = parser.parse_args()
  settings['nodl'] = args.nodl
  return args

def update_first(email):
  if settings['email'] == email:
    line = "first 0\n"
  if settings['email2'] == email:
    line = "first2 0\n"
  try:
    with open(conf_file, "a") as conf:
      conf.write(line)
  except IOError as e:
    print("Failed to update conf file following OAUTH for %s" % e)
    print("Manually add the line \"%s\" to the config file" % line)
  return True

def make_prog_dir():
  if not os.path.exists(program_dir):
    try:
      os.mkdir(program_dir)
    except IOError as e:
      log("Error creating program dir: %s " % e)
      return False
  return True

def log(what):
  s = "\n%s : %s" % (datetime.datetime.now(), what)
  if TESTING:
    print(s)
  else:
    with open(log_file, 'ab+') as f:
      f.write(s.encode("UTF-8"))

def load_settings():
  if not make_prog_dir():
    return False
  if not os.path.exists(conf_file):
    # ask for the email address and music destination
    print("Welcome to gmpydl - I cant find a config file so please enter the following to begin\n")
    settings['email'] = input("Google Account email address: ")
    settings['dest'] = input("Music download destination directory: ")
    # If music manager is unable to resolve computer's MAC it needs to be explicitely set
    # https://unofficial-google-music-api.readthedocs.io/en/latest/reference/musicmanager.html#gmusicapi.clients.Musicmanager.login
    settings['uploader_id'] = input("Uploader ID, a unique id as a MAC address (all caps): ")
    try:
      with open(conf_file, "w") as conf:
        log("Writing config to file")
        conf.write("email %s\n" % settings['email'])
        conf.write("dest %s\n" % settings['dest'])
        conf.write("uploader_id %s\n" % settings['uploader_id'])
    except IOError as e:
      print("Error creating config file: %s" % e)
      return False
  else:
    try:
      # load settings from user conf file
      with open(conf_file) as conf:
        lines = conf.readlines()
        for x in lines:
          parts = x.split()
          if len(parts) < 1:
            continue
          if parts[0] == 'email':
            settings['email'] = parts[1]
          if parts[0] == 'dest':
            settings['dest'] = parts[1]
          if parts[0] == 'first':
            settings['first'] = parts[1]
          if parts[0] == 'uploader_id' and len(parts) > 1:
            settings['uploader_id'] = parts[1]
          if parts[0] == 'email2':
            settings['email2'] = parts[1]
          if parts[0] == 'first2':
            settings['first2'] = parts[1]
    except IOError:
      log("Cant load config file. Does it exist? (%s)" % conf_file)
      return False
    if settings['email'] == None:
      log("Email address not found")
      return False
  log("Music going to %s" % settings['dest'])
  return True

def add_account():
  if load_settings():
    if settings['email2'] == None:
      print("Adding second account to gmpydl - please enter the following to begin\n")
      settings['email2'] = input("Google Account email address: ")
      try:
        with open(conf_file, "a") as conf:
          log("Writng config to file")
          conf.write("\nemail2 %s\n" % settings['email2'])
      except IOError as e:
        print("Error creating config file: %s" % e)
        return False
      # perform the oauth
      api = api_init()
      if api is not False:
        nice_close(api)
    else:
      print("Please remove email2 setting from %s" % conf_file)
  else:
    print("Epic Fail! Check config file")

def api_init():
  mm = Musicmanager()
  e = settings['email']
  creds = os.path.expanduser("~/.local/share/gmusicapi/oauth.cred") # default oauth store location
  if OTHERACCOUNT:
    e = settings['email2']
    creds = os.path.expanduser("~/.local/share/gmusicapi/oauth2.cred")
  if e is not None:
    if settings['first'] == '1' or OTHERACCOUNT and settings['first2'] == '1':
      print("Performing OAUTH for %s" % e)
      mm.perform_oauth(storage_filepath=creds)
      update_first(e)
  log("Logging in as %s" % e)
  if mm.login(oauth_credentials=creds, uploader_id=settings['uploader_id']):
    return mm
  log("Login failed for second user")
  return False

def nice_close(api):
  return api.logout()

def fill_all_store(api):
  count = 0
  songs = []
  for chunk in api.get_uploaded_songs(incremental=True):
    songs = songs + chunk
    out = 'Loading library...%d' % len(songs)
    sys.stdout.write("\r\x1b[K"+out.__str__())
    sys.stdout.flush()
  print("\r\n")
  for s in songs:
    # id comes back in unicode so have to make it dictionary friendly string
    sid = unicodedata.normalize('NFKD', s['id']).encode('ascii', 'ignore').decode('ascii')
    if sid not in all_store:
      all_store[sid] = s
      count += 1

def get_song_data(song):
  return song['artist'], song['album'], song['album_artist'], song['title']

def download_song(api, sid, update_dl):
  song = _get_track_info(sid)
  path = _get_song_dir(song)
  artist, album, alb_artist, title = get_song_data(song)
  f = _get_normalized_file_path(path, song)
  if os.path.isfile(f):
    if not OVERWRITE:
      log("File {} already exists - marking as downloaded (enable Overwrite to re-download)".format(f))
      if update_dl:
        _update_dl(sid)
      return True
  # do the download
  try:
    log("Starting download of %s - %s" % (artist, title))
    _, audio = api.download_song(song['id'])
  except Exception as e:
    log(str(e) + " ID: " + song['id'] + " - " + song['title'])
    return False
  filepath = _get_normalized_file_path(path, song)
  try:
    with open(filepath, 'wb') as f:
      f.write(audio)
    if update_dl:
      _update_dl(sid)
  except IOError as e:
    log("Failed to write %s " % filepath + ": " + str(e))
    return False
  return True

def _update_dl(sid):
  with lock:
    dl_store[sid] = all_store[sid]
    dl_store.sync()

def _to_path(path_part):
  return path_part.replace("/","-")

def _get_normalized_file_path(path, song):
  song_title = song['title']
  song_title = _to_path(song_title)
  filename = u'%s/%02d - %s.mp3' % (path, song['track_number'], song_title)
  filepath = u'%s' % os.path.join(path, filename)
  return os.path.normpath(filepath)


def main():
  if not load_settings():
    return False
  api = api_init()
  if api:
    fill_all_store(api)
    if settings['nodl']:
      log("No download mode - synchronisig...")
      # dont do any downloads - mark all current songs as downloaded
      for s in all_store:
        dl_store[s] = all_store[s]
    else:
      diff = len(all_store) - len(dl_store)
      log("%d new songs" % diff)
      dl_count = 0
      if diff > 0:
        threads = list()
        for s in all_store:
          if s not in dl_store:
            if _mkdir_song(s):
              downloadThread = threading.Thread(target=download_song, args=(api, s, True), name="Thread-{}".format(s))
              downloadThread.setDaemon(True)
              threads.append(downloadThread)
            #download_song(api, s, True)
              dl_count += 1
              if TESTING and dl_count == 10:
                  break
        submit_threads(threads)

      log("%d new songs downloaded" % dl_count)
    nice_close(api)
  else:
    log("Failed to initialise GMusic API")

def _get_track_info(sid):
  return all_store[sid]

def _get_song_dir(song):
  path = None
  artist, album, alb_artist, title = get_song_data(song)
  if alb_artist and alb_artist != song['artist']:
    alb_artist_short = alb_artist.split(';')
    if len(alb_artist_short) > 0:
      alb_artist = alb_artist_short[0]
    path = os.path.expanduser("%s/%s/%s" % (settings['dest'], _to_path(alb_artist), _to_path(album)))
  else:
    path = os.path.expanduser("%s/%s/%s" % (settings['dest'], _to_path(artist), _to_path(album)))

  return path

def _mkdir_song(sid):
  song = _get_track_info(sid)
  path = _get_song_dir(song)
  result = True
  if not os.path.exists(path):
    try:
      os.makedirs(path)
    except OSError as e:
      log("Error making directory: %s" % e)
      result = False
    except IOError:
      log("Failed to make dir")
      result = False

  return result


def submit_threads(threads):
  total = len(threads)
  log("%d%%" % 0)
  index = 0
  while len(threads):
    partials = list()
    for thread in threads:
      thread.start()
      partials.append(thread)
      threads.remove(thread)
      if len(partials) == NUM_THREADS:
        break

    for t in partials:
      t.join()
      index += 1

    percentage = (index * 100) / total
    log("%d%%" % percentage)

def get_input():
  term = input("Enter your search term: ")
  ty = int(input("Supported search types: \nArtist - 1\nAlbum - 2\nSong - 3\nEnter type: "))
  return term, ty

def searchmain():
  if not load_settings():
    return False
  api = api_init()
  fill_all_store(api)
  term, termtyp = get_input()
  term = term.lower().strip()
  dl_list = {}
  for s in all_store:
    song = all_store[s]
    artist, album, alb_artist, title = get_song_data(song)
    if termtyp == 1:
      if term in artist.lower() or term in alb_artist.lower():
        dl_list[s] = song
    if termtyp == 2:
      if term in album.lower():
        dl_list[s] = song
    if termtyp == 3:
      if term in title.lower():
        dl_list[s] = song
  if len(dl_list) == 0:
    print("None found")
    return
  print("Proposing download of %d songs:" % len(dl_list))
  for s in dl_list:
    print("Song: %s - Artist: %s from Album: %s" % (dl_list[s]["title"], dl_list[s]["artist"], dl_list[s]["album"]))
  mode = int(input("Go ahead (1) or choose songs interactively (2)\n[1/2]: "))
  if not api:
    print("Error - Failed to initialise GMusic API") # notify user as this is generally run interactively
    return
  else:
    x = 1
    for s in dl_list:
      if mode == 2:
        do = input("Download %s - %s(%s)? [Y/n] :" % (dl_list[s]["title"], dl_list[s]["artist"], dl_list[s]["album_artist"]))
        if do.strip() == "n" or do.strip() == "N":
          print("Skipping...")
          continue
      if not _mkdir_song(s) or not download_song(api, s, False):
        print("Download failed - eh?!")
      else:
        out = "Completed %d/%d..." % (x, len(dl_list))
        if mode != 2:
          sys.stdout.write("\r\x1b[K"+out.__str__())
          sys.stdout.flush()
        else:
          print(out)
        x += 1
  print("Done!")
  nice_close(api)

if __name__ == "__main__":
  args = do_args()
  TESTING = args.debug
  SEARCHMODE = args.search
  OVERWRITE = args.overwrite
  ADDACCOUNT = args.addaccount
  OTHERACCOUNT = args.otheraccount
  NUM_THREADS = args.threads
  make_prog_dir()
  if ADDACCOUNT:
    add_account()
    sys.exit()
  all_store = {} # open an empty store
  if SEARCHMODE:
    searchmain()
  else:
    if OTHERACCOUNT:
      dl_store = shelve.open(dl2_store_file)
    else:
      dl_store = shelve.open(dl_store_file)
    main()
    dl_store.sync()
    dl_store.close()
  sys.exit()
