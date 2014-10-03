#!/usr/bin/python2.7
"""
Search for characters in filenames which are illegal in Windows. Either log or
remove these.

Designed as part of Hogarth's archiving procedure.

Author: Josh Smith
Contact: joshsmith2@gmail.com

"""

#TO DO LIST
#FUNCTIONALITY:
#TODO: Write test function
#TODO: Deal with proliferation of global variables

#FORMATTING:
#TODO: Fix string formatting for some long strings
#TODO: Line lengths

import atexit
import getopt
import os
import os.path
import shutil
import sys
import swisspy
from itertools import chain
import subprocess as sp
from string import whitespace

#These can be reconfigured depending on the folder structure
toArchiveDir = "./To Archive"
passDir =  "./Passed_For_Archive"
illegalLogDir = "./Logs"
problemDir = "./Problem Files"
hiddenDir = "./.Hidden"
transferErrorDir=os.path.join(problemDir,"_Transfer_Errors")

class File:
    """Used to define a file which exists in source and dest

    location : str
        Path to file
    size : int
        Size of file
    modtime : str
        Last modified time of file
    md5 : str
        md5 hash of file

    """
    def __init__(self,
                 path,
                 size="",
                 m_time="",
                 md5=""):
        self.path = path
        self.size = size
        self.m_time = m_time
        self.md5 = md5

def cleanUp(pid_file, log_file):
    """Run some cleanup tasks on unexpected exit"""
    purgeHiddenDir()
    #Close pid files, if they exist
    try:
        os.remove(pid_file)
    except OSError as e:
        if e.errno == 2:
            #Pidfile doesn't exist.
            pass
        else:
            raise

def logList(human_header,  the_list,
            syslog_header="", log_files=[], syslog_files=[],
            log_split='\n\t', syslog_split='\n'):
    """Log lists of strings gracefully, sending a human readable header and list
    to LOG_FILES, and a machine readable one to syslog_files.

    human_header : str
        An explanation of what this list represents
    syslog_header : str
        A header for logstash, if required.
    the_list : list
        List to be logged
    log_files : list : paths
        Human readable log files
    syslog_files : list : paths
        Syslog files
    log_split : str
        Default '\n\t'
        The string with which to join the human readable list.
    syslog_split : str
        Default: '\n'
        The string with which to join the syslog list.

    """
    if log_files:
        swisspy.print_and_log(human_header + log_split +  log_split.join(the_list) + "\n",
                          log_files=LOG_FILES)
    if syslog_files:
        headedList = [syslog_header + l for l in the_list]
        swisspy.print_and_log(syslog_split.join(headedList) + syslog_split,
                          syslog_files=syslog_files, quiet=True, ts=None)

def moveAndCreate(source,dest):
    """Move a file from source to dest, creating intermediate directories
     if they don't exist.

     """
    if not os.path.exists(dest):
        dest_dirname = sp.Popen(['dirname', dest], stdout=sp.PIPE).communicate()[0][:-1]
        move_command = sp.call(['mv', '-v', source, dest], stderr=sp.PIPE)

        #If the move has failed, it's probably because the intermediates don't exist.
        if move_command > 0:
            sp.call(['mkdir','-p', dest_dirname])
            sp.call(['mv', '-v', source, dest])

def pathJoin(path1, path2):
    """Returns a properly formatted path with extraneous backslashes removed
    consisting of a concatenation of path1 and path2

    """
    return os.path.abspath(swisspy.unescape(swisspy.prepend(path1, path2)))

def purgeHiddenDir():
    """Move all files back out of .Hidden and into problemDir"""
    for o in swisspy.immediate_subdirs(hiddenDir):
        # If any file in .Hidden is already in problemFolder,
        # move it to a new timestamped folder to avoid overwriting.
        if os.path.exists(os.path.join(problemDir, o)):
            movedTo = os.path.join(problemDir, "Duplicates_" + swisspy.time_stamp('short'))
            os.mkdir(movedTo)
            # Removed 'try' here
            swisspy.print_and_log(str(o) + " has been moved to " + str(movedTo) + "/" + str(o) + \
                              ".\n                      " + \
                              "Please move or delete the folder from this " + \
                              "location once it is no longer required.\n",
                              LOG_FILES, quiet=quiet)

