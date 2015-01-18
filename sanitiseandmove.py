#!/usr/bin/env python2.6
"""
Search for characters in filenames which are illegal in Windows. Either log or
remove these.

Designed as part of Hogarth's archiving procedure.

Author: Josh Smith
Contact: joshsmith2@gmail.com

"""


#FORMATTING:
#TODO: Line lengths
#TODO: Change the_root to hidden?

import atexit
import os
import os.path
import shutil
import sys
import swisspy
from itertools import chain
import subprocess as sp
import argparse
from string import whitespace
from threading import Event
from time import ctime

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
        self.m_time_secs = m_time
        self.md5 = md5

        self.modification_time = None
        if self.m_time_secs:
            self.modification_time = ctime(m_time)

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
        swisspy.print_and_log(human_header + log_split +
                              log_split.join(the_list) + "\n",
                              log_files=log_files)
    if syslog_files:
        headedList = [syslog_header + l for l in the_list]
        swisspy.print_and_log(syslog_split.join(headedList) + syslog_split,
                              syslog_files=syslog_files,
                              quiet=True, ts=None)

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

def sanitise(in_string, strip_trailing_spaces=True):
    """Remove any occurrences of characters found in black_list from theString,
    except ':' which, for legibility, are changed to '-'

    Returns a dictionary consisting of the return string, a list of characters
    substituted, and their positions

    in_string : str
        The string to be processed
    strip_trailing_spaces : Bool
        If true, remove any number of trailing spaces from the end of the string.
    """
    black_list = '' #Delete these characters. Currently empty.
    replace_list = [(':','-'), ('`','_'), ('\\','_'), ('/','_'), ('?','_'),
                   ('"','_'), ('<','_'), ('>','-'), ('|','_'), ('*','_')]
    strip_from_end = [' '] # Strip any of these characters from the end of the string
    strip_count = 0
    strip_chars_found = []
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
        if to_append in strip_from_end:
            strip_count += 1
            strip_chars_found.append(char)
        else:
            strip_count = 0
            strip_chars_found = []
        out_strings.append(to_append)
    out_string = ''.join(out_strings)
    #If we've found any characters to strip, remove these from the end of the string.
    if strip_count > 0:
        out_string = out_string[:-strip_count]
        for scf in strip_chars_found:
            subs_made.add(scf)
        for r in range(strip_count):
            positions.append(len(in_string) - r - 1)
    return {'out_string':out_string,
            'subs_made':subs_made,
            'positions':positions}

def get_arguments():
    """Return command line arguments from argparse"""
    blurb = "sanitise-and-move : A utility to facilitate cross-platform "\
            "file transfers, by dealing with illegal characters in a "\
            "sensible way. Developed by Josh Smith (joshsmith2@gmail.com)"
    p = argparse.ArgumentParser(description=blurb)
    p.add_argument('-c','--casesensitive', dest='casesensitive',
                   action='store_true', default=False,
                   help="For use on case sensitive filesystems Default - off.")
    p.add_argument('-d','--dorename', dest='dorename',
                   action='store_true', default=False,
                   help="Actually rename the files - otherwise just log "
                        "and output to standard output.")
    p.add_argument('-l','--logstash_dir', dest='logstash_dir', metavar="PATH",
                   help="A directory on the archive box containing a set of "
                        "files sent by rsyslog to logstash.")
    p.add_argument('-r','--rename_log_dir', dest='rename_log_dir',
                   metavar="PATH",
                   help="Directory, usually on the destination, for logs of "
                        "files which have been renamed to be stored.")
    p.add_argument('-o','--oversizelog', dest='oversizelog', metavar="PATH",
                   help="Log to write files with overlong path names in - "
                        "otherwise don't log.")
    p.add_argument('-p','--passdir', dest='passdir', metavar="PATH",
                   help="Directory to which clean files should be moved.")
    p.add_argument('-q','--quiet', dest='quiet', action='store_true',
                   default=False,
                   help="Don't output to standard out")
    p.add_argument('-t','--target', dest='target', metavar='PATH',
                   help="The location of the hot folder.")
    p.add_argument('--temp-log-file', dest='temp_log_file', metavar='PATH',
                   default="/tmp/saniTempLog.log",
                   help="A file to write temporary log information to.")
    p.add_argument('--trust-source', dest='trust_source', action='store_true',
                   default=False, help="Transfer all files from source "
                                       "regardless of mod time. Use with caution.")
    #TODO: What does this store?
    return p.parse_args()

