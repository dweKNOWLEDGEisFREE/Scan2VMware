#!/usr/bin/env python3
# -*- coding: utf-8 -*-

''' tsk_cron - Scan2VMware collector cronjob.
             * Query data from vSphere servers.
             * CleanUp old log files.


    This program is part of the Scan2 Suite.
    https://github.com/dweKNOWLEDGEisFREE

    This program is licensed under the GNU General Public License v3.0

    Copyright 2019 by David Weyand, Ernst Schmid

'''


# IMPORTS
import sys, os, json, csv, requests, datetime
import lib_logs
import zlib, xml.sax
import ipaddress

from alembic.util.messaging import status


#from pid import PidFile

# VERSION
__all__     = []
__version__ = 0.5
__date__    = '2018-06-01'
__updated__ = '2019-01-22'

# CONFIGURATION DATA
prg_file = None
cfg_file = 'config.json'
log_file = 'cron_log.json'
inf_file = 'cron_inf.json'

# PATH SETTINGS
path_PRG  = None
path_XML  = './data/logfiles'
path_HTML = './static/data/logfiles'
path_iTop = './itop/conf/params.local.xml'

#VMware file settings
csv_File_1_i = './itop/data/vSphereIPv4AddressCollector-%s.csv'
csv_File_1_o = './itop/data/vSphereIPv4AddressCollector-%s.csv.mod'
csv_File_1_T = './itop/data/vSphereIPv4AddressCollector-%s.csv.tmp'
#VMware file settings
csv_File_2_i = './itop/data/vSphereServerTeemIpCollector.raw-%s.csv'
csv_File_2_o = './itop/data/vSphereServerTeemIpCollector.raw-%s.csv.mod'
csv_File_2_T = './itop/data/vSphereServerTeemIpCollector.raw-%s.csv.tmp'
#VMware file settings
csv_File_3_i = './itop/data/vSphereHypervisorCollector-%s.csv'
csv_File_3_o = './itop/data/vSphereHypervisorCollector-%s.csv.mod'
csv_File_3_T = './itop/data/vSphereHypervisorCollector-%s.csv.tmp'
#VMware file settings
csv_File_4_i = './itop/data/vSphereFarmCollector-%s.csv'
csv_File_4_o = './itop/data/vSphereFarmCollector-%s.csv.mod'
csv_File_4_T = './itop/data/vSphereFarmCollector-%s.csv.tmp'
#VMware file settings
csv_File_5_i = './itop/data/vSphereVirtualMachineTeemIpCollector.raw-%s.csv'
csv_File_5_o = './itop/data/vSphereVirtualMachineTeemIpCollector.raw-%s.csv.mod'
csv_File_5_T = './itop/data/vSphereVirtualMachineTeemIpCollector.raw-%s.csv.tmp'


# iTop ACCESS DATA
cfg_itop_cr  = {}
# vSphere ACCESS DATA
cfg_vsphere  = {}
# Crontab PARAMETERS
cfg_crontab  = {}
# Log File PROCESSING
cfg_logfile  = {}


'''        
vSpherelnkIPInterfaceToIPAddressCollector
primary_key;ipinterface_id;ipaddress_id

vSphereLogicalInterfaceCollector
primary_key;macaddress;name;virtualmachine_id

vSphereModelCollector
primary_key;name;type;brand_id

vSphereOSFamilyCollector
primary_key;name

vSphereOSVersionCollector
primary_key;name;osfamily_id
'''