# Should never need to do this
#            except ValueError as e:
#                reopenedLogs=[open(os.path.abspath(f.name), 'a') for f in LOG_FILES]
#                swisspy.print_and_log(str(o) + " has been moved to " + str(movedTo) + "/" + str(o) + \
#                                  ".\nPlease move or delete the folder from " +\
#                                  "this location once it is no longer required.\n",
#                                  reopenedLogs, quiet=quiet)
        else:
            movedTo = problemDir
        try:
            shutil.move(os.path.join(hiddenDir, o), movedTo)
        except OSError as e:
            swisspy.print_and_log("Error occurred when moving " + hiddenDir + "/" +\
                              o + ": " + str(e) + "\n", LOG_FILES, quiet=quiet)

def renameFile(pathDict, prevPath, renameLogFile, rename=False, indicator='^',):
    """Renames a file, or logs its abberations

    pathDict : dict
        A dictionary as output by sanitise():
        {'result': The sanitised string,
         'subsMade': Any characters which were removed or substituted
         'positions': the positions of the chars in subsMade}
    prevPath : str : path
        The original path to the file
    rename : bool
        If True, rename the file; otherwise just log.
    indicator : str
        Used in logging to indicate positions of changed characters

    """
    prevRoot = os.path.dirname(prevPath)
    newPath = os.path.join(prevRoot, pathDict['outString'])
    #Work out where the changed characters are in the full string, as opposed
    #to just the basename. Strip the path the the hidden dir off this.
    positionsInPath = [p + len(prevRoot) - len(hiddenDir) for p in pathDict['positions']]
    #Strip the path of the hidden dir out of the string to be logged
    #The '+1' here deals with the first forward slash
    pathToLog = prevPath[len(hiddenDir) + 1:]
    newPathToLog = newPath[len(hiddenDir) + 1:]
    #Construct indicator string (shows where offending characters are)
    indList = []
    for i in range(len(pathToLog)):
        if i in positionsInPath:
            indList.append(indicator)
        else:
            indList.append(" ")
    indLine = ''.join(indList)

    if rename:
        try:
            shutil.move(prevPath, newPath)
            # Log the renamed file in human readable format, on the SAN if
            # a rename log file has been defined...
            changeLogFiles = LOG_FILES[:]
            if renameLogFile:
                changeLogFiles.append(renameLogFile)

            swisspy.print_and_log("Changed from: " + pathToLog + '\n' +\
                              "Changed to:   " + newPathToLog + '\n\n',
                               changeLogFiles, ts="long", quiet=quiet)
            # ...and for logstash.
            if logstashDir:
                with open(logstashFiles['renamed'], 'a') as lsf:
                    lsf.write("{Changed from: }" + prevPath +\
                              "{to: }" + newPath + '\n')
        except OSError:
            swisspy.print_and_log("Error: unable to rename " + prevPath + '\n',
                               LOG_FILES, ts="long", quiet=quiet)
    else:
        # Add the clean path to a list of changed files,
        # so that logging without changing works correctly
        sanitisedList.append(newPath)
        if pathDict['subsMade']:
            swisspy.print_and_log("Illegal characters found in file   : " +\
                               pathToLog + '\n',
                               LOG_FILES, ts=None, quiet=quiet)
            swisspy.print_and_log("At these positions                 : " +\
                               indLine + '\n',
                               LOG_FILES, ts=None, quiet=quiet)
            swisspy.print_and_log("Characters found (comma separated) : " +\
                               ', '.join(pathDict['subsMade']) + '\n',
                               LOG_FILES, ts=None, quiet=quiet)
            swisspy.print_and_log("Suggested change                   : " +\
                               newPathToLog + '\n\n',
                               LOG_FILES, ts=None, quiet=quiet)

def retryWrapper(errorList):
    """Iterate through errorList, retrying the transfer of any failed files"""
    if errorList:
        for e in errorList:
            eSourcePath = e[0]
            eDestPath = e[1]
            newErrors = retryTransfer(eSourcePath, eDestPath, errorList)
            return newErrors

