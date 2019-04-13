#!/usr/bin/env python3
# -*- coding: utf-8 -*-

''' tsk_ctrl - Scan2VMware collector web interface.
             * Responsible for all http related stuff.


    This program is part of the Scan2 Suite.
    https://github.com/dweKNOWLEDGEisFREE

    This program is licensed under the GNU General Public License v3.0

    Copyright 2019 by David Weyand, Ernst Schmid

'''


# Imports used by LOG FILE etc.
import os, sys, crontab, datetime
import json
import lib_logs

# Imports for Flask
from flask import Flask, render_template, request
from flask import redirect

# Imports and config data of CONFIG
from flask_wtf import Form
from wtforms   import HiddenField, SelectField, BooleanField, StringField, IntegerField, validators



# Configuration data
cfg_file = 'config.json'
log_file = 'jobs.json'

# Path settings
path_XML  = './data/logfiles'
path_HTML = './static/data/logfiles'
path_iTop = './itop/conf/params.local.xml' 


# iTop ACCESS DATA
cfg_itop_cr = {
    'url' : 'http://itop-server-url',
    'usr' : 'sync2vmware',
    'pwd' : 'sync2password'
}

# vSphere ACCESS DATA
cfg_vsphere = {
    'synchro_user'   : 'sync2vmware',
    'default_org_id' : 'unbekannt',
    'doQ_1'          : False,
    'url_1'          : 'vSphere-Server:443',
    'usr_1'          : 'vSphere-User',
    'pwd_1'          : 'vSphere-Password'
}

# Crontab PARAMETERS
cfg_crontab = {
    'doQuery' : False,
    'doClean' : False,
    'time'    : 0,
    'id'      : 'Scan2VMware'
}

# Log File PROCESSING
cfg_logfile = {
    'number' : 100,
    'age'    : 28
}



''' iTop XML SAVE CONFIG
'''
def config_iTop_save():
    # import element tree
    import xml.etree.ElementTree as ET 

    def writeELEM(root, name, data):
        # Reading element data
        elems = root.findall(name)
        for elem in elems:
            elem.text=data

    # info
    print('tsk_ctrl: saving iTop parameters', file=sys.stdout)
    try:
        #import xml file
        tree = ET.parse(path_iTop)
        root = tree.getroot()
        # iTop url
        writeELEM(root, "itop_url",      cfg_itop_cr ['url'     ])
        # iTop usr
        writeELEM(root, "itop_login",    cfg_itop_cr ['usr'     ])
        # iTop usr
        writeELEM(root, "itop_password", cfg_itop_cr ['pwd'     ])
        # mySQL host
        writeELEM(root, "sql_host",      cfg_mysql_cr['host'    ])
        # mySQL database
        writeELEM(root, "sql_database",  cfg_mysql_cr['database'])
        # mySQL user
        writeELEM(root, "sql_login",     cfg_mysql_cr['user'    ])
        # mySQL password
        writeELEM(root, "sql_password",  cfg_mysql_cr['password'])
        # write it back
        tree.write(path_iTop)   
    except:
        print('ERROR..: config_iTop_save iTop ACCESS FAILED', file=sys.stderr)
        return


''' vSphere GET NUMBER OF SERVER CONFIGURATIONS
'''
def vSphere_Srv_No():
    # Use global
    global cfg_vsphere
    # Checking for 'doQ_NO'
    tmpNo=0
    # Check for first miss
    while 'doQ_'+str(tmpNo+1) in cfg_vsphere:
        tmpNo+=1
    # Return number of entries
    return tmpNo


''' vSphere ADD NEW SERVER ENTRY
'''
def vSphere_Srv_Add(url, usr, pwd, query):
    # Use global
    global cfg_vsphere
    # Number of entries
    tmpNo=vSphere_Srv_No()
    # Add new entry
    cfg_vsphere['doQ_'+str(tmpNo+1)]=query
    cfg_vsphere['url_'+str(tmpNo+1)]=url
    cfg_vsphere['usr_'+str(tmpNo+1)]=usr
    cfg_vsphere['pwd_'+str(tmpNo+1)]=pwd