class Sanitisation:
    """This is the parent object, containing variables for the sanitisation,
    which will be referred to throughout in order to avoid passing global
    variables around.
    """

    def __init__(self, pass_dir, case_sens=False,
                 error_log_file_name = None, log_file=None, location=None,
                 logstash_dir='/var/log/sanitisePathsSysLogs', oversize_log_file_name=None, quiet=False,
                 rename=False, rename_log_dir=None,
                 temp_log_file="/tmp/saniTempLog.log",
                 target='.', files_to_delete=['.DS_Store', '._.DS_Store'],
                 test_suite=False, create_pid=True,
                 trust_source=True):

        self.target = target

        # The standard folder structure within the hot folder
        dirs = {'to_archive': os.path.join(self.target, "To Archive"),
                'log': os.path.join(self.target, "Logs"),
                'problem': os.path.join(self.target, "Problem Files"),
                'hidden': os.path.join(self.target, ".Hidden"),
                'pass': os.path.join(self.target, "Passed_For_Archive"), # TODO: Really?
                 }

        self.logstash_dir = os.path.abspath(logstash_dir)
        #Define logstash files
        self.logstash_files = {'renamed':'renamed.txt',
                               'transferred':'transferred.txt',
                               'there_and_different':'there_and_different.txt',
                               'there_but_same':'there_but_same.txt',
                               'failed':'failed.txt',
                               'removed':'removed.txt',
                               'transfer_error':'transfer_errors.txt',}
        for lf in self.logstash_files:
            self.logstash_files[lf] = os.path.join(self.logstash_dir,
                                                   self.logstash_files[lf])

        #TODO: Variable descriptions

        # Attributes with set initial values
        self.error_list = []
        self.errors_found = False
        self.l_case_list = [] #See Sanitise
        self.log_files = []
        self.old_path = ''
        self.sanitised_list = []

        self.hidden_dir = dirs['hidden']
        self.illegal_log_dir = dirs['log'] #TODO: Really?
        self.problem_dir = dirs['problem']
        self.to_archive_dir = dirs['to_archive']
        self.transfer_error_dir = os.path.join(self.problem_dir,
                                               "_Transfer_Errors")
        self.files_to_delete = files_to_delete

        # Switches
        self.case_sens = case_sens
        self.quiet = quiet
        self.rename = rename
        self.test_suite = test_suite
        self.trust_source = trust_source

        # Paths - e.g to log files
        self.error_log_file_name = error_log_file_name
        self.log_file = log_file
        self.location = location
        self.pass_dir = pass_dir
        self.temp_log_file = os.path.abspath(temp_log_file)

        # Silly duplications. TODO: Get rid of these.
        self.the_root = self.hidden_dir
        if oversize_log_file_name:
            oversize_log_file_name = os.path.abspath(oversize_log_file_name)
        if rename_log_dir:
            rename_log_dir = os.path.abspath(rename_log_dir)

        self.oversize_log_file_name = oversize_log_file_name
        self.rename_log_dir = rename_log_dir

        #Create a sanitised, short dir_id for use in log and PID files
        self.dir_id = self.target[:256]
        for c in ["/", "\\", " "]:
            if c in self.dir_id:
                self.dir_id = self.dir_id.replace(c,"")
        self.pid_file = "/tmp/SanitisePaths" + self.dir_id + ".pid"

        # Register functions to run on exit
        atexit.register(self.clean_up)

        # Set events to pass to other threads
        self.started_transfer = Event()

        self.create_pid = create_pid

    def clean_up(self):
        """Run some cleanup tasks on unexpected exit"""
        self.started_transfer.clear()
        #Close pid files, if they exist
        try:
            self.purge_hidden_dir()
            os.remove(self.pid_file)
        except OSError as e:
            if e.errno == 2:
                #Pidfile doesn't exist.
                pass
            else:
                raise

    def rename_to_clean(self, obj, path, obj_type, rename_log_file):
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
        full_path = os.path.join(path, obj)
        clean_path = full_path
        clean_dict = sanitise(obj)

        #If sanitising made any difference, there will be entries in subMade
        if clean_dict['subs_made']:
            #Check for strings prefixed with '.', remove this character, and replace it after file renaming.
            self.errors_found = True
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
            if os.path.exists(clean_path) or \
            clean_path in self.sanitised_list:
                clean_path = swisspy.append_index(clean_split[0],
                                                  clean_dict['out_string'][len(clean_split[0]):],
                                                  path)
            #Set the newly constructed path as the clean path to use
            clean_dict['out_string'] = os.path.basename(clean_path)
            self.rename_file(clean_dict, full_path, rename_log_file,
                             self.rename)
        # If the cleaned and original versions are the same, check that there's no
        # case clash with a previously seen file
        else:
            if self.case_sens:
                extension = ""
                if full_path.lower() in self.l_case_list:
                    filename = full_path.split('/')[-1]
                    if "." in filename:
                        extension = "." + filename.split(".")[-1]
                        filename = filename[:-len(extension)]
                    clean_path = swisspy.append_index(filename, extension, path)
                    self.rename_file(clean_dict, full_path,
                                     rename_log_file, self.rename)

        # Append the clean (i.e final) path to the array which will allow us to
        # check for case sensitive clashes, if the case sensitive option is set.
        if self.case_sens:
            self.l_case_list.append(clean_path.lower())
        if self.oversize_log_file_name is not None:
            if len(full_path) > 254:
                log_to = self.log_files
                log_to.append(self.oversize_log_file_name)
                swisspy.print_and_log("Overlong directory found: {0} is {1}"
                                      " characters long.\n".format(clean_path,
                                                                   str(len(clean_path))),
                                      [log_to], quiet=self.quiet)

    def move_and_merge(self, source, dest, retry=3):
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
        different_but_trusted = []
        existing_same_files = [] #Files which exist in the destination but have the same modification time and size as the file to be moved.
        cleared_for_copy = [] # Array of directories which can safely be copied as long as no clashes are found. Returned if and only if existing_differing_files is empty.
        copied_files = [] # Array of files which made it.
        empty_dirs = []

        #TODO: Put the variables above into the docstring
        source_to_log = source.split('/')[-1]
        prefix = source[:-len(source_to_log)]

        #Check source itself before walking
        if not os.path.exists(dest):
            try:
                self.started_transfer.set()
                shutil.move(source, dest)
                msg = "No errors found in new folder {0}. Folder moved to" \
                      "{1}\n".format(source_to_log, dest)

                swisspy.print_and_log(msg, self.log_files,
                                      quiet=self.quiet)
            except shutil.Error as e:
                self.error_list.append(e)
                msg = "One or more files failed while trying to move {0} " \
                      "to {1}. This folder has been moved to {2}.\n" \
                      "Error:\n {3}".format(source_to_log, dest,
                                           self.problem_dir, e)
                swisspy.print_and_log(msg, self.log_files, quiet=self.quiet)
            #Walk to get list of files moved
            swisspy.print_and_log("Walking destination to get list " +\
                                  "of transferred files.\n",
                                  self.log_files, quiet=self.quiet)
            for root, dirs, files in os.walk(dest):
                for f in files:
                     copied_files.append(os.path.join(root,f))
        else:
            swisspy.print_and_log("Examining " + dest +
                                  " for existing files\n",
                                  self.log_files, quiet=self.quiet)
            for root, dirs, files in os.walk(source):
                #Starting from the deepest file
                for f in files:
                    source_file = File(path=os.path.join(root,f))
                    path_after_source = source_file.path[len(source)+1:]
                    dest_file = File(path=os.path.join(dest, path_after_source))
                    #If any file in source exists in dest, log this.
                    #Otherwise, add it to the 'cleared' list.
                    if os.path.exists(dest_file.path):
                        #Get attributes for source and dest files
                        source_file.size = os.path.getsize(source_file.path)
                        source_file.m_time_secs = os.path.getmtime(source_file.path)
                        source_file.modification_time = ctime(source_file.m_time_secs)

                        dest_file.size = os.path.getsize(dest_file.path)
                        dest_file.m_time_secs = os.path.getmtime(dest_file.path)
                        dest_file.modification_time = ctime(dest_file.m_time_secs)

                        # If size and mod time are the same, so are the files.
                        if source_file.size == dest_file.size and \
                           source_file.m_time_secs == dest_file.m_time_secs:
                            existing_same_files.append(source_file)
                        else:
                            if source_file.size < dest_file.size:
                                existing_differing_files.append((source_file,
                                                                 dest_file))

                            # If the sizes are different, so are the files.
                            if source_file.size >= dest_file.size:
                                if self.trust_source:
                                    different_but_trusted.append((source_file,
                                                                  dest_file))
                                    cleared_for_copy.append(source_file.path)
                                else:
                                    existing_differing_files.append((source_file,
                                                                     dest_file))

                            # If the sizes are the same, but m_time differs,
                            # do an md5 check. Skip if trust_source is on.
                            elif not self.trust_source:
                                if source_file.m_time_secs != dest_file.m_time_secs:
                                    source_file.md5 = swisspy.get_md5(source_file.path)
                                    dest_file.md5 = swisspy.get_md5(dest_file.path)
                                    # If the md5s differ, so do the files
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
                    header = "\n\tFile "+ str(file_no)
                    file_reports.append(header)
                    file_no += 1
                    #edf is a tuple of source and dest files, so:
                    for f in edf:
                        file_report = "\n\t{0}:".format(f.path)
                        for attr_name in ['size','modification_time','md5']:
                            attr_value = getattr(f,attr_name)
                            if attr_value:
                                file_report += "\n\t{0}: {1}".format(attr_name,
                                                                     attr_value)
                        file_reports.append(file_report)
                    file_reports.append("\n")

                message = "The following {0} files already exist in {1}; " \
                          "the transfer was unable to continue." \
                          "\n".format(len(existing_differing_files), dest)

                log_list(message, file_reports, log_files = self.log_files)
                        #TODO: Put syslog files in here, into [there_and_different]
                self.purge_hidden_dir()
                swisspy.print_and_log("Please version these files " +\
                                      "and attempt the upload again.\n",
                                      self.log_files, quiet=self.quiet)

            else: # Transfer can go ahead!
                if different_but_trusted:
                    file_reports = []
                    file_no = 1
                    for dbt in different_but_trusted:
                        header = "\n\tFile "+ str(file_no)
                        file_reports.append(header)
                        file_no += 1
                        for f in dbt:
                            file_report = "\n\t{0}:".format(f.path)
                            for attr_name in ['size','modification_time','md5']:
                                attr_value = getattr(f,attr_name)
                                if attr_value:
                                    file_report += "\n\t{0}: {1}".format(attr_name,
                                                                         attr_value)
                            file_reports.append(file_report)
                        file_reports.append("\n")

                    message = "The following {0} files already exist in {1}, but " \
                              "will be transferred since trust source is set." \
                              "\n".format(len(different_but_trusted), dest)
                    log_list(message, file_reports, log_files = self.log_files)

                if cleared_for_copy:
                    self.move_files(source, dest,
                                    cleared_for_copy, copied_files)

                if self.error_list:
                    log_list("An error occurred when moving some files to " \
                             " " + dest + ".\nError: ",
                             str(self.error_list),
                             log_files=self.log_files,
                             syslog_files=[self.logstash_files['failed']])
                else:
                    swisspy.print_and_log("No transfer errors occurred. " +\
                                          "Folder exists at " + dest + "\n\t",
                                          self.log_files, quiet=self.quiet)
        if self.error_list:
            error = chain(self.error_list).next().args[0]
            all_sources = [e[0] for e in error]
            success = False

            abiding_errors = error
            abiding_sources = all_sources

            for i in range(retry):
                msg = "\nTry no. {0}: Retrying files\n\t{1}" \
                      "\n".format(str(i + 1),
                                  '\n\t'.join(self.strip_hidden(abiding_sources,
                                                                prefix)))
                swisspy.print_and_log(msg, self.log_files, quiet=self.quiet)

                retry_errors = self.retry_wrapper()
                if retry_errors:
                    abiding_errors = retry_errors
                    abiding_sources = [e[0] for e in abiding_errors]
                else:
                    msg = "Transfer of files\n\t{0}\ncompleted on try{1}." \
                          "\n".format('\n\t'.join(all_sources),
                                      str(i + 1))
                    swisspy.print_and_log(msg, self.log_files,
                                          quiet=self.quiet)
                    copied_files.extend(all_sources)
                    success = True
                    break

            if not success:
                msg = "The following files failed to transfer, and have " \
                      "been moved to {edir}.\nThese files can be " \
                      "resubmitted by placing them in\n\t{tadir}\nIf " \
                      "there is still a directory corresponding to the " \
                      "copied project in 'Problem Files', these files " \
                      "will no longer be contained within it.\nIf you " \
                      "would like to recombine the project without " \
                      "resubmitting it, copy the files in\n\t{edir}\n " \
                      "into the project folder in\n\t{pdir}\n, choose " \
                      "'merge' in the dialogue box which appears, and " \
                      "delete the folder in {pdir}." \
                      "".format(edir=self.transfer_error_dir,
                                tadir=self.to_archive_dir,
                                pdir=self.problem_dir,)
                log_list(msg, self.strip_hidden(abiding_sources, prefix),
                        syslog_header="{MovedTo:}" + os.path.abspath(self.transfer_error_dir),
                        log_files=self.log_files,
                        syslog_files=[self.logstash_files['transfer_error']]
                        )

                #Move errored files to self.transfer_error_dir
                for f in abiding_sources:
                    file_path_start = len(os.path.abspath(self.hidden_dir))
                    file_path = os.path.abspath(f)[file_path_start + 1:]
                    move_to = os.path.join(self.transfer_error_dir,
                                           file_path)
                    move_and_create(f,move_to)

        if copied_files:
            log_list("The following files transferred successfully: \n\t",
                     copied_files,
                     log_files=self.log_files,
                     syslog_files=[self.logstash_files['transferred']])

        if existing_same_files:
            msg = "{0} files already have up-to-date copies in the archive, " \
                  "and were therefore not transferred."\
                  .format(len(existing_same_files))
            swisspy.print_and_log(msg, self.log_files, quiet=self.quiet)

            log_list("",
                     self.strip_hidden([e.path for e in existing_same_files], prefix),
                     log_files=[],
                     syslog_files=[self.logstash_files['there_but_same']],
                     )

            if not existing_differing_files:
                for esf in existing_same_files:
                    try:
                        os.remove(esf.path)
                    except Exception as e:
                        swisspy.print_and_log("Could not delete " + esf +\
                                              " due to the following error:"
                                              " " + str(e),
                                              self.log_files,
                                              quiet=self.quiet)

                # Walk the remaining files from the bottom,
                # removing empty directories:
                for root, dirs, files in os.walk(source,topdown=False):
                    empty_dirs.append(root)
                    os.rmdir(root)
                swisspy.print_and_log("Removed the following "
                                      "empty directories:\n\t{0}\n"
                                      "".format('\n\t'.join(self.strip_hidden(empty_dirs,
                                                                              prefix))))

    def purge_hidden_dir(self):
        """Move all files back out of .Hidden and into self.problem_dir"""
        for o in swisspy.immediate_subdirs(self.hidden_dir):
            # If any file in .Hidden is already in problemFolder,
            # move it to a new timestamped folder to avoid overwriting.
            if os.path.exists(os.path.join(self.problem_dir, o)):
                moved_to = os.path.join(self.problem_dir,
                                        "Duplicates_" + swisspy.time_stamp('short'))
                os.mkdir(moved_to)
                # Removed 'try' here
                msg = "{0} has been moved to {1}/{2}.\nPlease move or delete " \
                      "the folder from this lovcation once it is no longer " \
                      "required.\n".format(o, moved_to, o)
                swisspy.print_and_log(msg, self.log_files, quiet=self.quiet)
            else:
                moved_to = self.problem_dir
            try:
                shutil.move(os.path.join(self.hidden_dir, o), moved_to)
            except OSError as e:
                msg = "The following error occurred when moving {0}/{1}:" \
                      "{2}".format(self.hidden_dir, o, e)
                swisspy.print_and_log(msg, self.log_files, quiet=self.quiet)

    def retry_transfer(self, src, dest, errors):
        """Attempt to retransfer errored files.
        Returns none on success, and raises any errors encountered.

        """
        def transfer_catching_errors():
            try:
                shutil.move(src,dest)
                return None
            except shutil.Error as e:
                return e.message
            except Exception as e:
                print "\nA fatal error occurred: ", e
                sys.exit(1)

        # If the file doesn't exist in dest, try and transfer from source
        if not os.path.exists(dest):
            if os.path.exists(src):
                return transfer_catching_errors()
            else:
                msg = "Error: retried file does not exist at {0} or {1}.\n"\
                 "".format(src, dest)
                swisspy.print_and_log(msg, self.log_files,
                                          quiet=self.quiet)

        # If the file does exist at the destination, attempt transfer.
        else:
            if os.path.exists(src):
                return transfer_catching_errors()
            else:
                swisspy.print_and_log("{0} does not exist. " + \
                                      "Look for it at {1}.".format(src, dest),
                                      self.log_files, quiet=self.quiet)

    def retry_wrapper(self):
        """Iterate through self.error_list, retrying the transfer of any failed files"""
        if self.error_list:
            for e in self.error_list:
                source_path = e[0]
                dest_path = e[1]
                new_errors = self.retry_transfer(source_path, dest_path,
                                                 self.error_list)
                return new_errors

    def rename_file(self, path_dict, prev_path, rename_log_file,
                    rename=False, indicator='^',):
        """Renames a file, or logs its abberations

        path_dict : dict
            A dictionary as output by sanitise(), with the following structure:
                {'out_string': The sanitised string,
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
        positions_in_path = [p + len(prev_root) - len(self.hidden_dir) for p in path_dict['positions']]
        #Strip the path of the hidden dir out of the string to be logged
        #The '+1' here deals with the first forward slash
        path_to_log = prev_path[len(self.hidden_dir) + 1:]
        new_path_to_log = new_path[len(self.hidden_dir) + 1:]
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
                # Log the renamed file in human readable format, on the
                # SAN if a rename log file has been defined...
                change_log_files = self.log_files[:]
                if rename_log_file:
                    change_log_files.append(rename_log_file)

                msg = "Changed from: {0}\nChanged to:   {1}\n\n" \
                      "".format(path_to_log, new_path_to_log)
                swisspy.print_and_log(msg, change_log_files,
                                      ts=None, quiet=self.quiet)
                # ...and for logstash.
                if self.logstash_dir:
                    with open(self.logstash_files['renamed'], 'a') as lsf:
                        lsf.write("{Changed from: }" + prev_path +\
                                  "{to: }" + new_path + '\n')
            except OSError:
                swisspy.print_and_log("Error: unable to rename " + prev_path + '\n',
                                   self.log_files, ts="long", quiet=self.quiet)
        else:
            # Add the clean path to a list of changed files,
            # so that logging without changing works correctly
            self.sanitised_list.append(new_path)
            if path_dict['subs_made']:
                swisspy.print_and_log("Illegal characters found in file   : " +\
                                   path_to_log + '\n',
                                   self.log_files, ts=None, quiet=self.quiet)
                swisspy.print_and_log("At these positions                 : " +\
                                   ind_line + '\n',
                                   self.log_files, ts=None, quiet=self.quiet)
                swisspy.print_and_log("Characters found (comma separated) : " +\
                                   ', '.join(path_dict['subs_made']) + '\n',
                                   self.log_files, ts=None, quiet=self.quiet)
                swisspy.print_and_log("Suggested change                   : " +\
                                   new_path_to_log + '\n\n',
                                   self.log_files, ts=None, quiet=self.quiet)

    def strip_hidden(self, from_list, to_remove=None):
        """Given a lost of files, remove a given common path from them - in this
         case, the path to the hidden directory.

        from_list : list : strings : paths
            The list of paths to be stripped
        to_remove :
            The common path to be removed

        """
        if not to_remove:
            to_remove = self.hidden_dir
        return [f[len(to_remove):] for f in from_list]

    def write_pid(self):
        """Write PID file to prevent multiple syncronously running
        instances of the program.
        """
        if os.path.isfile(self.pid_file):
            with open(self.pid_file, 'r') as pf:
                existing_pid = pf.read()
                try:
                    if swisspy.check_pid(existing_pid):
                        message = "Process with pid " + existing_pid + \
                                  " is currently running. Exiting now.\n"
                        swisspy.print_and_log(message, [self.temp_log_file],
                                              ts='long', quiet=False)
                        sys.exit()
                    else:
                        swisspy.print_and_log("Removing stale pidfile\n",
                                              [self.temp_log_file],
                                              ts='long', quiet=False)
                        os.remove(self.pid_file)
                except OSError as e:
                    swisspy.print_and_log("Process could not be checked. Error: " + \
                                          str(e) + "\n",
                                          [self.temp_log_file], ts='long', quiet=False)

        else:
            pf = open(self.pid_file, 'w')
            pf.write(str(os.getpid()))

    def move_files(self, source, dest, files, copied_files):
        self.started_transfer.set()
        swisspy.print_and_log("Moving files cleared for copy"
                              "\n\tFiles transferred:\n",
                              self.log_files, quiet=self.quiet)
        for f in files:
            if source in f:
                file_path = self.strip_hidden([f], source + '/')[0]
            else:
                file_path = f
            target = os.path.join(dest,file_path)
            if os.path.exists(f): # Guards against resource fork disappearance
                try:
                    shutil.move(f, target)
                except shutil.Error as e:
                    self.error_list.append(e)
                    return
                else:
                    copied_files.append(file_path)
                    swisspy.print_and_log("\t" + file_path + "\n",
                                          self.log_files,
                                          ts=None,
                                          quiet=self.quiet)

def main(s):
    """ Call the requisite functions of s, a Sanitisation object"""

    #Write a pid file
    if s.create_pid:
        s.write_pid()

    try:
        folder = swisspy.immediate_subdirs(s.to_archive_dir)[0]
    except IndexError: #'To Archive dir is empty"
        return

    deleted_files = []
    if s.rename:
        if not s.rename_log_dir:
            swisspy.print_and_log("Please specify a directory to log "
                                  "renamed files to (usually on dest.)",
                                  s.log_files, quiet=s.quiet)
            sys.exit(1)
        rename_log_file = os.path.join(s.rename_log_dir, folder + ".txt")
    else:
        rename_log_file = ""
    folder_start_path = os.path.join(s.to_archive_dir, folder)
    #Check the directory to be copied isn't still being written to:
    if swisspy.dir_being_written_to(folder_start_path):
            swisspy.print_and_log(folder + " is being written to. "
                                           "Skipping this time.",
                              [s.temp_log_file], ts="long", quiet=s.quiet)
            return
    log_folder = os.path.join(s.illegal_log_dir, folder)
    if not os.path.exists(log_folder):
        os.mkdir(log_folder)
    log_path =  os.path.join(log_folder,
                             swisspy.time_stamp('short') + ".log")
    #A list of <260 char files to be logged to
    s.log_files = [log_path[:259]]
    swisspy.print_and_log("Processing " + folder + "\n",
                          s.log_files, quiet=s.quiet)
    # Move everything to the hidden folder, unless it's already there,
    # in which case move it to Problem Files
    if folder in swisspy.immediate_subdirs(s.the_root):
        move_to = os.path.join(s.problem_dir, folder)
        swisspy.print_and_log(str(folder) + " is already being processed."
                              "It has been moved to " + move_to,
                              s.log_files, quiet=s.quiet)
        shutil.move(folder_start_path, move_to)
        return
    else:
        shutil.move(folder_start_path, os.path.join(s.the_root,folder))

    #Sanitise the directory itself, and update 'folder' if a change is made
    s.rename_to_clean(folder, s.the_root, 'dir', rename_log_file)
    if sanitise(folder)['out_string'] != folder:
        folder = sanitise(folder)['out_string']
    target_path = os.path.join(s.the_root, folder)
    s.errors_found = False

    for path, dirs, files in os.walk(target_path, topdown=False):
        #Sanitise file names
        for f in files:
            s.rename_to_clean(f, path, 'file', rename_log_file)
            if f in s.files_to_delete:
                full_path = os.path.join(path,f)
                try:
                    os.remove(full_path)
                    deleted_files.append(f)
                except Exception as e:
                    msg = "Unable to remove file {0} \n " \
                          "Error details: {1}\n".format(f, str(e))
                    swisspy.print_and_log(msg, s.log_files, quiet=s.quiet)
        #Sanitise directory names
        for d in dirs:
            s.rename_to_clean(d, path, 'dir', rename_log_file)

    if not s.errors_found or s.rename:
        passFolder = os.path.join(s.pass_dir, folder)
        msg = "Finished sanitising {0}. Moving to {1}\n".format(folder,
                                                                s.pass_dir)
        swisspy.print_and_log(msg, s.log_files, quiet=s.quiet)
        s.move_and_merge(target_path, passFolder)

    else:
        try:
            shutil.move(target_path, s.problem_dir)
            swisspy.print_and_log ("{0} has been moved to" \
                               "{1}.\n".format(folder, s.problem_dir),
                               s.log_files, quiet=s.quiet)

        except shutil.Error as e:
            msg = "Unable to move {0} to {1} - it may already exist in that " \
                  "location.\nIf you need to archive a changed version of " \
                  "this file, please rename it appropriately and retry.\n" \
                  "Error: {2}\n".format(folder, s.problem_dir, e)
            swisspy.print_and_log (msg, s.log_files, quiet=s.quiet)

if __name__ == '__main__':
    args = get_arguments()
    s = Sanitisation(args.passdir, args.casesensitive,
                     logstash_dir=args.logstash_dir,
                     rename_log_dir=args.rename_log_dir,
                     oversize_log_file_name=args.oversizelog,
                     quiet=args.quiet,
                     target=args.target,
                     temp_log_file=args.temp_log_file,
                     rename=args.dorename,
                     trust_source=args.trust_source,
                     )
    try:
        main(s)
    except Exception as e:
        try:
            error_file = os.path.join(s.logstash_dir, "errors.txt")
            swisspy.print_and_log("\nError encountered: " +  str(e),
                                  log_files=[error_file], quiet=False)
        except IOError:
            print "Couldn't open " + error_file
        raise