def retryTransfer(src,dest,errors):
    """Attempt to retransfer errored files.
    Returns none on success, and raises any errors encountered.

    """
    if os.path.exists(dest):
    #If file exists in dest, do an md5 check to see if it's the same as src.
        try:
            src_md5 = swisspy.get_md5(src)
        except IOError as e:
            if os.path.exists(dest):
                swisspy.print_and_log("File " + src + " does not exist. " +\
                                  "Look for it at " + dest + \
                                  "\nError: " + str(e) + "\n",
                                  LOG_FILES, quiet=quiet)
            else:
                swisspy.print_and_log("File does not exist at " + src + " or " + dest + \
                                  "\nError: " + str(e) + "\n",
                                  LOG_FILES, quiet=quiet)
            return None

        dest_md5 = swisspy.get_md5(dest)
        if src_md5 == dest_md5:
            return None
    try:
        shutil.move(src,dest)
        return None
    except shutil.Error as e:
        return e.message
    except Exception as e:
        print "\nA fatal error occurred: ", e
        sys.exit(1)

def renameToClean(obj, path, objType, renameLogFile):
    """If path contains any forbidden characters, sanitise it and rename it.

    obj : str
        Name of the file or directory object to be sanitised.
    path : str : path
        Basename to obj - path at which it is located.
    objType : str : 'file', 'dir'
        The type of the object to be sanitised ('file' or 'dir')
    renameLogFile : str : path
        Path to the file in which to log renamed objects.

    """
    global ERRORS_FOUND
    fullPath = os.path.join(path, obj)
    cleanPath = fullPath
    cleanDict = sanitise(obj)

    #If sanitising made any difference, there will be entries in subMade
    if cleanDict['subsMade']:
        #Check for strings prefixed with '.', remove this character, and replace it after file renaming.
        ERRORS_FOUND = True
        prefix = ""
        if cleanDict['outString'][:1] == '.':
            prefix = '.'
            cleanDict['outString'] = cleanDict['outString'][1:]
        #Separate filename from extension:
        cleanSplit = cleanDict['outString'].split('.')
        #For files and directories which were only composed of illegal characters, rename these 'Renamed file' or 'Renamed Folder'
        if cleanSplit[0].strip() == '':
            if objType == 'file':
                cleanDict['outString'] = 'Renamed File' + cleanDict['outString'][len(cleanSplit[0]):]
            elif objType == 'dir':
                cleanDict['outString'] = 'Renamed Folder'
        #Replace any previously removed periods
        cleanDict['outString'] = prefix + cleanDict['outString']
        cleanPath = os.path.join(path, cleanDict['outString'])
        #If the clean path already exists, append '(n)' to the filename
        if os.path.exists(cleanPath) or cleanPath in sanitisedList:
            cleanPath = swisspy.append_index(cleanSplit[0], cleanDict['outString'][len(cleanSplit[0]):], path)
        #Set the newly constructed path as the clean path to use
        cleanDict['outString'] = cleanPath
        renameFile(cleanDict, fullPath, renameLogFile, rename)
    # If the cleaned and original versions are the same, check that there's no
    # case clash with a previously seen file
    else:
        if caseSens:
            extension = ""
            if fullPath.lower() in lCaseList:
                filename = fullPath.split('/')[-1]
                if "." in filename:
                    extension = "." + filename.split(".")[-1]
                    filename = filename[:-len(extension)]
                cleanPath = swisspy.append_index(filename, extension, path)
                renameFile(cleanDict, fullPath, renameLogFile, rename)

    # Append the clean (i.e final) path to the array which will allow us to
    # check for case sensitive clashes, if the case sensitive option is set.
    if caseSens:
        lCaseList.append(cleanPath.lower())
    if oversizeLogFileName is not None:
        if len(fullPath) > 254:
            if not quiet:
                print swisspy.time_stamp() + "--WARNING-- Overlong directory found: " + cleanPath + \
                      " is " + str(len(cleanPath)) + " characters long.\n"
            if oversizeLogFileName is not None:
                oversizeFile.write( swisspy.time_stamp() + "Oversize directory: " + cleanPath + "\n")
                oversizeFile.write(str(len(cleanPath)) + " characters long.\n\n")