''' iTop VMware cvs Pathing
'''
def csv_patching():

    def get_IP_2_ORG_NAME(ip):
        if ip==None or len(ip)==0:
            return None
        # IP-Range Liste durchsuchen
        n_ip=int(ipaddress.IPv4Address(ip))
        for i in range(len(lst_IpRange)):
            if (n_ip>=int(ipaddress.IPv4Address(lst_IpRange[i][2])) and
                n_ip<=int(ipaddress.IPv4Address(lst_IpRange[i][3]))):
                return lst_IpRange[i][1]
        return None

    def get_CLIENTNAME_2_ORG_NAME(clientname):
        if clientname==None or len(clientname)==0:
            return None
        # Liste durchsuchen
        for i in range(len(lst_IPv4AddressCollector)):
            if lst_IPv4AddressCollector[i][3]==clientname:
                return lst_IPv4AddressCollector[i][2]
        return None

    def get_SERVERNAME_2_ORG_NAME(servername):
        if servername==None or len(servername)==0:
            return None
        # Liste durchsuchen
        for i in range(len(lst_ServerTeemIpCollector)):
            if lst_ServerTeemIpCollector[i][1]==servername:
                return lst_ServerTeemIpCollector[i][2]
        return None

    def get_FARMNAME_2_ORG_NAME(servername):
        if servername==None or len(servername)==0:
            return None
        # Liste durchsuchen
        for i in range(len(lst_HypervisorCollector)):
            if lst_HypervisorCollector[i][5]==servername:
                return lst_HypervisorCollector[i][2]
        return None

    def get_CsvSafe(txt):
        if len(txt)==0 or txt.isalnum():
            return txt
        else:
            return '\"'+txt+'\"'


    # Retrieving IP RANGE LIST
    lst_IpRange=iTopQuery_IpRange()
    if lst_IpRange==None or lst_IpRange==False or len(lst_IpRange)==0:
        return 1

    # FILE 1 vSphereIPv4AddressCollector
    # primary_key;ip;org_id;short_name;status
    print('tsk_cron: processing vSphereIPv4AddressCollector Entries')
    lst_IPv4AddressCollector=[]
    # File LOOP
    cnt_file=1
    while os.path.isfile(csv_File_1_i % str(cnt_file)):
        print('tsk_cron: FILE:', csv_File_1_i % str(cnt_file))
        with open(csv_File_1_i % str(cnt_file)) as csv_file:
            # OPEN FILE
            csv_reader = csv.reader(csv_file, delimiter=';')
            txt_writer = open(csv_File_1_T % str(cnt_file),"w")
            # INDEX 
            idx_ip     = None
            idx_org_id = None
            cnt_line   = 0
            flg_rename = False
            # READING
            for row in csv_reader:
            #   print(str(row))
                if cnt_line==0:
                    # Index bestimmen
                    try:
                        idx_ip    =row.index('ip')
                        idx_org_id=row.index('org_id')
                        cnt_line+=1
                        print ('tsk_cron: CSV NO '+
                               'ip['+str(idx_ip)+'] '+
                               'org_id['+str(idx_org_id)+']')
                    except Exception as e:
                        print(e)
                        break
                    # Inhalt ausgeben
                    for i in range(len(row)):
                        if i<len(row)-1:
                            print(row[i],file=txt_writer, end=';')
                        else:
                            print(row[i],file=txt_writer)
                else:
                    # Inhalt ausgeben
                    inf=[]
                    for i in range(len(row)):
                        # Vorbelegen
                        dat=row[i]
                        # Ersetzen
                        if i==idx_org_id:
                            tmp=get_IP_2_ORG_NAME(row[idx_ip])
                            print ('tsk_cron: ['+str(row[idx_ip])+
                                   '] get_IP_2_ORG_NAME ['+ str(tmp)+']')
                            if tmp!=None and tmp!=dat:
                                dat=tmp
                                flg_rename=True
                        # Speichern
                        inf.append(dat)
                        # Ausgeben
                        if i<len(row)-1:
                            print(dat, file=txt_writer, end=';')
                        else:
                            print(dat, file=txt_writer)
                    # Inhalt speichern
                    lst_IPv4AddressCollector.append(inf)
                    cnt_line+=1
            txt_writer.close()
            # Datei umbenennen
            if flg_rename:
                os.rename(csv_File_1_i % str(cnt_file), csv_File_1_o % str(cnt_file))
                os.rename(csv_File_1_T % str(cnt_file), csv_File_1_i % str(cnt_file))
             #  try:
             #  except OSError as e:
             #      print ("ERROR: %s - %s." % (e.filename, e.strerror))
        #   print(lst_IPv4AddressCollector)
            print('tsk_cron: %s elements' % str(len(lst_IPv4AddressCollector)))
        # Next file
        cnt_file+=1

    # FILE 2 vSphereServerTeemIpCollector
    # primary_key;name;org_id;serialnumber;status;brand_id;model_id;osfamily_id;
    # osversion_id;cpu;ram;managementip_id
    print('tsk_cron: processing vSphereServerTeemIpCollector Entries')
    lst_ServerTeemIpCollector=[]
    # File LOOP
    cnt_file=1
    while os.path.isfile(csv_File_2_i % str(cnt_file)):
        print('tsk_cron: FILE:', csv_File_2_i % str(cnt_file))
        with open(csv_File_2_i % str(cnt_file)) as csv_file:
            # OPEN FILE
            csv_reader = csv.reader(csv_file, delimiter=';')
            txt_writer = open(csv_File_2_T % str(cnt_file),"w")
            # INDEX 
            idx_lookup   = None
            idx_org_id   = None
            idx_special1 = None
            idx_special2 = None
            cnt_line     = 0
            flg_rename   = False
            # READING
            for row in csv_reader:
            #   print(str(row))
                if cnt_line==0:
                    # Index bestimmen
                    try:
                        idx_lookup=row.index('managementip_id')
                        idx_org_id=row.index('org_id')
                        idx_special1=row.index('model_id')
                        idx_special2=row.index('osversion_id')
                        cnt_line+=1
                        print ('tsk_cron: CSV NO '+
                               'managementip_id['+str(idx_lookup)+'] '+
                               'org_id['+str(idx_org_id)+'] '+
                               'model_id['+str(idx_special1)+'] '+
                               'osversion_id['+str(idx_special2)+']')
                    except:
                        break
                    # Inhalt ausgeben
                    for i in range(len(row)):
                        if i<len(row)-1:
                            print(row[i],file=txt_writer, end=';')
                        else:
                            print(row[i],file=txt_writer)
                else:
                    # Inhalt ausgeben
                    inf=[]
                    for i in range(len(row)):
                        # Vorbelegen
                        dat=row[i]
                        # Ersetzen
                        if i==idx_org_id:
                            tmp=get_IP_2_ORG_NAME(row[idx_lookup])
                            print ('tsk_cron: ['+str(row[idx_lookup])+
                                   '] get_IP_2_ORG_NAME ['+ str(tmp)+']')
                            if tmp!=None and tmp!=dat:
                                dat=tmp
                                flg_rename=True
                        # Speichern
                        inf.append(dat);
                        if (i==idx_special1 or i==idx_special2) and len(dat)>0:
                            dat='\"'+dat+'\"'
                        # Ausgeben
                        if i<len(row)-1:
                            print(dat, file=txt_writer, end=';')
                        else:
                            print(dat, file=txt_writer)
                    # Inhalt speichern
                    lst_ServerTeemIpCollector.append(inf)
                    cnt_line+=1
            txt_writer.close()
            # Datei umbenennen
            if flg_rename:
                os.rename(csv_File_2_i % str(cnt_file), csv_File_2_o % str(cnt_file))
                os.rename(csv_File_2_T % str(cnt_file), csv_File_2_i % str(cnt_file))
             #  try:
             #  except OSError as e:
             #      print ("ERROR: %s - %s." % (e.filename, e.strerror))
        #   print(lst_ServerTeemIpCollector)
            print('tsk_cron: %s elements' % str(len(lst_ServerTeemIpCollector)))
        # Next file
        cnt_file+=1

    # FILE 3 vSphereHypervisorCollector
    # primary_key;name;org_id;status;server_id;farm_id
    print('tsk_cron: processing vSphereHypervisorCollector Entries')
    lst_HypervisorCollector=[]
    # File LOOP
    cnt_file=1
    while os.path.isfile(csv_File_3_i % str(cnt_file)):
        print('tsk_cron: FILE:', csv_File_3_i % str(cnt_file))
        with open(csv_File_3_i % str(cnt_file)) as csv_file:
            # OPEN FILE
            csv_reader = csv.reader(csv_file, delimiter=';')
            txt_writer = open(csv_File_3_T % str(cnt_file),"w")
            # INDEX 
            idx_lookup = None
            idx_org_id = None
            cnt_line   = 0
            flg_rename = False
            # READING
            for row in csv_reader:
            #   print(str(row))
                if cnt_line==0:
                    # Index bestimmen
                    try:
                        idx_lookup=row.index('name')
                        idx_org_id=row.index('org_id')
                        cnt_line+=1
                        print ('tsk_cron: CSV NO '+
                               'name['+str(idx_lookup)+'] '+
                               'org_id['+str(idx_org_id)+'] '+']')
                    except:
                        break
                    # Inhalt ausgeben
                    for i in range(len(row)):
                        if i<len(row)-1:
                            print(row[i],file=txt_writer, end=';')
                        else:
                            print(row[i],file=txt_writer)
                else:
                    # Inhalt ausgeben
                    inf=[]
                    for i in range(len(row)):
                        # Vorbelegen
                        dat=row[i]
                        # Ersetzen
                        if i==idx_org_id:
                            tmp=get_SERVERNAME_2_ORG_NAME(row[idx_lookup])
                            print ('tsk_cron: ['+str(row[idx_lookup])+
                                   '] get_SERVERNAME_2_ORG_NAME ['+ str(tmp)+']')
                            if tmp!=None and tmp!=dat:
                                dat=tmp
                                flg_rename=True
                        # Speichern
                        inf.append(dat);
                        # Ausgeben
                        if i<len(row)-1:
                            print(dat, file=txt_writer, end=';')
                        else:
                            print(dat, file=txt_writer)
                    # Inhalt speichern
                    lst_HypervisorCollector.append(inf)
                    cnt_line+=1
            txt_writer.close()
            # Datei umbenennen
            if flg_rename:
                os.rename(csv_File_3_i % str(cnt_file), csv_File_3_o % str(cnt_file))
                os.rename(csv_File_3_T % str(cnt_file), csv_File_3_i % str(cnt_file))
             #  try:
             #  except OSError as e:
             #      print ("ERROR: %s - %s." % (e.filename, e.strerror))
        #   print(lst_HypervisorCollector)
            print('tsk_cron: %s elements' % str(len(lst_HypervisorCollector)))
        # Next file
        cnt_file+=1

    # FILE 4 vSphereFarmCollector
    # primary_key;name;org_id
    print('tsk_cron: processing vSphereFarmCollector Entries')
    lst_FarmCollector=[]
    # File LOOP
    cnt_file=1
    while os.path.isfile(csv_File_4_i % str(cnt_file)):
        print('tsk_cron: FILE:', csv_File_4_i % str(cnt_file))
        with open(csv_File_4_i % str(cnt_file)) as csv_file:
            # OPEN FILE
            csv_reader = csv.reader(csv_file, delimiter=';')
            txt_writer = open(csv_File_4_T % str(cnt_file),"w")
            # INDEX 
            idx_lookup = None
            idx_org_id = None
            cnt_line   = 0
            flg_rename = False
            # READING
            for row in csv_reader:
            #   print(str(row))
                if cnt_line==0:
                    # Index bestimmen
                    try:
                        idx_lookup=row.index('name')
                        idx_org_id=row.index('org_id')
                        cnt_line+=1
                        print ('tsk_cron: CSV NO '+
                               'name['+str(idx_lookup)+'] '+
                               'org_id['+str(idx_org_id)+'] '+']')
                    except:
                        break
                    # Inhalt ausgeben
                    for i in range(len(row)):
                        if i<len(row)-1:
                            print(row[i],file=txt_writer, end=';')
                        else:
                            print(row[i],file=txt_writer)
                else:
                    # Inhalt ausgeben
                    inf=[]
                    for i in range(len(row)):
                        # Vorbelegen
                        dat=row[i]
                        # Ersetzen
                        if i==idx_org_id:
                            tmp=get_FARMNAME_2_ORG_NAME(row[idx_lookup])
                            print ('tsk_cron: ['+str(row[idx_lookup])+
                                   '] get_FARMNAME_2_ORG_NAME ['+ str(tmp)+']')
                            if tmp!=None and tmp!=dat:
                                dat=tmp
                                flg_rename=True
                        # Speichern
                        inf.append(dat);
                        # Ausgeben
                        if i<len(row)-1:
                            print(dat, file=txt_writer, end=';')
                        else:
                            print(dat, file=txt_writer)
                    # Inhalt speichern
                    lst_FarmCollector.append(inf)
                    cnt_line+=1
            txt_writer.close()
            # Datei umbenennen
            if flg_rename:
                os.rename(csv_File_4_i % str(cnt_file), csv_File_4_o % str(cnt_file))
                os.rename(csv_File_4_T % str(cnt_file), csv_File_4_i % str(cnt_file))
             #  try:
             #  except OSError as e:
             #      print ("ERROR: %s - %s." % (e.filename, e.strerror))
        #   print(lst_FarmCollector)
            print('tsk_cron: %s elements' % str(len(lst_FarmCollector)))
        # Next file
        cnt_file+=1

    # FILE 5 vSphereVirtualMachineTeemIpCollector
    # primary_key;name;status;org_id;ram;cpu;osfamily_id;osversion_id;
    # virtualhost_id;description
    print('tsk_cron: processing vSphereVirtualMachineTeemIp Entries')
    lst_VirtualMachineTeemIp=[]
    # File LOOP
    cnt_file=1
    while os.path.isfile(csv_File_5_i % str(cnt_file)):
        print('tsk_cron: FILE:', csv_File_5_i % str(cnt_file))
        with open(csv_File_5_i % str(cnt_file)) as csv_file:
            # OPEN FILE
            csv_reader = csv.reader(csv_file, delimiter=';')
            txt_writer = open(csv_File_5_T % str(cnt_file),"w")
            # INDEX 
            idx_lookup1 = None
            idx_lookup1 = None
            idx_org_id  = None
            idx_special = None
            cnt_line    = 0
            flg_rename  = False
            # READING
            for row in csv_reader:
            #   print(str(row))
                if cnt_line==0:
                    # Index bestimmen
                    try:
                        idx_lookup1 =row.index('name')
                        idx_lookup2 =row.index('virtualhost_id')
                        idx_org_id  =row.index('org_id')
                        idx_special1=row.index('osversion_id')
                        idx_special2=row.index('description')
                        cnt_line+=1
                        print ('tsk_cron: CSV NO '+
                               'name['+str(idx_lookup1)+'] '+
                               'virtualhost_id['+str(idx_lookup2)+'] '+
                               'org_id['+str(idx_org_id)+'] '+
                               'osversion_id['+str(idx_special1)+'] '+
                               'description['+str(idx_special1)+'] '+']')
                    except:
                        break
                    # Inhalt ausgeben
                    for i in range(len(row)):
                        if i<len(row)-1:
                            print(row[i],file=txt_writer, end=';')
                        else:
                            print(row[i],file=txt_writer)
                else:
                    # Inhalt ausgeben
                    inf=[]
                    for i in range(len(row)):
                        # Vorbelegen
                        dat=row[i]
                        # Ersetzen
                        if i==idx_org_id:
                            tmp=get_FARMNAME_2_ORG_NAME(row[idx_lookup1])
                            print ('tsk_cron: ['+str(row[idx_lookup1])+
                                   '] get_FARMNAME_2_ORG_NAME ['+ str(tmp)+']')
                            if tmp!=None and tmp!=dat:
                                dat=tmp
                                flg_rename=True
                            if tmp==None:
                                tmp=get_FARMNAME_2_ORG_NAME(row[idx_lookup2])
                                print ('tsk_cron: ['+str(row[idx_lookup2])+
                                       '] get_FARMNAME_2_ORG_NAME ['+ str(tmp)+']')
                                if tmp!=None and tmp!=dat:
                                    dat=tmp
                                    flg_rename=True
                        # Speichern
                        inf.append(dat);
                        if (i==idx_special1 or i==idx_special2) and len(dat)>0:
                            dat='\"'+dat+'\"'
                        # Ausgeben
                        if i<len(row)-1:
                            print(dat, file=txt_writer, end=';')
                        else:
                            print(dat, file=txt_writer)
                    # Inhalt speichern
                    lst_VirtualMachineTeemIp.append(inf)
                    cnt_line+=1
            txt_writer.close()
            # Datei umbenennen
            if flg_rename:
                os.rename(csv_File_5_i % str(cnt_file), csv_File_5_o % str(cnt_file))
                os.rename(csv_File_5_T % str(cnt_file), csv_File_5_i % str(cnt_file))
             #  try:
             #  except OSError as e:
             #      print ("ERROR: %s - %s." % (e.filename, e.strerror))
        #   print(lst_VirtualMachineTeemIp)
            print('tsk_cron: %s elements' % str(len(lst_VirtualMachineTeemIp)))
        # Next file
        cnt_file+=1

    return 0



