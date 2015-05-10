#!/usr/bin/env python

# Copyright (c) 2015 Steve Newbury
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from gmusicapi import Musicmanager
from getpass import getpass
import os
import sys
import shelve
import unicodedata

program_dir = os.path.expanduser("~/.gmpydl")
all_store_file = os.path.join(program_dir, ".gmpydl_store")
dl_store_file = os.path.join(program_dir, ".gmpydl_dl_store")
conf_file = os.path.join(program_dir, ".gmpydl.conf")

def update_first():
	try:
		with open(conf_file, "a") as conf:
			conf.write("first 0")
        except IOError:
		print "Failed to update conf file following OAUTH"
		print "Manually add the line \"first 0\" to the config file"
	return True

# assume its the first launch and have no id 
settings = {'email': None, 'last_id': '0', 'first': '1', 'dest': '~/gmusic/MUSIC'}

def load_settings():
	try:
		# load settings from user conf file
		with open(conf_file) as conf:
			lines = conf.readlines()
			for x in lines:
				parts = x.split()
				if parts[0] == 'email':
					settings['email'] = parts[1]
				if parts[0] == 'first':
					settings['first'] = parts[1]
				if parts[0] == 'last_id':
					settings['last_id'] = parts[1]
				if parts[0] == 'dest':
					settings['dest'] = parts[1]

	except IOError:
		print "Cant load config file. Does it exist? (~/.gmpydl.conf)"
		return False
	if settings['email'] == None:
		print "Email address not found"
		return False 
	print "Logging in as %s" % settings['email']
	return True

def begin():		
	mm = Musicmanager()
	if settings['first'] == '1':
		mm.perform_oauth()
		update_first()
	if mm.login():
		return mm
	return False

def nice_close(api):
	return api.logout()

def fill_all_store(api):
	print "%d songs in store" % len(all_store)
	count = 0
	songs = []
	for chunk in api.get_uploaded_songs(incremental=True):
		songs = songs + chunk
		
	print "%d songs online" % len(songs)
		
	for s in songs:
		# id comes back in unicode so have to make it "store" friendly string 
		sid = unicodedata.normalize('NFKD', s['id']).encode('ascii', 'ignore')
		if not all_store.has_key(sid):
			all_store[sid] = s
			count += 1 
	## do something with the songs
	all_store.sync
	print "Added %d songs to the store" % count
		
def download_song(api, sid):
	song = all_store[sid]
	artist = song['artist']
	album = song['album']
	alb_artist = song['album_artist']
	title = song['title']
	print alb_artist
	if alb_artist and alb_artist != artist:
		alb_artist_short = alb_artist.split(';')
		if len(alb_artist_short) > 0:
			alb_artist = alb_artist_short[0]
		path = os.path.expanduser("%s/%s/%s" % (settings['dest'], alb_artist, album))
	else:
		path = os.path.expanduser("%s/%s/%s" % (settings['dest'], artist, album))
	if not os.path.exists(path):
		try:
			os.makedirs(path)
			print "Making %s " % path
		except IOError:
			print "Failed to make dir"
			return False
	else:
		print "Path exists"
	songdata = all_store[sid]
	print "Starting download of %s - %s" % (artist, title)
	filename, audio = api.download_song(songdata['id'])
	filepath = os.path.join(path, filename)
	try:
		with open(filepath, 'wb') as f:
			f.write(audio)
		print "File written"
		dl_store[sid] = all_store[sid]
		print "added to download store"
	except IOError:
		print "Failed to write %s " % filepath
		return False
	return True

def main():
	if not load_settings():
		return False
	api = begin()
	if api != False:
		fill_all_store(api)
		#x = 0
		for s in all_store:
			if not dl_store.has_key(s):
				download_song(api, s)
				#x += 1
				#if x == 20:
				#	break
		nice_close(api)

if not os.path.exists(program_dir):
	os.mkdir(program_dir)
all_store = shelve.open(all_store_file)
dl_store = shelve.open(dl_store_file)
main()
all_store.close()
dl_store.close()
sys.exit()