def sanitise(inString):
    """Remove any occurrences of characters found in blackList from theString,
    except ':' which, for legibility, are changed to '-'

    Returns a dictionary consisting of the return string, a list of characters
    substituted, and their positions

    inString : str
        The string to be processed

    """
    blackList = '' #Delete these characters. Currently empty.
    replaceList = [(':','-'), ('`','_'), ('\\','_'), ('/','_'), ('?','_'),
                   ('"','_'), ('<','_'), ('>','-'), ('|','_'), ('*','_')]
    subsMade = set() #Any characters which have been substituted. Here to catch ':'
    positions = []
    outStringList = []

    """Go through the input string character by character,
    constructing on output list which can be joined to form out output.
    This meticulous approach allows us to identify
    which characters were exchanged, and where. """
    for n, char in enumerate(inString):
        charToAppend = char
        #Remove characters from the blacklist
        if char in blackList:
            subsMade.add(char)
            positions.append(n)
            charToAppend = ''
        #Substitute any non-space whitespace with spaces
        if char in whitespace and char != " ":
            subsMade.add("Whitespace(" + repr(char) + ")")
            positions.append(n)
            charToAppend = ' '
        #Make any replacements (e.g ':' for '-')
        for rl in replaceList:
            replaceIn = rl[0]
            replaceOut = rl[1]
            if char == replaceIn:
                subsMade.add(char)
                positions.append(n)
                charToAppend = replaceOut
        outStringList.append(charToAppend)
    outString = ''.join(outStringList)
    return {'outString':outString, 'subsMade':subsMade, 'positions':positions}

def usage():
        print ("sanitise-and-move : A utility to facilitate cross-platform "\
               "file transfers, by dealing with illegal characters in a "\
               "sensible way. Developed by Josh Smith (joshsmith2@gmail.com)")
        print ("\nUsage:")
        print ("   -c, --casesensitive: For use on case sensitive filesystems Default - off.")
        print ("   -d, --dorename:      Actually rename the files - otherwise just log and output to standard output.")
        print ("   -h, --help:          Print this help and exit.")
        print ("   -l  --logstashDir:   A directory on the archive box containing a set of files sent by rsyslog to logstash.")
        print ("   -r  --renameLogDir:  Directory, usually on the destination, for logs of files which have been renamed to be stored.")
        print ("   -o, --oversizelog:   Log to write files with overlong path names in - otherwise don't log.")
        print ("   -p, --passdir:       Directory to which clean files should be moved.")
        print ("   -q, --quiet:         Don't output to standard out.")
        print ("   -t, --target:        The location of the hot folder")
        print ("   --temp-log-file:     A file to write log information to\n")

def writePid(dirId):
    """Write PID file to prevent multipe syncronously running instances of the
    program.

    """
    pidFile = "/tmp/SanitisePaths" + dirId + ".pid"
    if os.path.isfile(pidFile):
        with open(pidFile, 'r') as pf:
            existing_pid = pf.read()
            try:
                if swisspy.check_pid(existing_pid):
                    swisspy.print_and_log("Process with pid " + existing_pid +\
                                      " is currently running. Exiting now.\n",
                                      [tempLogFile], ts='long', quiet=False)
                    sys.exit()
                else:
                    swisspy.print_and_log("Removing stale pidfile\n",
                                      [tempLogFile], ts='long', quiet=False)
                    os.remove(pidFile)
            except OSError as e:
                swisspy.print_and_log("Process could not be checked. Error: " +\
                                  str(e) + "\n",
                                  [tempLogFile], ts='long', quiet=False)

    else:
        pf = open(pidFile, 'w')
        pf.write(str(os.getpid()))
    atexit.register(cleanUp, pid_file=pidFile, log_file=logFile)

def stripHidden(from_list, to_remove=os.path.abspath(hiddenDir)):
    """Given a lost of files, remove a given common path from them - in this
     case, the path to the hidden directory.

    from_list : list : strings : paths
        The list of paths to be stripped
    to_remove :
        The common path to be removed

    """
    return [f[len(to_remove):] for f in from_list]

