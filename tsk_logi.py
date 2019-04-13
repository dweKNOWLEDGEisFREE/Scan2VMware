#!/usr/bin/env python3
# -*- coding: utf-8 -*-

''' tsk_logi - Log File Interceptor
             * Intercepts and stores output from the called program.


    This program is part of the Scan2 Suite.
    https://github.com/dweKNOWLEDGEisFREE

    This program is licensed under the GNU General Public License v3.0

    Copyright 2019 by David Weyand, Ernst Schmid

'''


# IMPORTS
import sys, os, datetime, random


# VERSION
__all__     = []
__version__ = 0.1
__date__    = '2019-03-01'
__updated__ = '2019-03-03'

# CONFIGURATION DATA
prg_file = None

# PATH SETTINGS
path_PRG  = None
path_TEMP = '/var/tmp'
path_HTML = './static/data/logfiles'

# FILE SETTINGS
file_TEMP = 'scan2VMware.tmp'

# LOG FILE SETTINGS
file_LOG_cntr = 1
file_LOG_name = ""


''' GetTmpFileName
'''
def GetTmpFileName():
    # Filename
    tmpName =path_TEMP+'/'
    tmpName+='{:%Y%m%d%H%M%S}'.format(datetime.datetime.now())
    tmpName+=str(random.randint(100000000, 999999999))
    tmpName+=file_TEMP
    return tmpName


''' GetLogFileName
'''
def GetLogFileName(inf):
    # Global
    global file_LOG_cntr, file_LOG_name
    # Creating Log File Name TIMESTAMP
    tst='{:%Y-%m-%d--%H-%M-%S}'.format(datetime.datetime.now())
    if (file_LOG_name != tst):
        file_LOG_cntr = 1
        file_LOG_name=tst
    else:
        file_LOG_cntr+=1
    # Return name
    if inf==None:
        return path_HTML+'/'+tst+'-'+str(file_LOG_cntr)+'.txt'
    else:
        return path_HTML+'/'+tst+'-'+str(file_LOG_cntr)+'--'+inf+'.txt'
    

''' GO
'''
if __name__ == "__main__":
    # PROGRAM DATA
    path_PRG, prg_file = os.path.split(os.path.abspath(sys.argv[0]))
    os.chdir(path_PRG)
    print("tsk_logi: prog - "+prg_file)
    print("tsk_logi: path - "+path_PRG)
    # SHOW PARAMETERS
    print('tsk_logi: para - No:'+str(len(sys.argv))+' Str:'+str(sys.argv))
    # SHOW USER ID
    print('tsk_logi: rUID - %d' % os.getuid())
    print('tsk_logi: eUID - %d' % os.geteuid())
    # PROGRAM PARAMTERS
    if len(sys.argv)<2:
        exit(-1)
    cmd=sys.argv[1]
    for i in range(2, len(sys.argv)):
        cmd+=' "'+sys.argv[i]+'"'
    # TEMP FILE NAME
    fn=GetTmpFileName()
    # EXECUTE COMMAND
    cmd+=' >'+fn+' 2>&1'
    print('tsk_logi: cmd ['+cmd+']')
    sys.stdout.flush()
    sys.stderr.flush()
    ret=os.system(cmd)
    print('tsk_logi: res ['+str(ret)+']')
    # RENAME FILE
    try:
        os.rename(fn, GetLogFileName(None))
    except:
        print("tsk_logi: rename failed")
    # RETURN RESULT
    exit(ret)
