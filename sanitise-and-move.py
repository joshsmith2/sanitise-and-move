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
TO_ARCHIVE_DIR = "./To Archive"
PASS_DIR =  "./Passed_For_Archive"
ILLEGAL_LOG_DIR = "./Logs"
PROBLEM_DIR = "./Problem Files"
HIDDEN_DIR = "./.Hidden"
TRANSFER_ERROR_DIR=os.path.join(PROBLEM_DIR,"_Transfer_Errors")

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

def clean_up(pid_file, log_file):
    """Run some cleanup tasks on unexpected exit"""
    purge_hidden_dir()
    #Close pid files, if they exist
    try:
        os.remove(pid_file)
    except OSError as e:
        if e.errno == 2:
            #Pidfile doesn't exist.
            pass
        else:
            raise

def log_list(human_header,  the_list,
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

def move_and_create(source,dest):
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

def path_join(path1, path2):
    """Returns a properly formatted path with extraneous backslashes removed
    consisting of a concatenation of path1 and path2

    """
    return os.path.abspath(swisspy.unescape(swisspy.prepend(path1, path2)))

def purge_hidden_dir():
    """Move all files back out of .Hidden and into PROBLEM_DIR"""
    for o in swisspy.immediate_subdirs(HIDDEN_DIR):
        # If any file in .Hidden is already in problemFolder,
        # move it to a new timestamped folder to avoid overwriting.
        if os.path.exists(os.path.join(PROBLEM_DIR, o)):
            moved_to = os.path.join(PROBLEM_DIR, "Duplicates_" + swisspy.time_stamp('short'))
            os.mkdir(moved_to)
            # Removed 'try' here
            swisspy.print_and_log(str(o) + " has been moved to " + str(moved_to) + "/" + str(o) + \
                              ".\n                      " + \
                              "Please move or delete the folder from this " + \
                              "location once it is no longer required.\n",
                              LOG_FILES, quiet=QUIET)

# Should never need to do this
#            except ValueError as e:
#                reopenedLogs=[open(os.path.abspath(f.name), 'a') for f in LOG_FILES]
#                swisspy.print_and_log(str(o) + " has been moved to " + str(moved_to) + "/" + str(o) + \
#                                  ".\nPlease move or delete the folder from " +\
#                                  "this location once it is no longer required.\n",
#                                  reopenedLogs, quiet=QUIET)
        else:
            moved_to = PROBLEM_DIR
        try:
            shutil.move(os.path.join(HIDDEN_DIR, o), moved_to)
        except OSError as e:
            swisspy.print_and_log("Error occurred when moving " + HIDDEN_DIR + "/" +\
                              o + ": " + str(e) + "\n", LOG_FILES, quiet=QUIET)

def rename_file(path_dict, prev_path, rename_log_file, rename=False, indicator='^',):
    """Renames a file, or logs its abberations

    path_dict : dict
        A dictionary as output by sanitise():
        {'result': The sanitised string,
         'subs_made': Any characters which were removed or substituted
         'positions': the positions of the chars in subs_made}
    prev_path : str : path
        The original path to the file
    rename : bool
        If True, rename the file; otherwise just log.
    indicator : str
        Used in logging to indicate positions of changed characters

    """
    prev_root = os.path.dirname(prev_path)
    new_path = os.path.join(prev_root, path_dict['out_string'])
    #Work out where the changed characters are in the full string, as opposed
    #to just the basename. Strip the path the the hidden dir off this.
    positions_in_path = [p + len(prev_root) - len(HIDDEN_DIR) for p in path_dict['positions']]
    #Strip the path of the hidden dir out of the string to be logged
    #The '+1' here deals with the first forward slash
    path_to_log = prev_path[len(HIDDEN_DIR) + 1:]
    new_path_to_log = new_path[len(HIDDEN_DIR) + 1:]
    #Construct indicator string (shows where offending characters are)
    ind_list = []
    for i in range(len(path_to_log)):
        if i in positions_in_path:
            ind_list.append(indicator)
        else:
            ind_list.append(" ")
    ind_line = ''.join(ind_list)

    if rename:
        try:
            shutil.move(prev_path, new_path)
            # Log the renamed file in human readable format, on the SAN if
            # a rename log file has been defined...
            change_log_files = LOG_FILES[:]
            if rename_log_file:
                change_log_files.append(rename_log_file)

            swisspy.print_and_log("Changed from: " + path_to_log + '\n' +\
                              "Changed to:   " + new_path_to_log + '\n\n',
                               change_log_files, ts="long", quiet=QUIET)
            # ...and for logstash.
            if LOGSTASH_DIR:
                with open(logstash_files['renamed'], 'a') as lsf:
                    lsf.write("{Changed from: }" + prev_path +\
                              "{to: }" + new_path + '\n')
        except OSError:
            swisspy.print_and_log("Error: unable to rename " + prev_path + '\n',
                               LOG_FILES, ts="long", quiet=QUIET)
    else:
        # Add the clean path to a list of changed files,
        # so that logging without changing works correctly
        SANITISED_LIST.append(new_path)
        if path_dict['subs_made']:
            swisspy.print_and_log("Illegal characters found in file   : " +\
                               path_to_log + '\n',
                               LOG_FILES, ts=None, quiet=QUIET)
            swisspy.print_and_log("At these positions                 : " +\
                               ind_line + '\n',
                               LOG_FILES, ts=None, quiet=QUIET)
            swisspy.print_and_log("Characters found (comma separated) : " +\
                               ', '.join(path_dict['subs_made']) + '\n',
                               LOG_FILES, ts=None, quiet=QUIET)
            swisspy.print_and_log("Suggested change                   : " +\
                               new_path_to_log + '\n\n',
                               LOG_FILES, ts=None, quiet=QUIET)

def retry_wrapper(ERROR_LIST):
    """Iterate through ERROR_LIST, retrying the transfer of any failed files"""
    if ERROR_LIST:
        for e in ERROR_LIST:
            source_path = e[0]
            dest_path = e[1]
            new_errors = retry_transfer(source_path, dest_path, ERROR_LIST)
            return new_errors

def retry_transfer(src,dest,errors):
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
                                  LOG_FILES, quiet=QUIET)
            else:
                swisspy.print_and_log("File does not exist at " + src + " or " + dest + \
                                  "\nError: " + str(e) + "\n",
                                  LOG_FILES, quiet=QUIET)
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

