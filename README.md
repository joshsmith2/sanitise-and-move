sanitise-and-move
=================

Sanitise all files in a directory, removing any characters from filenames which are illegal on Windows as well as problematic characters, then move them to another location, logging everything fully.

This was written for Hogarth in 2013 as an archiving solution. 
```
Usage:    

-c, --casesensitive       For use on case sensitive filesystems. Default - off.    
-d, --dorename            Actually rename the files - otherwise just log and output to standard output.    
-h, --help                Print this help and exit.    
-l  --logstashDir=path    A directory on the archive box containing a set of files sent by rsyslog to logstash.    
-r  --renameLogDir=path   Directory, usually on the destination, for logs of files which have been renamed to be stored. 
-o, --oversizelog=path    Log to write files with overlong path names in - otherwise don't log.    
-p, --passdir=path        Directory to which clean files should be moved.    
-q, --quiet               Don't output to standard out.    
-t, --target              The location of the hot folder    
--temp-log-file           A file to write log information to
```
