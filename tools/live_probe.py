"""Least-privilege real Firebase probe. No administrator credentials; no motor or schedules.
Credentials are read only from ignored local files and are never printed.
"""
import json, time, uuid, urllib.request, urllib.error, urllib.parse, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
report={'projectId':'pastillerobadi','databaseUrl':'https://pastillerobadi-default-rtdb.firebaseio.com',
    'hardwareUsed':False,'tests':{},'status':'PENDING'}
def save():
    (ROOT/'reports/firebase-setup').mkdir(parents=True,exist_ok=True)
    (ROOT/'reports/firebase-setup/live-probe.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
def http(url,method='GET',value=None):
    req=urllib.request.Request(url,data=None if value is None else json.dumps(value).encode(),method=method,
        headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=20) as response: return response.status,json.load(response)
    except urllib.error.HTTPError as error:
        return error.code,None
def run():
    code,_=http(report['databaseUrl']+'/devices/pastillero-01.json')
    report['tests']['anonymousReadDenied']=code in (401,403)
    code,_=http(report['databaseUrl']+'/validation/public-write-probe.json','PUT',{'testOnly':True})
    report['tests']['anonymousWriteDenied']=code in (401,403)
    p=ROOT/'app/google-services.json'
    if not p.exists(): report['pending']='Official google-services.json has not been saved'; return
    public=json.loads(p.read_text(encoding='utf-8-sig'))
    if public['project_info']['project_id']!='pastillerobadi': raise ValueError('Wrong Firebase project')
    client=next(c for c in public['client'] if c['client_info']['android_client_info']['package_name']=='mx.edu.badi.pastillero')
    key=client['api_key'][0]['current_key']
    credentials={}
    for line in (ROOT/'private/integration.local.properties').read_text(encoding='utf-8-sig').splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            k,v=line.split('=',1); credentials[k.strip()]=v if k.strip().endswith('.password') else v.strip()
    if not all(credentials.get(role+'.'+field) for role in ('owner','device') for field in ('email','password')):
        report['pending']='Personal account credentials are not complete in local private file'; return
    identities={}
    for role in ('owner','device'):
        code,body=http('https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key='+urllib.parse.quote(key),
            'POST',{'email':credentials[role+'.email'],'password':credentials[role+'.password'],'returnSecureToken':True})
        report['tests'][role+'Authentication']=code==200
        if code!=200: report['pending']='Authentication failed for '+role+' (no credential values logged)'; return
        identities[role]=body
    mapping={'devices':{'pastillero-01':{'ownerUid':identities['owner']['localId'],'deviceUid':identities['device']['localId']}}}
    (ROOT/'private/provision-identities.json').write_text(json.dumps(mapping,indent=2),encoding='utf-8')
    def db(role,path,method='GET',body=None):
        return http(report['databaseUrl']+'/devices/pastillero-01/'+path+'.json?auth='+
            urllib.parse.quote(identities[role]['idToken']),method,body)
    code,_=db('owner','ownerUid'); report['tests']['ownerRead']=code==200
    code,_=db('device','deviceUid'); report['tests']['deviceRead']=code==200
    if not report['tests']['ownerRead'] or not report['tests']['deviceRead']:
        report['pending']='Publish reviewed rules and provision the two UIDs using private/provision-identities.json'; return
    def global_db(role,path,method='GET',body=None):
        return http(report['databaseUrl']+'/'+path+'.json?auth='+
            urllib.parse.quote(identities[role]['idToken']),method,body)
    owner_uid=identities['owner']['localId']; device_uid=identities['device']['localId']
    code,own_access=global_db('owner','access/users/'+owner_uid)
    report['tests']['ownerOwnAccessEnabled']=code==200 and isinstance(own_access,dict) and own_access.get('enabled') is True
    code,_=global_db('owner','access/users/'+owner_uid+'/enabled','PUT',True)
    report['tests']['ownerCannotChangeOwnAccess']=code in (401,403)
    code,_=global_db('owner','access/users/'+device_uid)
    report['tests']['ownerCannotReadOtherAccountAccess']=code in (401,403)
    code,_=global_db('device','access/users')
    report['tests']['deviceCannotReadAccountDirectory']=code in (401,403)
    for role in ('owner','device'):
        code,_=global_db(role,'devices')
        report['tests'][role+'CannotReadAllDevices']=code in (401,403)
        code,_=global_db(role,'administration')
        report['tests'][role+'CannotReadAdministration']=code in (401,403)
    command_id='qa-'+uuid.uuid4().hex
    now=int(time.time()*1000)
    command={'type':'PING','requestedBy':identities['owner']['localId'],'requestedAt':now,'expiresAt':now+600000,
        'targetMode':'simulation','planRevision':0}
    code,_=db('device','commandRequests/'+command_id,'PUT',command)
    report['tests']['deviceCannotRequest']=code in (401,403)
    code,_=db('owner','commandRequests/'+command_id,'PUT',command)
    report['tests']['ownerRequest']=code==200
    code,_=db('owner','commandRequests/'+command_id,'PUT',command)
    report['tests']['identicalRequestRetry']=code==200
    code,received=db('device','commandRequests/'+command_id)
    report['tests']['deviceReceivesRequest']=code==200 and received==command
    code,_=db('owner','commandRequests/'+command_id,'PUT',{**command,'type':'DISPENSE'})
    report['tests']['invalidCommandRejected']=code in (401,403)
    bridge=ROOT/'reports/command-bridge.exe'
    if bridge.exists() and report['tests']['deviceReceivesRequest']:
        decision=subprocess.check_output([str(bridge),'PING','simulation','1',str(now),str(now+600000),str(int(time.time()*1000)),'0','0'],text=True).strip()
        report['tests']['firmwareCppCommandValidatorOnPC']=decision=='OK'
    report['status']='PASS' if all(report['tests'].values()) else 'FAIL'
    report['limitations']=['No ESP32 firmware execution on silicon','No Android APK network test in this probe',
        'No Wi-Fi outage tested by this probe','PING requests are marked qa-* and simulation; no schedule or dose event written']
try: run()
except Exception as error:
    report['status']='ERROR'; report['errorType']=type(error).__name__  # Never print URLs/tokens/response bodies.
finally:
    save(); print('Firebase live probe:',report['status']); print('Report: reports/firebase-setup/live-probe.json')