def moveAndMerge(source, dest, retry=3):
    """Copy source to dest, merging child folders which already exist in dest,
    but erroring on any files which already exist there.

    source : str : path
        The source of the files
    dest : str : path
        The destination
    retry : int
        How many times to retry failed transfers
    """
    existingDifferingFiles = [] #Files which already exist in dest, and differ from any uploaded files with the same name. If this is not empty by the end of the walk, source will not be copied
    existingSameFiles = [] #Files which exist in the destination but have the same modification time and size as the file to be moved.
    clearedForCopy = [] # Array of directories which can safely be copied as long as no clashes are found. Returned if and only if existingDifferingFiles is empty.
    copiedFileList = [] # Array of files which made it.
    errorList = []
    emptyDirs = []
    #TODO: Put the variables above into the docstring
    sourceToLog = source.split('/')[-1]
    prefix = source[:-len(sourceToLog)]

    #Check source itself before walking
    if not os.path.exists(dest):
        try:
            shutil.move(source, dest)
            swisspy.print_and_log ("No errors found in new folder " + sourceToLog + ". " +\
                               "Folder moved to " + dest + "\n",
                               LOG_FILES, quiet=quiet)
        except shutil.Error as e:
            errorList.append(e)
            swisspy.print_and_log ("One or more files failed while trying " +\
                               "to move " + sourceToLog + " to " + dest +\
                               ". This folder has been moved to the " +\
                               "'Problem Files' directory.\n" +\
                               "Error: \n " + str(e) + "\n",
                               LOG_FILES, quiet=quiet)
        #Walk to get list of files moved
        swisspy.print_and_log("Walking destination to get list " +\
                          "of transferred files.\n",
                          LOG_FILES, quiet=quiet)
        for root, dirs, files in os.walk(dest):
            for f in files:
                 copiedFileList.append(os.path.join(root,f))
    else:
        swisspy.print_and_log("Examining " + dest + " for existing files\n",
                          LOG_FILES, quiet=quiet)
        for root, dirs, files in os.walk(source):
            #Starting from the deepest file,
            for f in files:
                source_file = File(path=os.path.join(root,f))
                pathAfterSource = source_file.path[len(source)+1:]
                dest_file = File(path=os.path.join(dest, pathAfterSource))
                #If any file in source exists in dest, log this.
                #Otherwise, add it to the 'cleared' list.
                if os.path.exists(dest_file.path):
                    #Get attributes for source and dest files
                    source_file.size = os.path.getsize(source_file.path)
                    source_file.m_time = swisspy.get_mod_time(source_file.path)
                    dest_file.size = os.path.getsize(dest_file.path)
                    dest_file.m_time = swisspy.get_mod_time(dest_file.path)
                    if source_file.size == dest_file.size and \
                       source_file.m_time == dest_file.m_time:
                        existingSameFiles.append(source_file)
                    else:
                        if source_file.size != dest_file.size:
                            existingDifferingFiles.append((source_file,
                                                           dest_file))
                        elif source_file.m_time != dest_file.m_time:
                            source_file.md5 = swisspy.get_md5(source_file.path)
                            dest_file.md5 = swisspy.get_md5(dest_file.path)
                            if source_file.md5 != dest_file.md5:
                                existingDifferingFiles.append((source_file,
                                                               dest_file))
                            else:
                                existingSameFiles.append(source_file)
                else:
                    clearedForCopy.append(source_file.path)

            for d in dirs:
                dir = os.path.join(root,d)
                afterSource = dir[len(source)+1:]
                if not os.path.exists(os.path.join(dest, afterSource)):
                    clearedForCopy.append(dir)
                    #Remove this directory from the list of dirs to be walked
                    dirs.remove(d)

        if existingDifferingFiles:
            file_reports=[]
            file_no = 1
            for edf in existingDifferingFiles:
                header = "\n\tFile {}:".format(file_no)
                file_reports.append(header)
                file_no += 1
                #edf is a tuple of source and dest files, so:
                for f in edf:
                    file_report = "\n\t{}:".format(f.path)
                    for attr_name in ['size','m_time','md5']:
                        attr_value = getattr(f,attr_name)
                        if attr_value:
                            file_report += "\n\t{}: {}".format(attr_name,
                                                               attr_value)
                    file_reports.append(file_report)
                file_reports.append("\n")
            logList("Unable to move {0}. The following {1} files already " \
                    "exist in {2}: \n".format(source,
                                              len(existingDifferingFiles),
                                              dest),
                    file_reports,
                    log_files=LOG_FILES,
                    #TODO: Put syslog files in here, into [there_and_different]
                    )
            purgeHiddenDir()
            swisspy.print_and_log("Please version these files " +\
                              "and attempt the upload again.\n",
                              LOG_FILES, quiet=quiet)
        else:
            if clearedForCopy:
                swisspy.print_and_log("Moving files cleared for copy\n\t" +\
                                  "Files transferred:\n",
                                  LOG_FILES, quiet=quiet)
                for c in clearedForCopy:
                    target = os.path.join(dest,c)
                    try:
                        shutil.move(c, target)
                        copiedFileList.append(c)
                        swisspy.print_and_log("\t" + c + "\n",
                                          LOG_FILES, ts=None, quiet=quiet)
                    except shutil.Error as e:
                        errorList.append(e)

            if errorList:
                logList("An error occurred when moving some files to " + dest +\
                        ".\nError: ",
                        str(errorList),
                        log_files=LOG_FILES,
                        syslog_files=[logstashFiles['failed']])
            else:
                swisspy.print_and_log("No transfer errors occurred. " +\
                                  "Folder exists at " + dest + "\n\t",
                                  LOG_FILES, quiet=quiet)
    if errorList:
        error= chain(errorList).next().args[0]
        allSources = [e[0] for e in error]
        success = False

        abidingErrors = error
        abidingSources = allSources

        for i in range(retry):
            swisspy.print_and_log("\nTry no. " + str(i + 1) + ': ' +\
                              "Retrying files\n\t" +\
                              '\n\t'.join(stripHidden(abidingSources, prefix)) + '\n',
                              LOG_FILES, quiet=quiet)

            retryErrors = retryWrapper(abidingErrors)
            if retryErrors:
                abidingErrors = retryErrors
                abidingSources = [e[0] for e in abidingErrors]
            else:
                swisspy.print_and_log("Transfer of files\n\t" +\
                                  '\n\t'.join(allSources) + "\ncompleted on "+\
                                  "try " + str(i + 1) + ".\n",
                                  LOG_FILES, quiet=quiet)
                copiedFileList.extend(allSources)
                success=True
                break

        if not success:
            logList("The following files failed to transfer, and have been moved to " +\
                    os.path.abspath(transferErrorDir) + ".\n" +\
                    "These files can be resubmitted by placing them in \n\t" +\
                    toArchiveDir + ".\n"
                    "If there is still a directory corresponding to the copied " +\
                    "project in 'Problem Files', these files will no longer " +\
                    "be contained within it.\nIf you would like to recombine " +\
                    "the project without resubmitting it, copy the files " +\
                    "in \n\t" + transferErrorDir + "\n into the project folder " +\
                    "in \n\t" + problemDir +\
                    ", choose 'merge' in the dialogue box which appears, " +\
                    "and delete the folder in " + transferErrorDir + ".",
                    stripHidden(abidingSources, prefix),
                    syslog_header="{MovedTo:}" + os.path.abspath(transferErrorDir),
                    log_files=LOG_FILES,
                    syslog_files=[logstashFiles['transfer_error']]
                    )

            #Move errored files to transferErrorDir
            for f in abidingSources:
                file_path_start = len(os.path.abspath(hiddenDir))
                file_path = os.path.abspath(f)[file_path_start + 1:]
                move_to = os.path.abspath(os.path.join(transferErrorDir, file_path))
                moveAndCreate(f,move_to)

    if copiedFileList:
        logList("The following files transferred successfully: \n\t",
                copiedFileList,
                log_files=LOG_FILES,
                syslog_files=[logstashFiles['transferred']]
        )

    if existingSameFiles:
        logList("The following files already have up to date copies" + \
                " in the archive, and were therefore not transferred:",
                stripHidden([e.path for e in existingSameFiles], prefix),
                log_files=LOG_FILES,
                syslog_files=[logstashFiles['there_but_same']],
                )
        if not existingDifferingFiles:
            for esf in existingSameFiles:
                try:
                    os.remove(esf.path)
                except Exception as e:
                    swisspy.print_and_log("Could not delete " + esf +\
                                     " due to the following error: " + str(e),
                                     LOG_FILES, quiet=quiet)

            #Walk the remaining files from the bottom, removing empty directories:
            for root, dirs, files in os.walk(source,topdown=False):
                emptyDirs.append(root)
                os.rmdir(root)
            swisspy.print_and_log("Removed the following empty directories:\n\t" +\
                              '\n\t'.join(stripHidden(emptyDirs, prefix)) + '\n')