''' iTop: Requesting all currently IP ranges in use from iTop.
'''
def iTopQuery_IpRange():
    # REST
    try:
        # REST REQUEST CREATE
        json_data = {
            'operation': 'core/get',
            'class'    : 'IPv4Range',
            'key'      : "SELECT IPv4Range"
        }
        encoded_data = json.dumps(json_data)
        # REST REQUEST TRANSMITT
        res = requests.post(cfg_itop_cr.get('url')+'/webservices/rest.php?version=1.0',
                            verify=False,
                            data={'auth_user': cfg_itop_cr.get('usr'), 
                                  'auth_pwd' : cfg_itop_cr.get('pwd'),
                                  'json_data': encoded_data})
    except:
        print('ERROR...: iTop REST ACCESS FAILED IPv4Range', file=sys.stderr)
        return False    
    # LIST CREATION
    iTop_Lst_IPv4Ranges=[]
    result = json.loads(res.text);
    if result['code'] == 0:
        # Transfering data
        print('tsk_cron: IPv4 Rage List')
        for i in result['objects'].keys():
            iTop_Lst_IPv4Ranges.append([result['objects'][i]['fields']['org_id'],
                                        result['objects'][i]['fields']['org_name'],
                                        result['objects'][i]['fields']['firstip'],
                                        result['objects'][i]['fields']['lastip' ]])
    # No data
