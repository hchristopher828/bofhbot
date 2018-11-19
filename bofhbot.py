#!/usr/bin/env python3

#### module load python/3.6
#### need python3 cuz exception handling for ssh call

# bofhbot - An enhanced sinfo -R for lazy sys admins--aka bofh :)
# see README.rst for detailed description (and license).
# tin (at) berkeley.edu 

# future exercise can likely write this using functional approach
# for now, regular scripting style. 
# OOP can have a structure with problem node as list of objects
# and parallel ssh/ping/etc check on them 
# to speed up output


import os
import re # regex
import time
import argparse
import shlex
import sys
import subprocess
#import paramiko  # could abandone
from multiprocessing import Pool
from shutil import copyfile 

# global param :)  better as OOP get() fn or some such.  
sinfoRSfile = '/var/tmp/sinfo-RSE.txt'
#sinfoRSfile = 'sinfo-RSE-eg.txt.head5'
nodeColumnIndex=3
nodeColumnIndex=0

# programmer aid fn
# dbgLevel 3 (ie -ddd) is expected by user troubleshooting problem parsing input file
# currently most detailed output is at level 5 (ie -ddddd) and it is eye blurry even for programmer
#dbgLevel = 0  
##dbgLevel = 1   use -ddddd now
def dbg( level, strg ):
    if( dbgLevel >= level ) : 
        print( "<!--dbg%s: %s-->" % (level, strg) )

# -v add verbose output.  not sure if ever would need it
def vprint( level, strg ):
    if( verboseLevel >= level ) : 
        print( "%s" % strg )

#def parseCliArg():
#    optino1 = sys.argv[1]
# parseCliArg()-end
# Sorry Nick, I much rather use argparse. -Tin


def process_cli() :
        # https://docs.python.org/2/howto/argparse.html#id1
        parser = argparse.ArgumentParser( description='This script give enhanced status of problem nodes reported by eg sinfo -R')
        parser.add_argument('-i', '--ipmi',  help="include ipmi test (may req elevated priv)",  required=False, action="store_true" ) 
        parser.add_argument('-w',  help="TBA pdsh-style list of nodes eg n00[06-17].sav3" ) 
        parser.add_argument('-g',  help="TBA heck take /etc/pdsh/group def file for node list" ) 
        parser.add_argument('-n', '--nodelist',  help="Use a specified nodelist file, eg /etc/pdsh/group/all",  required=False, default="" ) 
        parser.add_argument('-s', '--sfile',  help='Use a file containing output of sinfo -N -R -S %E --format="%N %6t %19H %9u %E"', required=False, default="" ) 
        parser.add_argument('-v', '--verboselevel', help="Add verbose output. Up to -vv maybe useful. ", action="count", default=0)
        parser.add_argument('-d', '--debuglevel', help="Debug mode. Up to -ddd useful for troubleshooting input file parsing. -ddddd intended for coder. ", action="count", default=0)
        parser.add_argument('--version', action='version', version='%(prog)s 0.2')
        args = parser.parse_args()
        global dbgLevel 
        global verboseLevel 
        dbgLevel = args.debuglevel
        verboseLevel = args.verboselevel
        if args.nodelist != '' :
            args.nodelist = re.sub( r'[^A-Za-z0-9/\-_%\. ]+', r'_', args.nodelist )
            vprint(1, "## cli parse for --nodelist, after cleansing, will use: '%s'" % args.nodelist )
        if args.sfile != '' :
            # check path not having things like /foo/bar;rm /etc/passwd
            # the clean list is probably harsher than need to be , but it is a path, not typically convoluted
            vprint(2, "cli parse for --sfile input  '%s'" % args.sfile )
            args.sfile = re.sub( r'[^A-Za-z0-9/\-_%\. ]+', r'_', args.sfile )  # not sure if i really want to allow space...
            vprint(1, "## cli parse for --sfile will use: '%s'" % args.sfile )
        if args.ipmi :
            dbg(3, "-i or --ipmi option was used" )
        return args
# end process_cli() 




# get ouptupt of sinfo -R -S ... 
# now just store output in a file  sinfoRSfile (global; future oop property)
# return is just exit code of running the sinfo cmd.
def generateSinfo() :
    # https://github.com/PySlurm/pyslurm  but then have to install python lib before being able to use script :-/
    #sinfoRS = subprocess.run(['sinfo', '-R -S %E --format="%9u %19H %6t %N %E"'])
    #cmd = 'sinfo -R -S %E --format="%9u %19H %6t %N %E" ' + " > "  +  sinfoRSfile     # more human readable
    cmd = 'sinfo -N -R -S %E --format="%N %6t %19H %9u %E" ' + " > "  +  sinfoRSfile   # node first, one node per line :)
    command = cmd
    dbg(5, command)
    #sinfoRSout = subprocess.call(shlex.split(command))
    sinfoRSout = os.system(command) # exit code only from mos.system()
    dbg(5, sinfoRSout )
    return sinfoRSout 
    # return is just exit code of running the sinfo cmd.
    #+sinfoRS = os.popen(cmd).read()
    #sinfoRS = open('sinfo-RSE-eg.txt.head5','r')