#Initialise command line options
try:
    opts, args = getopt.getopt(sys.argv[1:],
                               "r:l:o:t:p:qdhcx",
                               ["renameLogDir=","logstashDir=","oversizelog=",
                                "target=","passdir=","quiet","dorename",
                                "help","casesensitive","debug",
                                "temp-log-file",]
                              )

except getopt.GetoptError as err:
        # print help information and exit:
        usage()
        print str(err) # will print something like "option -a not recognized"
        sys.exit(2)

sanitisedList = []
errorList = []
lCaseList = []
LOG_FILES = []

#Argument variables
caseSens = False
debug = False #NB - this variable used only during development, so not in the --help.
ERRORS_FOUND = False
errorLogFileName = None
logFile = None
location = None
logstashDir = None
oldPath = ""
oversizeLogFileName = None
quiet = False
rename = False
renameLogDir = None
target = toArchiveDir
tempLogFile = open ("/tmp/saniTempLog.log", 'a')
theRoot = hiddenDir

for o, a in opts:
        if o in ("-d","--dorename"):
            rename = True
        elif o in ("-h","--help"):
            usage()
            sys.exit(2)
        elif o in ("-q","--quiet"):
            quiet = True
        elif o in ("-o","--oversizelog"):
            oversizeLogFileName = a
            oversizeOut = os.path.abspath(oversizeLogFileName)
            oversizeFile = open (oversizeOut, 'a')
        elif o == "--temp-log-file":
            tempLogFile = open(os.path.abspath(a), 'a')
        elif o == "--debug":
            debug = True
        elif o in ("-c", "--casesensitive"):
            caseSens = True
        elif o in ("-p", "--passdir"):
            passDir = a
        elif o in ("-x", "--problemDir"):
            problemDir = a
        elif o in ("-l", "--logstashdir"):
            logstashDir = os.path.abspath(a)
        elif o in ("-r", "--renamelogdir"):
            renameLogDir = os.path.abspath(a)
        elif o in ("-t", "--target"):
            target = a
            theRoot = pathJoin(target, theRoot)
            illegalLogDir = pathJoin(target, illegalLogDir)
            passDir = pathJoin(target, passDir)
            problemDir = pathJoin(target, problemDir)
            toArchiveDir = pathJoin(target, toArchiveDir)
            hiddenDir = pathJoin(target, hiddenDir)
            transferErrorDir=os.path.join(problemDir,"_Transfer_Errors")