#   print (iTop_Lst_IPv4Ranges)
    return iTop_Lst_IPv4Ranges


''' iTop XML SAVE CONFIG
'''
def config_iTop_save(no):
    # import element tree
    import xml.etree.ElementTree as ET 

    def writeELEM(root, name, data):
        # Reading element data
        elems = root.findall(name)
        for elem in elems:
            elem.text=data

    # info
    print('tsk_cron: XML update', file=sys.stdout)
    try:
        #import xml file
        tree = ET.parse(path_iTop)
        root = tree.getroot()
        # Debug
    #   for child in root:
    #       print(child.tag, child.attrib)
        # iTop url usr pwd
        writeELEM(root, "itop_url",         cfg_itop_cr ['url'])
        writeELEM(root, "itop_login",       cfg_itop_cr ['usr'])
        writeELEM(root, "itop_password",    cfg_itop_cr ['pwd'])
        # vSphere iTop
        writeELEM(root, "synchro_user",     cfg_vsphere ['synchro_user'  ])
        writeELEM(root, "default_org_id",   cfg_vsphere ['default_org_id'])
        # vSphere Server        
        writeELEM(root, "vsphere_uri",      cfg_vsphere ['url_'+str(no)])
        writeELEM(root, "vsphere_login",    cfg_vsphere ['usr_'+str(no)])
        writeELEM(root, "vsphere_password", cfg_vsphere ['pwd_'+str(no)])
        # vSphere iTop
        child=tree.find("json_placeholders")
        if child != None:
            writeELEM(child, "prefix", "scan2vmware_"+str(no))
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