''' vSphere DEL SERVER ENTRY NO x
'''
def vSphere_Srv_Del(idx):
    # Use global
    global cfg_vsphere
    # Number of entries
    tmpNo=vSphere_Srv_No()
    if tmpNo<=1 or idx<1 or idx>tmpNo:
        return
    # Transfer data
    while idx<tmpNo:
        cfg_vsphere['url_'+str(idx)]=cfg_vsphere['url_'+str(tmpNo)]
        cfg_vsphere['usr_'+str(idx)]=cfg_vsphere['usr_'+str(tmpNo)]
        cfg_vsphere['pwd_'+str(idx)]=cfg_vsphere['pwd_'+str(tmpNo)]
        cfg_vsphere['doQ_'+str(idx)]=cfg_vsphere['doQ_'+str(tmpNo)]
        idx+=1        
    # Delete last element
    del cfg_vsphere['url_'+str(tmpNo)]
    del cfg_vsphere['usr_'+str(tmpNo)]
    del cfg_vsphere['pwd_'+str(tmpNo)]
    del cfg_vsphere['doQ_'+str(tmpNo)]        


''' vSphere_Srv_LstNo
'''
def vSphere_Srv_LstNo():
    # Use global
    global cfg_vsphere
    # Variables
    tmpLst=[]
    tmpIdx=0
    tmpMax=vSphere_Srv_No()
    # Generate
    while tmpIdx<tmpMax:
        tmpIdx+=1
        tmpLst+=[(str(tmpIdx), str(tmpIdx))]
    # Result
    return tmpLst


''' vSphere_Srv_LstNames
'''
def vSphere_Srv_LstNames():
    # Use global
    global cfg_vsphere
    # Variables
    tmpLst=[]
    tmpIdx=0
    tmpMax=vSphere_Srv_No()
    # Generate
    while tmpIdx<tmpMax:
        tmpIdx+=1
        tmpLst+=[(str(tmpIdx), cfg_vsphere['url_'+str(tmpIdx)])]
    # Result
    return tmpLst


''' CONFIG CHECK
'''
def config_check():
    # Use global
    global cfg_itop_cr, cfg_vsphere, cfg_crontab, cfg_logfile
    # Checking CRONTAB job flags
    if cfg_crontab['doQuery']==None:
        cfg_crontab['doQuery']=False
    # CleanUp log files.
    if cfg_crontab['doClean']==None:
        cfg_crontab['doClean']=False
    # Checking CRONTAB TIME parameters
    if cfg_crontab['time']==None or int(cfg_crontab['time'])>=24*60:
        cfg_crontab['doQuery']=False
        cfg_crontab['doClean']=False
        cfg_crontab['time'   ]=0
    # Checking LOGFILE parameters
    if cfg_logfile['number']==None or int(cfg_logfile['number'])<10:
        cfg_logfile['number']=10
    if cfg_logfile['age']==None or int(cfg_logfile['age'])<7:
        cfg_logfile['age']=7


''' CONFIG LOAD
'''
def config_load():
    # loading
    try:
        with open(cfg_file) as json_file:
            # Use global
            global cfg_itop_cr, cfg_vsphere, cfg_crontab, cfg_logfile
            # load  
            data = json.load(json_file)
            # update
            cfg_itop_cr=data['iTop'   ][0]
            cfg_vsphere=data['vSphere'][0]
            cfg_crontab=data['Crontab'][0]
            cfg_logfile=data['LogFile'][0]
            # info
            print('tsk_ctrl: config file loaded', file=sys.stdout)
    except:
        print('tsk_ctrl: no JSON read access', file=sys.stderr)
    # checking
    config_check()
        

