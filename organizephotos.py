import os
import sys
import EXIF
from os.path import join
from datetime import datetime
from datetime import date
import time

# Function to format a timestamp (string) into a legal file format
# two forms this will come in
# 1- system file mod timestamp (ie '2007-06-27 21:24:01.921875')
# 2- EXIF DateTimeOriginal timestamp (ie '2007:06:27 21:24:01')
# result should be something like '2007-06-27_t212401[_original]'
def getLegalFileName(root, file, strTimestamp, isOsStatTimestamp):

	#first, grab the file extension as we'll need it later
	# oh, and make sure we get the part after the last occurence of '.'
	fileParts = file.split('.')
	fileExtension = fileParts[len(fileParts)-1] 
	
	# get rid of the milliseconds if it's an os.stat timestamp
	if isOsStatTimestamp:
		if strTimestamp.find('.'):
			tmp = strTimestamp.split('.')
			strTimestamp = tmp[0]
	
	# separate the date from time and replace delimiters with legal characters
	strTimestamp = strTimestamp.split(' ')
	theDate = strTimestamp[0].replace(':', '-')
	theTime = '_t' + strTimestamp[1].replace(':', '')
	fileName = theDate + theTime

	# We have to further disambiguate files by using combo of timestamp and original name.  Even this could get dicey
	# if someone has copied the same file to a different subdirectory and not changed the name.	
	# if this file has not already been processed append the original filename
	if fileName not in fileParts[0]:
		fileName = fileName + '__' + fileParts[0]
	# this file already has the correctly formatted name, just use it.
	else:
		fileName = fileParts[0]

	# this is purely to deal with how Picasa manages edits to images.  Originals directory stores
	# the original of the file.  Instead of deleting, i'm appending _original to the to the filename
	if root.find('Original') > 0:
		fileName = fileName + '_original'
	elif root.find('.picasaoriginals') > 0:
		fileName = fileName + '_original'
	
	fileName = fileName + '.' + fileExtension
	return fileName

def getDestDir(destRoot, year):
	destDir = destRoot + '\\' + year
	if not os.path.isdir(destDir):
		os.mkdir(destDir)
	return destDir

def getFilePathFromSysModified(srcFilePath,destRoot, root, file):
	nonImgInfo = os.stat(srcFilePath)
	year = str(date.fromtimestamp(nonImgInfo.st_mtime).year)
	return os.path.join(getDestDir(destRoot, year), getLegalFileName(root, file, str(datetime.fromtimestamp(nonImgInfo.st_mtime)), True))

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

logfile = open('log.txt', 'a')
logfile.write('Info: Starting in ' + destRoot + '\n')
for root, dirs, files in os.walk(destRoot):

	# need to test for dirs that are 4 characters and start with '20' as in '2006'
	for dir in dirs[:]:
		# removes the target dirs to ensure no files are ever processed twice by this script.
		# i can modify (dirs.remove) in-place due to how os.walk Top=true works.
		if len(dir) == 4:
			if dir.startswith('20'):
				dirs.remove(dir)
	# iterate through the remaining directory's files
	for file in files[:]:
		srcFilePath = os.path.join(root, file)
		logfile.write('Info: -------------------- start processing file ' + srcFilePath + '--------------------\n') 
		dest = destRoot
		
		# exit loop if it's one of those pesky hidden files
		if '.ini' not in file:
			if '.db' not in file:
				# got get the extended image file properties 
				f = open(srcFilePath, 'rb')
				tags = EXIF.process_file(f, stop_tag="EXIF DateTimeOriginal")
				f.close()

				if not tags:
					logfile.write('Warning: NO EXIF TAGS for this file\n')
					dest = getFilePathFromSysModified(srcFilePath, destRoot, root, file)
				else:
					fileHasDateTime = False
					for tag in tags.keys():
						if tag == 'EXIF DateTimeOriginal':
							fileHasDateTime = True
							logfile.write('INFO: EXIF DateTimeOriginal = ' + str(tags[tag]) +'\n')
							dateParts = str(tags[tag]).split(':')
							year = dateParts[0]
							dest = os.path.join(getDestDir(destRoot, year), getLegalFileName(root, file, str(tags[tag]), False))
					if not fileHasDateTime:
						logfile.write('Warning: EXIF information was found but no DateTimeOrignal retrieved.  Using system modified time..\n')
						dest = getFilePathFromSysModified(srcFilePath, destRoot, root, file)

				logfile.write('Info: for file: ' + srcFilePath + '\n')
				logfile.write('Info: Dest was determined as: ' + dest + '\n')
				
				try:
					logfile.write('Info: Attempting to move file...\n')
					os.rename(srcFilePath, dest)
					logfile.write('Info: ' + file + ' successfully moved to ' + dest + '...\n')
				# this is pretty much always going to be a file already exists problem, or the file is in use problem.
				except WindowsError as (errno, strerror):
					logfile.write('Error: Error #' + str(errno) + ': ' + strerror + '\n')
					if errno == 183:
						logfile.write('Error: ' + file + ' cannot be moved to ' + dest + ' as it already exists.\n')
					else:
						logfile.write('Error: Unknown error when attempting to move ' + file + ' to ' + dest + '...\nThe file was not moved.\n')
		logfile.write('Info: -------------------- completed processing file ' + srcFilePath + '--------------------\n\n')
logfile.close()