#generateSinfo()-end

#def getSinfo():
def buildSinfoList():
#def buildSinfoList(infoRS=sinfoRSfile):
    # sinfoRSfile is currently global, i guess OOP would be very similar...
    # ++ consider changing to use fn arg for the file
    dbg(3, "buildSinfoList() about to open '%s'" % sinfoRSfile )
    sinfoRS = open( sinfoRSfile,'r')
    #print( sinfoRS )
    #linelist = sinfoRS.split('\s')
    # basic cleansing/sanitizing done, just to avoid hacking
    # note that the debug still process original line
    # once stable and known work as desired, move the sanitizing earlier in the code
    # especially now user could be providing --nodelist or --sfile 
    sinfoList = [ ] 
    for line in sinfoRS :
        dbg(4, "processing '%s'" % line.rstrip() )
        #currentLine = re.search( '([\S]+[\s]+)*', line.rstrip())   # truncate long lines :(  still match empty line :(
        currentLine = re.search( '^$', line )   # ie blank line
        if( currentLine ) :
            dbg(5, "skipping blank line" )
        else :
            # sinfoList.append( line.rstrip() )  # unsanitized, work.
            currentLine =  re.sub( '[;$`#\&\\\]', '_', line ).rstrip()   # sanitized
            # sanitization/cleansing replaces ; $ ` # &  \ with underscore
            # () still allowed.  but since $ not allowed, won't have 4()
            # * ' " are allowd.  not thinking of problem with these at this point
            sinfoList.append( currentLine )  # sanitized, replaces ; & with underscore
            #sinfoList.append( re.sub( r':;\&\*', r'_', line.rstrip() ) )  # sanitized, replaces ; & with underscore
            dbg(5, "adding...: '%s' to   sinfoList" % currentLine )
    #print( sinfoList )
    return sinfoList 
# buildSinfoList()-end


# Input: array list of lines with output of sinfo -R -S ...
# OUTPUT: array list of nodes (maybe empty)
# this was first coded up for offline development with saved sinfo ... output
# but useful for new user to call it, in case they want to dry run the script
# in non production environment :)
def sinfoList2nodeList( sinfoList ):
    #--linenum = 0 
    #--item = 0
    nodeList = [ ] 
    for line in sinfoList :
        nodeList.append( getNodeList( line ) )
    return nodeList
# sinfoList2nodeList()-end


# Input: single line of output of sinfo -R -S ...
# OUTPUT: array list of nodes (maybe empty)
# for now return a list of nodes needing ping/ssh info
## don't like this now.  very specific to our node naming convention of n0000.CLUSTER
## should just expect nodename from column 1 or some such
## TODO.  ie, relax it needing \d\d\d\d ... 
## do expect a cleansed file :)
def getNodeList( sinfoLine ) :
        line = sinfoLine
        nodeList = [ ]
        #node = re.search( '(n\d\d\d\d\.[\w]+)[,]*', str, re.U|re.I )  # only handle 1 node for now...

        #print( "%d :: %s " % (linenum, sinfoRS[linenum]) )
        lineItem = line.split()
        try :
            #str = lineItem[3]
            str = lineItem[nodeColumnIndex]  # nodeColumnIndex is global param (++better OOP sinfo.nodeColumnIndex() )
        except IndexError :
            str = "NADA"
        #print( "%d :: %s " % (linenum, lineItem[0]) )
        #dbgstr = "%d :: %s " % (linenum, str) 
        #dbg( 3, dbgstr )
        #if( str ~= 'n[\d\d\d\d]' ) : 
        #node = re.search( r'(n[\d\d\d\d])', str, re.U|re.I|re.VERBOSE )  
        node = re.search( '(n\d\d\d\d\.[\w]+)[,]*', str, re.U|re.I )  # only handle 1 node for now...
        if node : 
            #nodeList[item] = str
            dbgstr =  "===%s===" % node.group(1) 
            dbg(3, dbgstr)
            nodeList.append( node.group(1) )
        return nodeList
#getNodeList()-end

# like sinfoList2nodeList( sinfoList ), but only use 1 line as input
# return only first node for now
# try to ssh to a node and see what happens to it
# return a variety of string depending of status of the node.  eg Up, TimeOut, Down?, askPassword
# https://github.com/matthew-li/lbnl_scripts/blob/master/check_mounted_systems.py
def checkSsh( node ) :
    litmusCmd = "uptime"
    command = "ssh %s %s" % (node, litmusCmd)
    timeout = 5
    try:
        #exitCode = subprocess.call(shlex.split(command), timeout=timeout)
        #return exitCode
        #exitCode = subprocess.check_output(shlex.split(command), timeout=timeout)
        #exitCode = subprocess.check_output(shlex.split(command), stderr='/dev/null', timeout=timeout)
        with open(os.devnull, 'w') as devnull: 
            sshStdOut = subprocess.check_output(shlex.split(command), timeout=timeout, stderr=devnull)
            dbg(5, "ssh test stdout: %s" % sshStdOut)
        return "up"
    except subprocess.CalledProcessError as e:
        error = "\"{cmd}\" had a bad return code of {ret}.".format(cmd=command, ret=e.returncode)
        return "DOWN"
        #raise ValueError(err)
    except subprocess.TimeoutExpired as e:
        error = "\"{cmd}\" exceeded the timeout of {t} seconds.".format(cmd=command, t=timeout)
        #raise TimeoutError(error)
        dbg(1, "This case likely have ssh asking for password")
        print( e.output )
        return "TimedOut"
    return "Ssh_unexpected_problem"