def rename_to_clean(obj, path, obj_type, rename_log_file):
    """If path contains any forbidden characters, sanitise it and rename it.

    obj : str
        Name of the file or directory object to be sanitised.
    path : str : path
        Basename to obj - path at which it is located.
    obj_type : str : 'file', 'dir'
        The type of the object to be sanitised ('file' or 'dir')
    rename_log_file : str : path
        Path to the file in which to log renamed objects.

    """
    global ERRORS_FOUND
    full_path = os.path.join(path, obj)
    clean_path = full_path
    clean_dict = sanitise(obj)

    #If sanitising made any difference, there will be entries in subMade
    if clean_dict['subs_made']:
        #Check for strings prefixed with '.', remove this character, and replace it after file renaming.
        ERRORS_FOUND = True
        prefix = ""
        if clean_dict['out_string'][:1] == '.':
            prefix = '.'
            clean_dict['out_string'] = clean_dict['out_string'][1:]
        #Separate filename from extension:
        clean_split = clean_dict['out_string'].split('.')
        #For files and directories which were only composed of illegal characters, rename these 'Renamed file' or 'Renamed Folder'
        if clean_split[0].strip() == '':
            if obj_type == 'file':
                clean_dict['out_string'] = 'Renamed File' + clean_dict['out_string'][len(clean_split[0]):]
            elif obj_type == 'dir':
                clean_dict['out_string'] = 'Renamed Folder'
        #Replace any previously removed periods
        clean_dict['out_string'] = prefix + clean_dict['out_string']
        clean_path = os.path.join(path, clean_dict['out_string'])
        #If the clean path already exists, append '(n)' to the filename
        if os.path.exists(clean_path) or clean_path in SANITISED_LIST:
            clean_path = swisspy.append_index(clean_split[0], clean_dict['out_string'][len(clean_split[0]):], path)
        #Set the newly constructed path as the clean path to use
        clean_dict['out_string'] = clean_path
        rename_file(clean_dict, full_path, rename_log_file, RENAME)
    # If the cleaned and original versions are the same, check that there's no
    # case clash with a previously seen file
    else:
        if CASE_SENS:
            extension = ""
            if full_path.lower() in L_CASE_LIST:
                filename = full_path.split('/')[-1]
                if "." in filename:
                    extension = "." + filename.split(".")[-1]
                    filename = filename[:-len(extension)]
                clean_path = swisspy.append_index(filename, extension, path)
                rename_file(clean_dict, full_path, rename_log_file, RENAME)

    # Append the clean (i.e final) path to the array which will allow us to
    # check for case sensitive clashes, if the case sensitive option is set.
    if CASE_SENS:
        L_CASE_LIST.append(clean_path.lower())
    if OVERSIZE_LOG_FILE_NAME is not None:
        if len(full_path) > 254:
            if not QUIET:
                print swisspy.time_stamp() + "--WARNING-- Overlong directory found: " + clean_path + \
                      " is " + str(len(clean_path)) + " characters long.\n"
            if OVERSIZE_LOG_FILE_NAME is not None:
                oversize_file.write(swisspy.time_stamp() + "Oversize directory: " + clean_path + "\n")
                oversize_file.write(str(len(clean_path)) + " characters long.\n\n")