''' vSphere query all servers
'''
def access_vSphere():
    # Use global
    global cfg_itop_cr, cfg_vsphere
    # Info
    maxNo=vSphere_Srv_No()
    for no in range(1, maxNo+1):
        # Info
        print('tsk_cron: Accessing server '+str(no)+'v'+str(maxNo), file=sys.stdout)
        # Enabled
        if cfg_vsphere ['doQ_'+str(no)]!=True:
            print('tsk_cron: skipping ...', file=sys.stdout)
        else:
            print('tsk_cron: using ...', file=sys.stdout)
            # XML update
            config_iTop_save(no)
            # PART 1
            # BUILD UPDATE COMMAND
            cmd=('cd itop;php exec.php --configure_only')
            sys.stdout.flush()
            sys.stderr.flush()
            ret=os.system(cmd)
            print('tsk_cron: CONFIGURE RES:',ret)
            # PART 2
            if ret==0:
                # BUILD UPDATE COMMAND
                cmd=('cd itop;php exec.php --collect_only')
                sys.stdout.flush()
                sys.stderr.flush()
                ret=os.system(cmd)
                print('tsk_cron: COLLECT RES:',ret)
            # PART 3
            if ret==0:
                # PATCHING
                ret=csv_patching()
                print('tsk_cron: PATCHING RES:',ret)
            # PART 4
            if ret==0:
                # BUILD UPDATE COMMAND
                cmd=('cd itop;php exec.php --synchro_only')
                sys.stdout.flush()
                sys.stderr.flush()
                ret=os.system(cmd)
                print('tsk_cron: SYNCHRO RES:',ret)