''' CONFIG SAVE
'''
def config_save():
    # checking
    config_check()
    # writing
    try:
        # Use global
        global cfg_itop_cr, cfg_vsphere, cfg_crontab, cfg_logfile
        # new config file
        data = {}
        data['iTop'   ]=[]
        data['iTop'   ].append(cfg_itop_cr)
        data['vSphere']=[]
        data['vSphere'].append(cfg_vsphere)
        data['Crontab']=[]
        data['Crontab'].append(cfg_crontab)
        data['LogFile']=[]
        data['LogFile'].append(cfg_logfile)
        print(data)
        # save
        with open(cfg_file, 'w') as outfile:
            json.dump(data, outfile)
        # info
        print('tsk_ctrl: new config file created', file=sys.stderr)
    except:
        print('tsk_ctrl: no JSON write access', file=sys.stderr)
        
        

''' CRON CHECK
'''
def cron_active():
    # Use global
    global cfg_crontab
    # Check for active entries
    try:
        jobs=crontab.CronTab(user='root')
        for job in jobs:
            if job.comment == cfg_crontab['id']:
                return 'RUNNING'
        return 'OFFLINE'
    except:
        return 'UNKNOWN'

def cron_list():
    # Use global
    global cfg_crontab
    # List crontab entries
    print('tsk_ctrl: cron jobs list', file=sys.stdout)
    try:
        jobs=crontab.CronTab(user='root')
        for job in jobs:
            print('tsk_ctrl: job ['+job.__str__()+']', file=sys.stdout)
    except:
        print('tsk_ctrl: no access to crontab', file=sys.stderr)
        