# checkSsh()-end 

def executeCommand(node, command, timeout=5):
    sshCommand = "ssh {node} \"{command}\"".format(node=node, command=command)
    try:
        with open(os.devnull, 'w') as devnull:
            sshStdOut = subprocess.check_output(shlex.split(sshCommand), timeout=timeout, stderr=devnull)
            return sshStdOut.decode('utf-8').strip()
    except:
        return None # Might want to add specific error handling later
# executeCommand()-end

def checkMountUsage(node, mount):
    command = "df -h {mount} --output=target,used | grep {mount} | awk '{{ print $2 }}'".format(mount=mount)
    usage = executeCommand(node, command)
    return usage or "NotFound"
# checkMountUsage()-end

# https://stackoverflow.com/questions/14236346/elegant-way-to-test-ssh-availability
# but paramiko seems to req lot of username/key setup, too variable for generic user to use :(
def checkSshParamiko_Abandoned( node ) :
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy( paramiko.AutoAddPolicy() )
    #ssh.set_missing_host_key_policy( AutoAddPolicy )
    retries = 1
    interval = 5
    #key =  None
    #private_key = paramiko.RSAKey.from_private_key_file(os.path.expanduser(key))
    for x in range(retries) :
        try : 
            #ssh.connect(node, pkey=private_key)
            ssh.connect(node)
            ssh.close()
            return "Up"
        except Exception as e :
            dbg(3, "check_ssh exception %s" % e)
            time.sleep( interval )
    return "Down"
    #return "TimeOut"
# checkSsh()-end 

# other checks to add
# checkNhc()
# (see README)


def cleanUp() :
    if( dbgLevel == 0 ) :
        os.remove( sinfoRSfile ) 
    dbg(1, "sinfoRSfile left at: %s " % sinfoRSfile )
    vprint(1, "## Run 'reset' if terminal is messed up" )
    #os.system( "reset") # terminal maybe messed up due to bad ssh, but reset clears the screen :(
# cleanUp()-end

def processLine(data):
    node, line = data
    sshStatus = checkSsh(node)
    scratchStatus = checkMountUsage(node, "/global/scratch") 	if sshStatus == 'up' else "(skip)"
    swStatus      = checkMountUsage(node, "/global/software") 	if sshStatus == 'up' else "(skip)"
    tmpStatus     = checkMountUsage(node, "/tmp") 		if sshStatus == 'up' else "(skip)"
    #print("%-120s ## ssh:%4s scratch:%10s" % (line, sshStatus, scratchStatus, swStatus, tmpStatus))
    print("%-80s ## ssh:%4s scratch:%7s sw:%7s tmp:%7s" % (line, sshStatus, scratchStatus, swStatus,tmpStatus))
#processLine()-end

def main(): 
    args = process_cli()
    dbg(5, "bofhbot I am")
    vprint(1, "## sinfo enhanced by bofhbot ##")
    # tmp exit
    #return


    # TODO ++ when turn into OOP
    # create as object property/state info
    # where various args could have "side effects"
    # eg, in addition to handling --nodelist as input for list of hosts
    #     also change the format to narrow the column containing host info (since no sinfo -R data)
    if( args.nodelist != "" ) :
        # used --nodelist option, 
        # nodelistFile = args.nodelist
        # --nodelist eg file /etc/pdsh/group/all -- ie, one hostname per line
        dbg(2, "--nodelist arg was %s" % args.nodelist )
        copyfile( args.nodelist, sinfoRSfile )
    elif( args.sfile != "" ) :
        # used --sfile option, 
        dbg(2, "--sfile arg was %s" % args.sfile )
        dbg(2, "sinfoRSfile is %s" % sinfoRSfile )
        # better off having objects.
        # right now it is like a hack, copy user's provided sinfo file into the location 
        # where my script would store the temporary output
        copyfile( args.sfile, sinfoRSfile )
    else :
        generateSinfo()
    #endif 
    # ++ TODO  currently only read sinfoFile for hostname, rest passed as comment
    #    at least when using --nodelist should narrow the column space since no sinfo -R comment avail.
    sinfoList = buildSinfoList() # fn use "OOP/Global" file containing sinfo output


    # tmp exit (for code dev use)
    #return


    # ++ OOP gather all info
    # ++ TODO consider have diff option and invoke alternate fn to format output
    pool = Pool(20)
    nodes = [ (node, line) for line in sinfoList for node in getNodeList(line) ]
    pool.map(processLine, nodes)
    cleanUp()
# main()-end


main()


#### vim modeline , but don't seems to fork on brc login node :(
#### vim: syntax=python  
