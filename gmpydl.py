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


def update_first():
	"""
	try:
		with open(os.path.expanduser("~/.gmpydl.conf")) as conf:
			## read through each line
			## put a 0 in first if we just did the oauth as you only need to do it once	
	except IOError:
		print "Error writing back to file
	"""
	return True

def begin() :

	settings = {}
	try:
		with open(os.path.expanduser("~/.gmpydl.conf")) as conf:
			lines = conf.readlines()
			for x in lines:
				parts = x.split()
				if parts[0] == 'email':
					settings['email'] = parts[1]
				if parts[0] == 'first':
					settings['first'] = parts[1]

	except IOError:
		print "Cant load config file. Does it exist? (~/.gmpydl.conf)"
		sys.exit()
	print "Logging in as %s" % settings['email']
		
	mm = Musicmanager()
	if settings['first'] == '1':
		mm.perform_oauth()
		update_first()
	if mm.login():
		return mm
	return False

def nice_close(api):
	return api.logout()


def main():
	api = begin()
	if api != False:
		songs = []
		for chunk in api.get_uploaded_songs(incremental=True):
			songs = songs + chunk
			print len(chunk)
	## do something with the songs
	nice_close(api)

main()
sys.exit()