def sanitise(in_string):
    """Remove any occurrences of characters found in black_list from theString,
    except ':' which, for legibility, are changed to '-'

    Returns a dictionary consisting of the return string, a list of characters
    substituted, and their positions

    in_string : str
        The string to be processed

    """
    black_list = '' #Delete these characters. Currently empty.
    replace_list = [(':','-'), ('`','_'), ('\\','_'), ('/','_'), ('?','_'),
                   ('"','_'), ('<','_'), ('>','-'), ('|','_'), ('*','_')]
    subs_made = set() #Any characters which have been substituted. Here to catch ':'
    positions = []
    out_strings = []

    """Go through the input string character by character,
    constructing on output list which can be joined to form out output.
    This meticulous approach allows us to identify
    which characters were exchanged, and where. """
    for n, char in enumerate(in_string):
        to_append = char
        #Remove characters from the blacklist
        if char in black_list:
            subs_made.add(char)
            positions.append(n)
            to_append = ''
        #Substitute any non-space whitespace with spaces
        if char in whitespace and char != " ":
            subs_made.add("Whitespace(" + repr(char) + ")")
            positions.append(n)
            to_append = ' '
        #Make any replacements (e.g ':' for '-')
        for rl in replace_list:
            replace_in = rl[0]
            replace_out = rl[1]
            if char == replace_in:
                subs_made.add(char)
                positions.append(n)
                to_append = replace_out
        out_strings.append(to_append)
    out_string = ''.join(out_strings)
    return {'out_string':out_string, 'subs_made':subs_made, 'positions':positions}

def usage():
        print ("sanitise-and-move : A utility to facilitate cross-platform "\
               "file transfers, by dealing with illegal characters in a "\
               "sensible way. Developed by Josh Smith (joshsmith2@gmail.com)")
        print ("\nUsage:")
        print ("   -c, --casesensitive: For use on case sensitive filesystems Default - off.")
        print ("   -d, --dorename:      Actually rename the files - otherwise just log and output to standard output.")
        print ("   -h, --help:          Print this help and exit.")
        print ("   -l  --LOGSTASH_DIR:   A directory on the archive box containing a set of files sent by rsyslog to logstash.")
        print ("   -r  --RENAME_LOG_DIR:  Directory, usually on the destination, for logs of files which have been renamed to be stored.")
        print ("   -o, --oversizelog:   Log to write files with overlong path names in - otherwise don't log.")
        print ("   -p, --passdir:       Directory to which clean files should be moved.")
        print ("   -q, --QUIET:         Don't output to standard out.")
        print ("   -t, --target:        The location of the hot folder")
        print ("   --temp-log-file:     A file to write log information to\n")

def write_pid(dir_id):
    """Write PID file to prevent multiple syncronously running instances of the
    program.

    """
    pid_file = "/tmp/SanitisePaths" + dir_id + ".pid"
    if os.path.isfile(pid_file):
        with open(pid_file, 'r') as pf:
            existing_pid = pf.read()
            try:
                if swisspy.check_pid(existing_pid):
                    swisspy.print_and_log("Process with pid " + existing_pid +\
                                      " is currently running. Exiting now.\n",
                                      [TEMP_LOG_FILE], ts='long', quiet=False)
                    sys.exit()
                else:
                    swisspy.print_and_log("Removing stale pidfile\n",
                                      [TEMP_LOG_FILE], ts='long', quiet=False)
                    os.remove(pid_file)
            except OSError as e:
                swisspy.print_and_log("Process could not be checked. Error: " +\
                                  str(e) + "\n",
                                  [TEMP_LOG_FILE], ts='long', quiet=False)

    else:
        pf = open(pid_file, 'w')
        pf.write(str(os.getpid()))
    atexit.register(clean_up, pid_file=pid_file, log_file=LOG_FILE)

