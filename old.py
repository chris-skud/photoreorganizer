import os
import sys
import shutil
import EXIF
from os.path import join
from datetime import datetime
from datetime import date
import time
import traceback

# Function to format a timestamp (string) into a legal file format
# two forms this will come in
# 1- system file mod timestamp (ie '2007-06-27 21:24:01.921875')
# 2- EXIF DateTimeOriginal timestamp (ie '2007:06:27 21:24:01')
# result should be something like '2007-06-27_t212401[_original]'
def getLegalFileName(root, file, strTimestamp):

	# get rid of the milliseconds if it's an os.stat timestamp
	if strTimestamp.find('.'):
		tmp = strTimestamp.split('.')
		strTimestamp = tmp[0]
	
	# separate the date from time and replace delimiters with legal characters
	strTimestamp = strTimestamp.split(' ')
	theDate = strTimestamp[0].replace(':', '-')
	theTime = '_t' + strTimestamp[1].replace(':', '')
	fileName = theDate + theTime

	# this is purely to deal with how Picasa manages edits to images.  Originals directory stores
	# the original of the file.  Instead of deleting, i'm appending _original to the to the filename
	if root.find('Original') > 0:
		fileName = fileName + '_original'
	elif root.find('.picasaoriginals') > 0:
		fileName = fileName + '_original'
	
	# and finally, let's stick the correct extension back on there and return
	if file.find('.') > 0:
		fileParts = file.split('.')
	fileName = fileName + '.' + fileParts[1]
	return fileName

def getDestDir(destRoot, year):
	return destRoot + '\\' + year


# command line format is: organizephotos.py startDir [destDir]
# example: organizephotos.py "C:\Documents and Settings\chriss\My Documents\My Pictures" "C:\MyNewPhotosDir"
# leaving the second parameter blank will simply create the dest directories as sub directories of the start dir (a very common use case)
if not os.path.isdir(sys.argv[1]):
	print 'you did not supply a valid starting directory.'
	sys.exit
destRoot = sys.argv[1]
if len(sys.argv) > 2:
	if os.path.isdir(sys.argv[2]):
		destRoot = sys.argv[2]

for root, dirs, files in os.walk(sys.argv[1]):

	# need to test for dirs that are 4 characters and start with '20' as in '2006'
	for dir in dirs[:]:
		# removes the target dirs to ensure no files are ever processed twice by this script.
		# i can modify (dirs.remove) in-place due to how os.walk Top=true works.
		if len(dir) == 4:
			if dir.startswith('20'):
				dirs.remove(dir)
	print dirs
	# iterate through the remaining directory's files
	for file in files[:]:
		srcFilePath = os.path.join(root, file)
		dest = destRoot
		
		# exit loop if it's one of those pesky hidden files
		if file == 'Thumbs.db':
			break
		elif file == 'Picasa.ini':
			break
		elif file == '.picasa.ini':
			break

		# got get the extended image file properties 
		try:
			f = open(srcFilePath, 'rb')
			tags = EXIF.process_file(f, stop_tag="EXIF DateTimeOriginal")
		except:
			tags = None
			print 'Error: EXIF problem.  Using file last modified date to name file.' + file
			errFile = open("errlog.txt","a")
			errFile.write(print_exc() + ' -- file: ' + file)
			raw_input("wait for you " + file)
		finally:
			f.close()
		# deal with non-image types.  just default to the file's last modification date.
		if not tags:
			nonImgInfo = os.stat(srcFilePath)
			year = str(date.fromtimestamp(nonImgInfo.st_mtime).year)
			dest = os.path.join(getDestDir(destRoot, year), getLegalFileName(root, file, str(datetime.fromtimestamp(nonImgInfo.st_mtime))))
			print 'not tags' + getLegalFileName(root, file, str(datetime.fromtimestamp(nonImgInfo.st_mtime)))
		# we've got an image and it's extended properties, now get the DateTimeOriginal (the picture creation date)
		else:
			for tag in tags.keys():
				if tag == 'EXIF DateTimeOriginal':
					dateParts = str(tags[tag]).split(':')
					year = dateParts[0]
					dest = os.path.join(getDestDir(destRoot, year), getLegalFileName(root, file, str(tags[tag])))
					print 'exif tags' + getLegalFileName(root, file, str(tags[tag]))
		
		if not os.path.isdir(getDestDir(destRoot, year)):
			os.mkdir(getDestDir(destRoot, year))
		try:
			print 'moving ' + file + ' to ' + dest + '...'
			#os.rename(srcFilePath, dest)
		# this is pretty much always going to be a file already exists problem, or the file is in use problem.
		except WindowsError as (errno, strerror):
			print 'Error #' + str(errno) + ': ' + strerror + ' file: ' + file
