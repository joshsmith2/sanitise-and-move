#!/usr/bin/python
#This script will check through all subfolders and files inside dir and remove all occurences of problematic characters

import sys
import os
import os.path
import re
import getopt
import time
import datetime

#Define functions:

def sanitise(inString):
#This function removes any occurences of characters found in blackList from theString, except ':' which, for legibility, are changed to '-'

		outString = inString.translate(None, blackList)

		#Remove all whitespace from filenames except spaces (from http://stackoverflow.com/questions/1898656/remove-whitespace-in-python-using-string-whitespace)
		noWhitespaceString = ' '.join(outString.split())

		#Prevent multiple runs of whitespace from being stripped
		noMultSpaceString = ' '.join(re.split(' +', outString))
	
		if noMultSpaceString != noWhitespaceString:
			
			outString = noWhitespaceString

		#Substitute hyphens for colons, to help legibility
		outString = re.sub(':','-',outString)

		return str(outString)

def appendIndex(filename, ext, path):
#Given a file 'filename' at location 'path' with extension 'ext', this will return the path of filename(n)ext, where n is the lowest integer for which filename(n-1)ext already exitsts.

	index = 1

	appendedFile = filename + "(" + str(index) + ")" + ext

	appendedPath = os.path.join(path, appendedFile)

	while os.path.exists(appendedPath) or appendedPath in sanitisedList:
		
		index += 1
		appendedFile = filename + "(" + str(index) + ")" + ext
		appendedPath = os.path.join(path, appendedFile)

	return appendedPath

def timeStamp():
#A timestamp which will tell you when the last renaming occurred. Will prefix all output from the program. 
		
	ts = time.time()
	return datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S') + " : "

def renameFile(prevPath, newPath, rename):
#Either renames a file, or logs it. 
	
	if rename:
		try:
					os.rename(prevPath, newPath)
					if not quiet:
						print timeStamp() + "Changed from: " + prevPath
						print timeStamp() + "Changed to:   " + newPath + "\n"
					if logFileName is not None:
						logFile.write( timeStamp() + "Changed from: " + prevPath + "\n")
						logFile.write( timeStamp() + "Changed to:	" + newPath + "\n")
		except OSError:
					print  timeStamp() + "Error: unable to rename " + prevPath + "\n"
					if logFileName is not None:
						logFile.write( timeStamp() + "Error: unable to rename " + prevPath + "\n")

	else:
		#Add the clean path to a list of changed files, so that logging without changing works correctly
		sanitisedList.append(newPath)


		if not quiet:
			print timeStamp() + "Would change:    " + prevPath
			print timeStamp() + "Would change to: " + newPath + "\n"
	
		if logFileName is not None:
			logFile.write( timeStamp() + "Would change:	 " + prevPath + "\n")
			logFile.write( timeStamp() + "Would change to: " + newPath + "\n")