def strip_hidden(from_list, to_remove=os.path.abspath(HIDDEN_DIR)):
    """Given a lost of files, remove a given common path from them - in this
     case, the path to the hidden directory.

    from_list : list : strings : paths
        The list of paths to be stripped
    to_remove :
        The common path to be removed

    """
    return [f[len(to_remove):] for f in from_list]

def move_and_merge(source, dest, retry=3):
    """Copy source to dest, merging child folders which already exist in dest,
    but erroring on any files which already exist there.

    source : str : path
        The source of the files
    dest : str : path
        The destination
    retry : int
        How many times to retry failed transfers
    """
    existing_differing_files = [] #Files which already exist in dest, and differ from any uploaded files with the same name. If this is not empty by the end of the walk, source will not be copied
    existing_same_files = [] #Files which exist in the destination but have the same modification time and size as the file to be moved.
    cleared_for_copy = [] # Array of directories which can safely be copied as long as no clashes are found. Returned if and only if existing_differing_files is empty.
    copied_files = [] # Array of files which made it.
    ERROR_LIST = []
    empty_dirs = []
    #TODO: Put the variables above into the docstring
    source_to_log = source.split('/')[-1]
    prefix = source[:-len(source_to_log)]

    #Check source itself before walking
    if not os.path.exists(dest):
        try:
            shutil.move(source, dest)
            swisspy.print_and_log ("No errors found in new folder " + source_to_log + ". " +\
                               "Folder moved to " + dest + "\n",
                               LOG_FILES, quiet=QUIET)
        except shutil.Error as e:
            ERROR_LIST.append(e)
            swisspy.print_and_log ("One or more files failed while trying " +\
                               "to move " + source_to_log + " to " + dest +\
                               ". This folder has been moved to the " +\
                               "'Problem Files' directory.\n" +\
                               "Error: \n " + str(e) + "\n",
                               LOG_FILES, quiet=QUIET)
        #Walk to get list of files moved
        swisspy.print_and_log("Walking destination to get list " +\
                          "of transferred files.\n",
                          LOG_FILES, quiet=QUIET)
        for root, dirs, files in os.walk(dest):
            for f in files:
                 copied_files.append(os.path.join(root,f))
    else:
        swisspy.print_and_log("Examining " + dest + " for existing files\n",
                          LOG_FILES, quiet=QUIET)
        for root, dirs, files in os.walk(source):
            #Starting from the deepest file,
            for f in files:
                source_file = File(path=os.path.join(root,f))
                path_after_source = source_file.path[len(source)+1:]
                dest_file = File(path=os.path.join(dest, path_after_source))
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
                        existing_same_files.append(source_file)
                    else:
                        if source_file.size != dest_file.size:
                            existing_differing_files.append((source_file,
                                                           dest_file))
                        elif source_file.m_time != dest_file.m_time:
                            source_file.md5 = swisspy.get_md5(source_file.path)
                            dest_file.md5 = swisspy.get_md5(dest_file.path)
                            if source_file.md5 != dest_file.md5:
                                existing_differing_files.append((source_file,
                                                               dest_file))
                            else:
                                existing_same_files.append(source_file)
                else:
                    cleared_for_copy.append(source_file.path)

            for d in dirs:
                dir = os.path.join(root,d)
                after_source = dir[len(source)+1:]
                if not os.path.exists(os.path.join(dest, after_source)):
                    cleared_for_copy.append(dir)
                    #Remove this directory from the list of dirs to be walked
                    dirs.remove(d)

        if existing_differing_files:
            file_reports=[]
            file_no = 1
            for edf in existing_differing_files:
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
            log_list("Unable to move {0}. The following {1} files already " \
                    "exist in {2}: \n".format(source,
                                              len(existing_differing_files),
                                              dest),
                    file_reports,
                    log_files=LOG_FILES,
                    #TODO: Put syslog files in here, into [there_and_different]
                    )
            purge_hidden_dir()
            swisspy.print_and_log("Please version these files " +\
                              "and attempt the upload again.\n",
                              LOG_FILES, quiet=QUIET)
        else:
            if cleared_for_copy:
                swisspy.print_and_log("Moving files cleared for copy\n\t" +\
                                  "Files transferred:\n",
                                  LOG_FILES, quiet=QUIET)
                for c in cleared_for_copy:
                    target = os.path.join(dest,c)
                    try:
                        shutil.move(c, target)
                        copied_files.append(c)
                        swisspy.print_and_log("\t" + c + "\n",
                                          LOG_FILES, ts=None, quiet=QUIET)
                    except shutil.Error as e:
                        ERROR_LIST.append(e)

            if ERROR_LIST:
                log_list("An error occurred when moving some files to " + dest +\
                        ".\nError: ",
                        str(ERROR_LIST),
                        log_files=LOG_FILES,
                        syslog_files=[logstash_files['failed']])
            else:
                swisspy.print_and_log("No transfer errors occurred. " +\
                                  "Folder exists at " + dest + "\n\t",
                                  LOG_FILES, quiet=QUIET)
    if ERROR_LIST:
        error= chain(ERROR_LIST).next().args[0]
        all_sources = [e[0] for e in error]
        success = False

        abiding_errors = error
        abiding_sources = all_sources

        for i in range(retry):
            swisspy.print_and_log("\nTry no. " + str(i + 1) + ': ' +\
                              "Retrying files\n\t" +\
                              '\n\t'.join(strip_hidden(abiding_sources, prefix)) + '\n',
                              LOG_FILES, quiet=QUIET)

            retry_errors = retry_wrapper(abiding_errors)
            if retry_errors:
                abiding_errors = retry_errors
                abiding_sources = [e[0] for e in abiding_errors]
            else:
                swisspy.print_and_log("Transfer of files\n\t" +\
                                  '\n\t'.join(all_sources) + "\ncompleted on "+\
                                  "try " + str(i + 1) + ".\n",
                                  LOG_FILES, quiet=QUIET)
                copied_files.extend(all_sources)
                success=True
                break

        if not success:
            log_list("The following files failed to transfer, and have been moved to " +\
                    os.path.abspath(TRANSFER_ERROR_DIR) + ".\n" +\
                    "These files can be resubmitted by placing them in \n\t" +\
                    TO_ARCHIVE_DIR + ".\n"
                    "If there is still a directory corresponding to the copied " +\
                    "project in 'Problem Files', these files will no longer " +\
                    "be contained within it.\nIf you would like to recombine " +\
                    "the project without resubmitting it, copy the files " +\
                    "in \n\t" + TRANSFER_ERROR_DIR + "\n into the project folder " +\
                    "in \n\t" + PROBLEM_DIR +\
                    ", choose 'merge' in the dialogue box which appears, " +\
                    "and delete the folder in " + TRANSFER_ERROR_DIR + ".",
                    strip_hidden(abiding_sources, prefix),
                    syslog_header="{MovedTo:}" + os.path.abspath(TRANSFER_ERROR_DIR),
                    log_files=LOG_FILES,
                    syslog_files=[logstash_files['transfer_error']]
                    )

            #Move errored files to TRANSFER_ERROR_DIR
            for f in abiding_sources:
                file_path_start = len(os.path.abspath(HIDDEN_DIR))
                file_path = os.path.abspath(f)[file_path_start + 1:]
                move_to = os.path.abspath(os.path.join(TRANSFER_ERROR_DIR, file_path))
                move_and_create(f,move_to)

    if copied_files:
        log_list("The following files transferred successfully: \n\t",
                copied_files,
                log_files=LOG_FILES,
                syslog_files=[logstash_files['transferred']]
        )

    if existing_same_files:
        log_list("The following files already have up to date copies" + \
                " in the archive, and were therefore not transferred:",
                strip_hidden([e.path for e in existing_same_files], prefix),
                log_files=LOG_FILES,
                syslog_files=[logstash_files['there_but_same']],
                )
        if not existing_differing_files:
            for esf in existing_same_files:
                try:
                    os.remove(esf.path)
                except Exception as e:
                    swisspy.print_and_log("Could not delete " + esf +\
                                     " due to the following error: " + str(e),
                                     LOG_FILES, quiet=QUIET)

            #Walk the remaining files from the bottom, removing empty directories:
            for root, dirs, files in os.walk(source,topdown=False):
                empty_dirs.append(root)
                os.rmdir(root)
            swisspy.print_and_log("Removed the following empty directories:\n\t" +\
                              '\n\t'.join(strip_hidden(empty_dirs, prefix)) + '\n')

