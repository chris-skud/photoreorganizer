import os
import sys
import EXIF
from os.path import join
from datetime import datetime
from datetime import date
import time

# Gets (and creates if necessary) the destination directory based on supplied args.  
def getDestDir(srcRoot, destRoot, year, month):
	# a bit hacky but always make sure month is 2 digit 
	if (len(month) == 1):
		month = '0' + month
	destDir = destRoot + '\\' + year + '\\' + month
	
	if not os.path.isdir(destDir):
		os.makedirs(destDir)
	return destDir

# command line format is: photoreorganizer.py startDir [destDir]
# example: photoreorganizer.py "C:\Documents and Settings\chriss\My Documents\My Pictures" "C:\MyNewPhotosDir"
# leaving the second parameter blank will simply create the dest directories as sub directories of the start dir (a very common use case)
logfile = open('log.txt', 'a')	
if not os.path.isdir(sys.argv[1]):
	print 'you did not supply a valid source directory.'
	logfile.write('Info: you did not supply a valid source directory.\n')
	sys.exit

#set srcRoot to first param
srcRoot = sys.argv[1]
#init destRoot to srcRoot.  Will be changed if user passed second arg
destRoot = sys.argv[1]

if len(sys.argv) > 2:
	logfile.write('Info: 2 args detected.\n')
	if os.path.isdir(sys.argv[2]):
		destRoot = sys.argv[2]
		logfile.write('Info: Second arg a valid directory and set to ' + destRoot + '\n')

logfile.write('Info: srcRoot = ' + srcRoot + ' destRoot = ' + destRoot + '\n')
for root, dirs, files in os.walk(srcRoot):

	# this section allows for exclusion of directories in the algorithm.  For now it's just Picasa specific but could 
	# be a user defined list
	for dir in dirs[:]:
		# Caution -this will break picasa meta and cause potential loss of edit/faces/etc fidelity
		if dir == 'Original':
			dirs.remove(dir)
		if dir == '.picasaoriginals':
			dirs.remove(dir)
	
	# iterate through the remaining directory's files
	for file in files[:]:
		srcFilePath = os.path.join(root, file)
		logfile.write('Info: -------------------- start processing file ' + srcFilePath + '--------------------\n') 
		dest = destRoot
		
		# skip if it's one of those pesky hidden files
		if '.ini' not in file:
			if '.db' not in file:
				# got get the extended image file properties 
				f = open(srcFilePath, 'rb')
				tags = EXIF.process_file(f, stop_tag="EXIF DateTimeOriginal")
				f.close()

				if not tags:
					logfile.write('Warning: NO EXIF TAGS for this file.  Falling back to filesystem date.\n')
					#dest = getFilePathFromSysModified(srcFilePath, destRoot, root, file)
					nonImgInfo = os.stat(srcFilePath)
					year = str(date.fromtimestamp(nonImgInfo.st_mtime).year)
					month = str(date.fromtimestamp(nonImgInfo.st_mtime).month)
					dest = os.path.join(getDestDir(root, destRoot, year, month), file)
				else:
					fileHasDateTime = False
					for tag in tags.keys():
						if tag == 'EXIF DateTimeOriginal':
							if not (str(tags[tag]) == '0000:00:00 00:00:00'):
								fileHasDateTime = True
								logfile.write('INFO: EXIF DateTimeOriginal = ' + str(tags[tag]) +'\n')
								dateParts = str(tags[tag]).split(':')
								year = dateParts[0]
								month = dateParts[1]
								dest = os.path.join(getDestDir(root, destRoot, year, month), file)
					if not fileHasDateTime:
						logfile.write('Warning: EXIF information was found but no DateTimeOrignal retrieved.  Using system modified time..\n')
						nonImgInfo = os.stat(srcFilePath)
						year = str(date.fromtimestamp(nonImgInfo.st_mtime).year)
						month = str(date.fromtimestamp(nonImgInfo.st_mtime).month)
						dest = os.path.join(getDestDir(root, destRoot, year, month), file)

				logfile.write('Info: for file: ' + srcFilePath + '\n')
				logfile.write('Info: Dest was determined as: ' + dest + '\n')
				
				try:
					logfile.write('Info: Attempting to move file...\n')
					if not (srcFilePath == dest):
						os.rename(srcFilePath, dest)
						logfile.write('Info: ' + file + ' successfully moved to ' + dest + '...\n')
					else:
						logfile.write('Info: ' + file + ' skipped.  File already in desired location (' + dest + ')...\n')
						# this is pretty much always going to be a file already exists problem, or the file is in use problem.
				except WindowsError as (errno, strerror):
					logfile.write('Error: Error #' + str(errno) + ': ' + strerror + '\n')
					print 'Error: An error has occured while attempting to copy a file.  Check the log for details.'
					if errno == 183:
						logfile.write('Error: ' + file + ' cannot be moved to ' + dest + ' as a file with the same name already exists.\n')
					else:
						logfile.write('Error: Unknown error when attempting to move ' + file + ' to ' + dest + '...\nThe file was not moved.\n')
		logfile.write('Info: -------------------- completed processing file ' + srcFilePath + '--------------------\n\n')
logfile.close()