#Construct a directory id for use in PID and log files
dirId = target[:259]
for c in ["/","\\"," "]:
    if c in dirId:
        dirId = dirId.replace(c,"")

#Write a pid file
if not debug:
    writePid(dirId)

#Define logstash files
if logstashDir:
    logstashFiles = {'renamed':'renamed.txt',
                     'transferred':'transferred.txt',
                     'there_and_different':'there_and_different.txt',
                     'there_but_same':'there_but_same.txt',
                     'failed':'failed.txt',
                     'removed':'removed.txt',
                     'transfer_error':'transfer_errors.txt',}
    for lf in logstashFiles:
        logstashFiles[lf] = os.path.join(logstashDir,logstashFiles[lf])

def main():
    global ERRORS_FOUND
    global LOG_FILES

    #Any files which we would like to remove on scanning
    filesToDelete = ['._.DS_Store', '.DS_Store']

    #MAIN FUNCTION:
    for folder in swisspy.immediate_subdirs(toArchiveDir):
        deletedFiles = []

        if rename:
            if not renameLogDir:
                swisspy.print_and_log("Please specify a directory to log renamed" +\
                                  " files to (usually on dest.)",
                                  LOG_FILES, quiet=quiet)
                sys.exit(1)

            renameLogFile = os.path.join(renameLogDir, folder + ".txt")
        else:
            renameLogFile = ""

        folderStartPath = os.path.join(toArchiveDir, folder)
        #Check the directory to be copied isn't still being written to:
        if swisspy.dir_being_written_to(folderStartPath):
                swisspy.print_and_log(folder + " is being written to. Skipping this time.",
                                  [tempLogFile], ts="long", quiet=quiet)
                continue
        logFolder = os.path.join(illegalLogDir, folder)
        if not os.path.exists(logFolder):
            os.mkdir(logFolder)

        logPath =  os.path.abspath(os.path.join(logFolder, swisspy.time_stamp('short') + ".log"))
        #A list of files to be logged to
        LOG_FILES = [logPath[:259]] #Limit folder names to shorter than 260 chars

        swisspy.print_and_log("Processing " + folder + "\n", LOG_FILES, quiet=quiet)

        #Move everything to the hidden folder, unless it's already there, in which case move it to Problem Files
        if folder in swisspy.immediate_subdirs(theRoot):
            moveTo = os.path.join(problemDir, folder)
            swisspy.print_and_log(str(folder) + " is already being processed."
                                  "It has been moved to " + moveTo,
                                  LOG_FILES, quiet=quiet)
            shutil.move(folderStartPath, moveTo)
            continue

        else:
            shutil.move(folderStartPath, os.path.join(theRoot,folder))

        #Sanitise the directory itself, and update 'folder' if a change is made
        renameToClean(folder, theRoot, 'dir', renameLogFile)
        if sanitise(folder)['outString'] != folder:
            folder = sanitise(folder)['outString']
        targetPath = os.path.join(theRoot, folder)
        ERRORS_FOUND = False

        for thePath, theDirs, theFiles in os.walk(targetPath, topdown=False):
            #Sanitise file names
            for f in theFiles:
                renameToClean(f, thePath, 'file', renameLogFile)
                if f in filesToDelete:
                    fullPath = os.path.join(thePath,f)
                    try:
                        os.remove(fullPath)
                        deletedFiles.append(f)
                    except Exception as e:
                        swisspy.print_and_log("Unable to remove file " + f + '\n' +\
                                          "Error details: " + str(e) + '\n',
                                          LOG_FILES, quiet=quiet)
            #Sanitise directory names
            for d in theDirs:
                renameToClean(d, thePath, 'dir', renameLogFile)


        if not ERRORS_FOUND or rename:
            passFolder = os.path.join(passDir, folder)
            swisspy.print_and_log("Finished sanitising " + str(folder) +\
                              ". Moving to " + passDir + "\n",
                              LOG_FILES, quiet=quiet)
            moveAndMerge(targetPath, passFolder)

        else:
            try:
                shutil.move(targetPath, problemDir)
                swisspy.print_and_log ("{} has been moved to" \
                                   "{}.\n".format(folder, problemDir),
                                   LOG_FILES, quiet=quiet)

            except shutil.Error as e:
                swisspy.print_and_log ("Unable to move " + folder + " to " + problemDir + " - it may already exist in that location.\n" +\
                                   "If you need to archive a changed version of this file, please rename it appropriately and retry.\n" +\
                                   "Error: " + str(e) + ")\n",
                                   LOG_FILES, quiet=quiet)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        try:
            with open(os.path.join(logstashDir,"errors.txt"), 'a') as error_file:
                swisspy.print_and_log("\nError encountered: " +  str(e),
                                      log_files=[error_file], quiet=False)
        except IOError:
            print "Couldn't open /var/log/sanitisePathsSysLogs/errors.txt"
        raise