#Initialise command line options
try:
    opts, args = getopt.getopt(sys.argv[1:],
                               "r:l:o:t:p:qdhcx",
                               ["RENAME_LOG_DIR=","LOGSTASH_DIR=","oversizelog=",
                                "target=","passdir=","QUIET","dorename",
                                "help","casesensitive","DEBUG",
                                "temp-log-file",]
                              )

except getopt.GetoptError as err:
        # print help information and exit:
        usage()
        print str(err) # will print something like "option -a not recognized"
        sys.exit(2)

SANITISED_LIST = []
ERROR_LIST = []
L_CASE_LIST = []
LOG_FILES = []

#Argument variables
CASE_SENS = False
DEBUG = False #NB - this variable used only during development, so not in the --help.
ERRORS_FOUND = False
ERROR_LOG_FILE_NAME = None
LOG_FILE = None
LOCATION = None
LOGSTASH_DIR = None
OLD_PATH = ""
OVERSIZE_LOG_FILE_NAME = None
QUIET = False
RENAME = False
RENAME_LOG_DIR = None
TARGET = TO_ARCHIVE_DIR
TEMP_LOG_FILE = open ("/tmp/saniTempLog.log", 'a')
THE_ROOT = HIDDEN_DIR

for o, a in opts:
        if o in ("-d","--dorename"):
            RENAME = True
        elif o in ("-h","--help"):
            usage()
            sys.exit(2)
        elif o in ("-q","--QUIET"):
            QUIET = True
        elif o in ("-o","--oversizelog"):
            OVERSIZE_LOG_FILE_NAME = a
            oversize_out = os.path.abspath(OVERSIZE_LOG_FILE_NAME)
            oversize_file = open (oversize_out, 'a')
        elif o == "--temp-log-file":
            TEMP_LOG_FILE = open(os.path.abspath(a), 'a')
        elif o == "--DEBUG":
            DEBUG = True
        elif o in ("-c", "--casesensitive"):
            CASE_SENS = True
        elif o in ("-p", "--passdir"):
            PASS_DIR = a
        elif o in ("-x", "--PROBLEM_DIR"):
            PROBLEM_DIR = a
        elif o in ("-l", "--logstashdir"):
            LOGSTASH_DIR = os.path.abspath(a)
        elif o in ("-r", "--renamelogdir"):
            RENAME_LOG_DIR = os.path.abspath(a)
        elif o in ("-t", "--target"):
            TARGET = a
            THE_ROOT = path_join(TARGET, THE_ROOT)
            ILLEGAL_LOG_DIR = path_join(TARGET, ILLEGAL_LOG_DIR)
            PASS_DIR = path_join(TARGET, PASS_DIR)
            PROBLEM_DIR = path_join(TARGET, PROBLEM_DIR)
            TO_ARCHIVE_DIR = path_join(TARGET, TO_ARCHIVE_DIR)
            HIDDEN_DIR = path_join(TARGET, HIDDEN_DIR)
            TRANSFER_ERROR_DIR=os.path.join(PROBLEM_DIR,"_Transfer_Errors")