''' GO
'''
if __name__ == "__main__":
    # PROGRAM DATA
    path_PRG, prg_file = os.path.split(os.path.abspath(sys.argv[0]))
    os.chdir(path_PRG)
    print("tsk_cron: prog - "+prg_file)
    print("tsk_cron: path - "+path_PRG)
    # SHOW PARAMETERS
    print('tsk_cron: para - No:'+str(len(sys.argv))+' Str:'+str(sys.argv))
    # SHOW USER ID
    print('tsk_cron: rUID - %d' % os.getuid())
    print('tsk_cron: eUID - %d' % os.geteuid())

    # READ CONFIG
    try:
        with open(cfg_file) as json_file:
            data=json.load(json_file)
    except:
        exit(1)

    # SAVE CONFIG DATA
    cfg_itop_cr = data['iTop'   ][0]
    cfg_vsphere = data['vSphere'][0]
    cfg_crontab = data['Crontab'][0]
    cfg_logfile = data['LogFile'][0]

    # CHECKING CONFIG - iTop
    if cfg_itop_cr == None:
        exit(30)
    # CHECKING CONFIG - vSphere
    if cfg_vsphere == None:
        exit(32)
    # CHECKING CONFIG - CRONTAB ACTION FLAGS
    if cfg_crontab == None:
        exit(33)
    if cfg_crontab['doQuery']==None:
        exit(34)
    if cfg_crontab['doClean']==None:
        exit(35)
    # CHECKING CONFIG - LOGFILES
    if cfg_logfile['number']==None or int(cfg_logfile['number'])==0:
        exit(50)
    if cfg_logfile['age'   ]==None or int(cfg_logfile['age'   ])==0:
        exit(51)

    # TIMESTAMP
    tst='{:%Y-%m-%d--%H-%M-%S}'.format(datetime.datetime.now())
    print('tsk_cron: START TIME STAMP ',tst) 
    # UPDATE status
    json_inf={"tst_st":tst, "tst_sp":'', "status":'RUNNING'}
    with open(inf_file, 'w') as outfile:
        json.dump(json_inf, outfile)

    if len(sys.argv)==1 and cfg_crontab['doQuery']==True:
        # Info
        print('tsk_cron: Start retrieving VMware data.', file=sys.stdout)
        # Check all selected servers
        access_vSphere()
        # Info
        print('tsk_cron: Stop retrieving VMware data.', file=sys.stdout)

    if len(sys.argv)==1 and cfg_crontab['doClean']==True:
        # Info
        print('tsk_cron: Removing outdated log files.', file=sys.stdout)
        # Get current time and date.
        now=datetime.datetime.today()
        # CleanUp of HTML Log File Directory
        lib_logs.delOldLogFiles(now, path_HTML, 'html', cfg_logfile['number'], cfg_logfile['age'])
        # CleanUp of XML Log File Directory
        lib_logs.delOldLogFiles(now, path_XML,  'xml', cfg_logfile['number'], cfg_logfile['age'])

    if len(sys.argv)>1 and not sys.argv[1].isdigit():
        print('tsk_cron: TESTING PATCHING', file=sys.stdout)
        ret=csv_patching()
        print('tsk_cron: PATCHING RES:',ret)

    if len(sys.argv)>1 and sys.argv[1].isdigit():
        # Info
        maxNo=vSphere_Srv_No()
        selNo=int(sys.argv[1])
        if selNo>=1 and selNo<=maxNo:
            # Info
            print('tsk_cron: Accessing server '+str(selNo)+'v'+str(maxNo), file=sys.stdout)
            # XML update
            config_iTop_save(selNo)
            # PART 1
            # BUILD UPDATE COMMAND
            cmd=('cd itop;php exec.php --configure_only')
            sys.stdout.flush()
            sys.stderr.flush()
            ret=os.system(cmd)
            print('tsk_cron: CONFIGURE RES:',ret)
            # PART 2
            if ret==0:
                # BUILD UPDATE COMMAND
                cmd=('cd itop;php exec.php --collect_only')
                sys.stdout.flush()
                sys.stderr.flush()
                ret=os.system(cmd)
                print('tsk_cron: COLLECT RES:',ret)
            # PART 3
            if ret==0:
                # PATCHING
                ret=csv_patching()
                print('tsk_cron: PATCHING RES:',ret)
            # PART 4
            if ret==0:
                # BUILD UPDATE COMMAND
                cmd=('cd itop;php exec.php --synchro_only')
                sys.stdout.flush()
                sys.stderr.flush()
                ret=os.system(cmd)
                print('tsk_cron: SYNCHRO RES:',ret)

    # TIMESTAMP
    tnd='{:%Y-%m-%d--%H-%M-%S}'.format(datetime.datetime.now())
    print('tsk_cron: STOP TIME STAMP ',tnd) 
    # UPDATE status
    json_inf={"tst_st":tst, "tst_sp":tnd, "status":'STAND BY'}
    with open(inf_file, 'w') as outfile:
        json.dump(json_inf, outfile)

    # UPDATE TIME MARKER
    json_log={}
    json_log['cur']=[]
    json_log['cur'].append(tst+' [UID:'+str(os.getuid()).__str__()+'/EUID:'+str(os.geteuid())+']')
    json_log['lst']=[]
    try:
        with open(log_file) as json_file:
            data=json.load(json_file)
            json_log['lst'].append(data['cur'][0])
    except:
        json_log['lst'].append("")
    with open(log_file, 'w') as outfile:
        json.dump(json_log, outfile)

    # READY
    exit(0)