def renameToClean(path, obj, objType):
		#Takes an object (a string - either a file or a directory, as defined in 'type' which must be one of 'file' or 'dir') and, if the string has any forbidden characters, sanitises it and renames it.

		fullPath = os.path.join(path, obj)		
	
		cleanObj = sanitise(obj)
		
		cleanPath = fullPath #This is a little dishonest here, since the path hasn't been cleaned yet, but it will change as soon as any sanitisation goes on

		#If sanitise has made any difference, record the file in a list of changed files, then rename the file.
		if cleanObj != obj:
			
				#Check for strings prefixed with '.', and remove these for replacement after file renaming.
				prefix = ""	
		
				if cleanObj[:1] == '.':
					prefix = '.'
					cleanObj = cleanObj[1:]

				#Separate filename from extension:
				cleanSplit = cleanObj.split('.')

				#For files and directories which were only composed of illegal characters, rename these 'Renamed file' or 'Renamed Folder'
				if cleanSplit[0].strip() == '':
						if objType == 'file':
								cleanObj = 'Renamed File' + cleanObj[len(cleanSplit[0]):]
						elif objType == 'dir':
								cleanObj = 'Renamed Folder'

				#Replace any previously removed periods
				cleanObj = prefix + cleanObj

				cleanPath = os.path.join(path, cleanObj)

				#If the clean path already exists, append '(n)' to the filename
				if os.path.exists(cleanPath) or cleanPath in sanitisedList:

						cleanPath = appendIndex(cleanSplit[0], cleanObj[len(cleanSplit[0]):], path)
	
				renameFile(fullPath, cleanPath, rename)
	
		#If the cleaned and original versions are the same, check that there's no case clash with a previously seen file
		else:
			
			if caseSens:		
				
				extension = ""

				if fullPath.lower() in lCaseList:
					
					filename = fullPath.split('/')[-1]
					
					#This could be spun off into a function, save some coding - bound to be reusable too.
					if "." in filename:
						extension = "." + filename.split(".")[-1]
						filename = filename[:-len(extension)]
				
					cleanPath = appendIndex(filename, extension, path)
	
					renameFile(fullPath, cleanPath, rename)

	 	#Append the clean (i.e final) path to the array which will allow us to check for case sensitive clashes, if the case sensitive option is set. 
	 	if caseSens:
			lCaseList.append(cleanPath.lower())

		if oversizeLogFileName is not None:
			if len(fullPath) > 254:
				if not quiet:
					print timeStamp() + "--WARNING-- Overlong directory found: " + cleanPath + " is " + str(len(cleanPath)) + " characters long.\n"
				if oversizeLogFileName is not None:
					oversizeFile.write( timeStamp() + "Oversize directory: " + cleanPath + "\n")
					oversizeFile.write(str(len(cleanPath)) + " characters long.\n\n")

def usage():
		print ("\nUsage:")
	
		print ("   -c, --casesensitive: For use on case sensitive filesystems. Default - off.")
		print ("   -d, --dorename:      Actually rename the files - otherwise just log and output to standard output")
		print ("   -e, --errorlog:      Error log (contains files which have thrown errors on renamed")
		print ("   -h, --help:          Print this help and exit")
		print ("   -l, --log:           Log filename; otherwise don't log ")
		print ("   -o, --oversizelog:   Log to write files with overlong path names in - otherwise don't log.")
		print ("   -q, --quiet:         Don't output to standard out")
		print ("   -r, --root:          Root directory otherwise use working directory\n")

try:
		opts, args = getopt.getopt(sys.argv[1:], "o:l:r:e:dhqbc", ["oversizelog=","log=", "root=", "dorename","help","quiet","debug","casesensitive","errorlog"])

except getopt.GetoptError as err:
		# print help information and exit:
		usage()
		print str(err) # will print something like "option -a not recognized"
		sys.exit(2)

sanitisedList=[]
errorList=[]
lCaseList=[]

#Argument variables
rename=False
theRoot = "."
logFileName = None
oversizeLogFileName = None
errorLogFileName = None
quiet = False
debug = False #NB - this variable used only during development, so not in the --help. 
oldPath = ""
caseSens = False

#If no options entered, print help and exit
if opts == []:
	print "\nError: no options passed."
	usage()
	sys.exit(2)

for o, a in opts:
		if o in ("-r","--root"):
				theRoot = a
		elif o in ("-l","--log"):
				logFileName = a
				logOut = os.path.abspath(logFileName)
				logFile = open (logOut, 'w')
		elif o in ("-d","--dorename"):
				rename = True
		elif o in ("-h","--help"):
				usage()
				sys.exit(2)
		elif o in ("-q","--quiet"):
				quiet = True
		elif o in ("-o","--oversizelog"):
				oversizeLogFileName = a
				oversizeOut = os.path.abspath(oversizeLogFileName)
				oversizeFile = open (oversizeOut, 'w')
		elif o in ("--debug"):
				debug = True
		elif o in ("-c", "--casesensitive"):
				caseSens = True
		elif o in ("-e", "--errorlog"):
				errorLogFileName = a
				errorOut = os.path.abspath(errorLogFileName)
				errorFile = open (logOut, 'w')

		

#These are the characters we want to remove
blackList = '`\/?"<>|*'


#MAIN FUNCTION:
#Save the first argument to a normalised logRoot variable


for thePath, theDirs, theFiles in os.walk(theRoot, topdown=False):

		#Sanitise file names
		for f in theFiles:
			renameToClean(thePath, f, 'file')
				
		#Sanitise directory names
		for d in theDirs:
				renameToClean(thePath, d, 'dir')