#Construct a directory id for use in PID and log files
dir_id = TARGET[:259]
for c in ["/","\\"," "]:
    if c in dir_id:
        dir_id = dir_id.replace(c,"")

#Write a pid file
if not DEBUG:
    write_pid(dir_id)

#Define logstash files
if LOGSTASH_DIR:
    logstash_files = {'renamed':'renamed.txt',
                     'transferred':'transferred.txt',
                     'there_and_different':'there_and_different.txt',
                     'there_but_same':'there_but_same.txt',
                     'failed':'failed.txt',
                     'removed':'removed.txt',
                     'transfer_error':'transfer_errors.txt',}
    for lf in logstash_files:
        logstash_files[lf] = os.path.join(LOGSTASH_DIR,logstash_files[lf])

def main():
    global ERRORS_FOUND
    global LOG_FILES

    #Any files which we would like to remove on scanning
    files_to_delete = ['._.DS_Store', '.DS_Store']

    #MAIN FUNCTION:
    for folder in swisspy.immediate_subdirs(TO_ARCHIVE_DIR):
        deleted_files = []

        if RENAME:
            if not RENAME_LOG_DIR:
                swisspy.print_and_log("Please specify a directory to log renamed" +\
                                  " files to (usually on dest.)",
                                  LOG_FILES, quiet=QUIET)
                sys.exit(1)

            rename_log_file = os.path.join(RENAME_LOG_DIR, folder + ".txt")
        else:
            rename_log_file = ""

        folder_start_path = os.path.join(TO_ARCHIVE_DIR, folder)
        #Check the directory to be copied isn't still being written to:
        if swisspy.dir_being_written_to(folder_start_path):
                swisspy.print_and_log(folder + " is being written to. Skipping this time.",
                                  [TEMP_LOG_FILE], ts="long", quiet=QUIET)
                continue
        log_folder = os.path.join(ILLEGAL_LOG_DIR, folder)
        if not os.path.exists(log_folder):
            os.mkdir(log_folder)

        log_path =  os.path.abspath(os.path.join(log_folder, swisspy.time_stamp('short') + ".log"))
        #A list of files to be logged to
        LOG_FILES = [log_path[:259]] #Limit folder names to shorter than 260 chars

        swisspy.print_and_log("Processing " + folder + "\n", LOG_FILES, quiet=QUIET)

        #Move everything to the hidden folder, unless it's already there, in which case move it to Problem Files
        if folder in swisspy.immediate_subdirs(THE_ROOT):
            move_to = os.path.join(PROBLEM_DIR, folder)
            swisspy.print_and_log(str(folder) + " is already being processed."
                                  "It has been moved to " + move_to,
                                  LOG_FILES, quiet=QUIET)
            shutil.move(folder_start_path, move_to)
            continue

        else:
            shutil.move(folder_start_path, os.path.join(THE_ROOT,folder))

        #Sanitise the directory itself, and update 'folder' if a change is made
        rename_to_clean(folder, THE_ROOT, 'dir', rename_log_file)
        if sanitise(folder)['out_string'] != folder:
            folder = sanitise(folder)['out_string']
        target_path = os.path.join(THE_ROOT, folder)
        ERRORS_FOUND = False

        for the_path, the_dirs, the_files in os.walk(target_path, topdown=False):
            #Sanitise file names
            for f in the_files:
                rename_to_clean(f, the_path, 'file', rename_log_file)
                if f in files_to_delete:
                    full_path = os.path.join(the_path,f)
                    try:
                        os.remove(full_path)
                        deleted_files.append(f)
                    except Exception as e:
                        swisspy.print_and_log("Unable to remove file " + f + '\n' +\
                                             "Error details: " + str(e) + '\n',
                                             LOG_FILES, quiet=QUIET)
            #Sanitise directory names
            for d in the_dirs:
                rename_to_clean(d, the_path, 'dir', rename_log_file)


        if not ERRORS_FOUND or RENAME:
            passFolder = os.path.join(PASS_DIR, folder)
            swisspy.print_and_log("Finished sanitising " + str(folder) +\
                              ". Moving to " + PASS_DIR + "\n",
                              LOG_FILES, quiet=QUIET)
            move_and_merge(target_path, passFolder)

        else:
            try:
                shutil.move(target_path, PROBLEM_DIR)
                swisspy.print_and_log ("{} has been moved to" \
                                   "{}.\n".format(folder, PROBLEM_DIR),
                                   LOG_FILES, quiet=QUIET)

            except shutil.Error as e:
                swisspy.print_and_log ("Unable to move " + folder + " to " + PROBLEM_DIR + " - it may already exist in that location.\n" +\
                                   "If you need to archive a changed version of this file, please rename it appropriately and retry.\n" +\
                                   "Error: " + str(e) + ")\n",
                                   LOG_FILES, quiet=QUIET)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        try:
            with open(os.path.join(LOGSTASH_DIR,"errors.txt"), 'a') as error_file:
                swisspy.print_and_log("\nError encountered: " +  str(e),
                                      log_files=[error_file], quiet=False)
        except IOError:
            print "Couldn't open /var/log/sanitisePathsSysLogs/errors.txt"
        raise