def cron_update():
    # Use global
    global cfg_crontab
    # Access crontab
    print('tsk_ctrl: cron job update', file=sys.stdout)
    try:
        # request access
        jobs=crontab.CronTab(user='root')
        # Delete cron jobs
        jobs.remove_all(comment=cfg_crontab['id'])
        # Saveing list of jobs
        jobs.write()
        # Update cron jobs
        if not bool(cfg_crontab['doQuery' ]) and not bool(cfg_crontab['doScan' ]) and \
           not bool(cfg_crontab['doUpdate']) and not bool(cfg_crontab['doClean']):
            return
        # Timecheck
        if int(cfg_crontab['time'])<0:
            return
        # Create Cron Job
        # Get path
        dirname, filename = os.path.split(os.path.abspath(sys.argv[0]))
        # Create job
        job=jobs.new(command=dirname+'/tsk_logi.py ./tsk_cron.py', comment=cfg_crontab['id'])
        # Every day at ...
        time = int(cfg_crontab['time']) % (24*60)
        job.minute.on(time %  60)
        job.hour.on  (time // 60)
        jobs.write()
        print('tsk_ctrl: job ['+job.__str__()+'] created.', file=sys.stdout)
        return
    except:
        return



# Booting up ...
print('tsk_ctrl: Scan2VMware ...', file=sys.stdout)
print('tsk_ctrl: test err output', file=sys.stderr)
print('tsk_ctrl: test std output', file=sys.stdout)

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['WTF_CSRF_ENABLED'] = False



''' FAVICON.ICO
'''
@app.route('/favicon.ico')
def url_favicon():
    print('url_favicon', file=sys.stderr)
    return app.send_static_file('favicon.ico')


''' REDIRECT from /
'''
@app.route('/')
def url_root():
    print('url_root', file=sys.stderr)
    return redirect("static/", code=302)

@app.route('/static/site/page/')
def url_page():
    print('url_page', file=sys.stderr)
    return app.send_static_file('site/page/index.html')



''' OVERVIEW
'''
@app.route('/static/')
def url_overview():
    print('url_overview', file=sys.stderr)
    return render_template("index.html")
#   return app.send_static_file('index.html')



''' STATUS
'''
@app.route('/static/site/status/')
def url_status():
    try:
        with open(log_file) as json_file:
            data=json.load(json_file)
            cur=data['cur'][0]
            lst=data['lst'][0]
            print (cur, lst)
    except:
        cur=""
        lst=""
    print (cur, lst)

    return render_template("site/status/index.html", cur=cur, lst=lst, cron=cron_active())
#   return app.send_static_file('site/status/index.html')



''' ACCESS DATA
'''
@app.route('/static/site/tools/', methods=["GET", "POST"])
def url_tools():

    # use global config variables
    global cfg_itop_cr, cfg_vsphere, cfg_crontab, cfg_logfile
        
    class ToolForm(Form):
        # dummy parameters
        cfgToolQuery  = HiddenField ('Query')
        cfgToolClean  = HiddenField ('Clean')
        # vSphere server selection
        srvLst=vSphere_Srv_LstNames()
        srvSel=1
        cfgVsphereLst = SelectField ('Server', choices=srvLst, default=srvSel)        


    # Request data
    toolForm = ToolForm(csrf_enabled=False)

    # Check for SCAN Button
    if request.method == 'POST' and not request.form.get('retrieve') is None and toolForm.validate:
        # Info
        print('tsk_ctrl: retrieve from server no ', str(toolForm.cfgVsphereLst.data), file=sys.stdout)
        # BUILD RETRIEVE COMMAND
        cmd=('./tsk_logi.py ./tsk_cron.py '+str(toolForm.cfgVsphereLst.data)+'&')
        print ('tsk_ctrl: RETRIEVE CMD ',cmd)
        sys.stdout.flush()
        sys.stderr.flush()
        os.system(cmd)
        print ('tsk_ctrl: RETRIEVE CMD running',cmd)

    # Check for QUERY Button
    if request.method == 'POST' and not request.form.get('cleanLog') is None and toolForm.validate:
        # Info
        print('tsk_ctrl: tool->clean', file=sys.stdout)
        # Get current time and date.
        now=datetime.datetime.today()
        # CleanUp of HTML Log File Directory
        lib_logs.delOldLogFiles(now, path_HTML, 'html', cfg_logfile['number'], cfg_logfile['age'])
        # CleanUp of XML Log File Directory
        lib_logs.delOldLogFiles(now, path_XML,  'xml', cfg_logfile['number'], cfg_logfile['age'])

    return render_template("site/tools/index.html", form=toolForm)
#   return app.send_static_file('site/tools/index.html')



''' CONFIGURATION ACCESS IP JOBS DATABASE CHRON NMAP
'''    
@app.route('/static/site/config/', methods=["GET", "POST"])
def url_config():
    
    class ConfigForm(Form):
        # iTop access parameters
        cfgItopUrl  = StringField (u'iTop URL:', 
                                  [validators.Length(min=0, max=50)], default=cfg_itop_cr['url'])
        cfgItopUser = StringField (u'iTop User name:', 
                                  [validators.Length(min=0, max=50)], default=cfg_itop_cr['usr'])
        cfgItopPwd  = StringField (u'iTop Password:', 
                                  [validators.Length(min=0, max=50)], default=cfg_itop_cr['pwd'])
        # vSphere global access parameters
        cfgVsphereSynchroUser = StringField (u'iTop Synchro Username',
                                             [validators.Length(min=0, max=50)], default=cfg_vsphere['synchro_user'])
        cfgVsphereOrgName     = StringField (u'iTop Default ORG Name',
                                             [validators.Length(min=0, max=50)], default=cfg_vsphere['default_org_id'])
        # vSphere server selection
        cfgVsphereLst = SelectField ('Server')        
        # vSphere server access parameters
        cfgVsphereIDX = HiddenField ()
        cfgVsphereDoQ = BooleanField()
        cfgVsphereUrl = StringField (u'vSphere URL', [validators.Length(min=0, max=50)])
        cfgVsphereUsr = StringField (u'vSphere USR', [validators.Length(min=0, max=50)])
        cfgVspherePwd = StringField (u'vSphere PWD', [validators.Length(min=0, max=50)])
        # Crontab Parameters
        tmHH=[]
        for i in range(0, 24, 1):
            tmHH+=[(str(i), str(i))]
        cfgScanTimeH = SelectField (choices=tmHH, default=str(int(cfg_crontab['time'])//60))
        tmMM=[]
        for i in range(0, 60, 5):
            tmMM+=[(str(i), str(i))]
        cfgScanTimeM = SelectField (choices=tmMM, default=str(((int(cfg_crontab['time'])//5)*5)%60))
        cfgDoQuery  = BooleanField(default=bool(cfg_crontab['doQuery']))
        cfgDoClean  = BooleanField(default=bool(cfg_crontab['doClean']))
        # Other configuration parameters
        cfgLogNumber = IntegerField('Total number of log files:', 
                                    [validators.Length(min=0, max=4)], default=cfg_logfile['number'])
        cfgLogAge    = IntegerField('Maximum age of log files (days):', 
                                    [validators.Length(min=0, max=3)], default=cfg_logfile['age'])

    def selDataSave():
        # Saving old data
        idxOld=str(cfgForm.cfgVsphereIDX.data)
        cfg_vsphere['doQ_'+idxOld] = cfgForm.cfgVsphereDoQ.data
        cfg_vsphere['url_'+idxOld] = cfgForm.cfgVsphereUrl.data
        cfg_vsphere['usr_'+idxOld] = cfgForm.cfgVsphereUsr.data
        cfg_vsphere['pwd_'+idxOld] = cfgForm.cfgVspherePwd.data

    def selDataUpdate():
        # Updating fields
        idxNew=str(cfgForm.cfgVsphereLst.data)
        cfgForm.cfgVsphereDoQ.data = bool(cfg_vsphere['doQ_'+idxNew])
        cfgForm.cfgVsphereUrl.data = str (cfg_vsphere['url_'+idxNew])
        cfgForm.cfgVsphereUsr.data = str (cfg_vsphere['usr_'+idxNew])
        cfgForm.cfgVspherePwd.data = str (cfg_vsphere['pwd_'+idxNew])
    
    # use global config variables
    global cfg_itop_cr, cfg_vsphere, cfg_crontab, cfg_logfile
    # Variablen
    cfgForm = ConfigForm(csrf_enabled=False)

    if request.method == 'GET':
        cfgForm.cfgVsphereIDX.data = 1
        cfgForm.cfgVsphereDoQ.data = bool(cfg_vsphere['doQ_1'])
        cfgForm.cfgVsphereUrl.data = str (cfg_vsphere['url_1'])
        cfgForm.cfgVsphereUsr.data = str (cfg_vsphere['usr_1'])
        cfgForm.cfgVspherePwd.data = str (cfg_vsphere['pwd_1'])

            
    if request.method == 'POST' and cfgForm.validate:
    
        if request.form.get('addVsphere') != None:
            # New entry
            vSphere_Srv_Add('', '', '', query=False)
            # Updateing selection
            cfgForm.cfgVsphereLst.choices = vSphere_Srv_LstNo()
            cfgForm.cfgVsphereLst.data    = str(vSphere_Srv_No())
            # Save/Update
            selDataSave()
            selDataUpdate()
            # Updating
            cfgForm.cfgVsphereIDX.data=cfgForm.cfgVsphereLst.data
            
        elif request.form.get('delVsphere') != None:
            if vSphere_Srv_No()>1:
                # Delete entry
                idx=int(cfgForm.cfgVsphereIDX.data)
                vSphere_Srv_Del(idx)                    
                # Updating select field
                cfgForm.cfgVsphereLst.choices = vSphere_Srv_LstNo()
                # Last entry
                if idx>vSphere_Srv_No():
                    cfgForm.cfgVsphereLst.data=str(vSphere_Srv_No())
                # Updating data
                selDataUpdate()
                # Updating
                cfgForm.cfgVsphereIDX.data=cfgForm.cfgVsphereLst.data
            
        elif (request.form.get('cfgVsphereLst') != None and
              cfgForm.cfgVsphereIDX.data!=cfgForm.cfgVsphereLst.data):    
            # Save/Update
            selDataSave()
            selDataUpdate()
            # Updating
            cfgForm.cfgVsphereIDX.data=cfgForm.cfgVsphereLst.data
        
        elif request.form.get('btnSubmit') != None:
            # Updating iTop configuration
            cfg_itop_cr['url']=cfgForm.cfgItopUrl.data
            cfg_itop_cr['usr']=cfgForm.cfgItopUser.data
            cfg_itop_cr['pwd']=cfgForm.cfgItopPwd.data
            # Updating crontab configuration parameters
            cfg_crontab['doQuery']=cfgForm.cfgDoQuery.data
            cfg_crontab['doClean']=cfgForm.cfgDoClean.data
            cfg_crontab['time'   ]=int(cfgForm.cfgScanTimeH.data)*60+int(cfgForm.cfgScanTimeM.data)
            # Updating other configuration parameters
            cfg_logfile['number']=cfgForm.cfgLogNumber.data
            cfg_logfile['age'   ]=cfgForm.cfgLogAge.data
            # Updating additional iTop configuration
            cfg_vsphere['synchro_user'  ]=cfgForm.cfgVsphereSynchroUser.data
            cfg_vsphere['default_org_id']=cfgForm.cfgVsphereOrgName.data
            # Updating vSphere configuration
            selDataSave()
            # Config Data Update
            config_save()
            cron_update()
    
    # update list of servers 
    cfgForm.cfgVsphereLst.choices = vSphere_Srv_LstNo()
    
    return render_template("site/config/index.html", form=cfgForm)
#   return app.send_static_file('site/config/index.html')


''' LOG FILES
'''
def make_entries_old(path):
    result=[]
    try:
        lst = os.listdir(path)
    except OSError:
        pass #ignore errors
    else:
        for name in lst:
            fn = os.path.join(path, name)
            nm=name.split('.')
#           print(nm, file=sys.stdout)
            if not os.path.isdir(fn) and len(nm) > 1 and nm[len(nm)-1].lower() == 'html':
            #   print(nm, file=sys.stdout)
                result.append(nm[0])
    result.sort(reverse=True)
    return result

def make_entries(path):

    def getmtime(name):
        return os.path.getmtime(os.path.join(path, name))

    result=[]
    try:
        lst = sorted(os.listdir(path), key=getmtime, reverse=True) 
    except OSError:
        pass #ignore errors
    else:
        for name in lst:
            fn = os.path.join(path, name)
            nm=name.split('.')
            if not os.path.isdir(fn) and len(nm) > 1 and nm[len(nm)-1].lower() == 'txt':
                result.append(nm[0])
    return result

@app.route('/static/site/logfiles/')
def url_logfiles():
#   print('-->', file=sys.stdout)
    logs=make_entries(path_HTML)
#   print(logs, file=sys.stderr)
#   print('<--', file=sys.stdout)
#   return render_template("site/logfiles/index.html", ref='static/data/logfiles/', ext='.html', list=logs)
    return render_template("site/logfiles/index.html", ref='static/data/logfiles/', ext='.txt',  list=logs)
#   return app.send_static_file('site/logfiles/index.html')



''' RUN SERVER
'''
if __name__ == '__main__':
    # SHOW PATH
    print('tsk_ctrl: Path - ',sys.argv[0])
    dirname, filename = os.path.split(os.path.abspath(sys.argv[0]))
    print ("tsk_ctrl: running from - ", dirname)
    os.chdir(dirname)
    # SHOW USER ID
    print('tsk_ctrl: Real UserID - %d' % os.getuid())
    print('tsk_ctrl: Effective UserID - %d' % os.geteuid())
    # get the config data.
    config_load()
    # list cron jobs
    cron_list()
#   cron_update()    
    # starting web server
    app.run(host= '0.0.0.0', port=5002)
