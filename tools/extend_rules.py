"""Generate command rules without changing existing plan/event permissions."""
import json
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'firebase/database.rules.json'
j=json.loads(p.read_text(encoding='utf-8-sig')); d=j['rules']['devices']['$device']
d['plan']['.validate']="newData.hasChildren(['revision','token','targetMode']) && ((!data.exists() && newData.child('revision').val() === 1) || newData.child('revision').val() === data.child('revision').val() + 1) && (!data.exists() || newData.child('targetMode').val() === data.child('targetMode').val() || !data.child('doses').exists())"
d['plan']['targetMode']={'.validate':"newData.val() === 'simulation' || newData.val() === 'hardware'"}
owner="auth != null && auth.uid === root.child('devices').child($device).child('ownerUid').val()"
device="auth != null && auth.uid === root.child('devices').child($device).child('deviceUid').val()"
def immutable(fields):
    return "(!data.exists() || ("+' && '.join(f"newData.child('{f}').val() === data.child('{f}').val()" for f in fields)+"))"
fields=['type','requestedBy','requestedAt','expiresAt','targetMode','planRevision']
d['commandRequests']={'.indexOn':['requestedAt'],'$command':{
    '.write':owner+' && newData.exists() && '+immutable(fields),
    '.validate':"$command.matches(/^[A-Za-z0-9-]{1,36}$/) && newData.hasChildren("+str(fields).replace(' ', '')+") && (newData.child('type').val() === 'PING' ? newData.child('planRevision').val() === 0 : newData.child('planRevision').val() >= 1)",
    'type':{'.validate':"newData.val() === 'PING' || newData.val() === 'APPLY_PLAN'"},
    'requestedBy':{'.validate':"newData.val() === auth.uid"},
    'targetMode':{'.validate':"newData.val() === 'simulation' || newData.val() === 'hardware'"},
    'planRevision':{'.validate':"newData.isNumber() && newData.val() % 1 === 0 && newData.val() >= 0 && newData.val() < 2000000000"},
    'requestedAt':{'.validate':"newData.isNumber() && newData.val() % 1 === 0 && (data.exists() || (newData.val() >= now - 60000 && newData.val() <= now + 60000))"},
    'expiresAt':{'.validate':"newData.isNumber() && newData.val() % 1 === 0 && newData.val() > newData.parent().child('requestedAt').val() && newData.val() <= newData.parent().child('requestedAt').val() + 600000"},
    '$other':{'.validate':False}}}
request="root.child('devices').child($device).child('commandRequests').child($command)"
fields=['status','reason','requestedAt','executedAt','planRevision','simulation']
d['commandResults']={'$mode':{
    '.indexOn':['executedAt'],
    '$command':{
    '.write':device+' && newData.exists() && '+immutable(fields),
    '.validate':"newData.hasChildren("+str(fields).replace(' ', '')+") && ($mode === 'simulation' || $mode === 'hardware') && "+request+".exists() && "+request+".child('targetMode').val() === $mode && newData.child('requestedAt').val() === "+request+".child('requestedAt').val() && newData.child('simulation').val() === ($mode === 'simulation') && (newData.child('status').val() !== 'COMPLETED' || (newData.child('reason').val() === 'OK' && ("+request+".child('type').val() === 'PING' || newData.child('planRevision').val() >= "+request+".child('planRevision').val())))",
    'status':{'.validate':"newData.val() === 'COMPLETED' || newData.val() === 'REJECTED'"},
    'reason':{'.validate':"newData.val() === 'OK' || newData.val() === 'EXPIRED_OR_INVALID_TIME' || newData.val() === 'INVALID_REVISION' || newData.val() === 'UNKNOWN_COMMAND'"},
    'requestedAt':{'.validate':"newData.isNumber() && newData.val() % 1 === 0"},
    'executedAt':{'.validate':"newData.isNumber() && newData.val() % 1 === 0 && newData.val() >= newData.parent().child('requestedAt').val() - 60000 && newData.val() <= now + 60000"},
    'planRevision':{'.validate':"newData.isNumber() && newData.val() % 1 === 0 && newData.val() >= 0 && newData.val() < 2000000000"},
    'simulation':{'.validate':"newData.isBoolean()"},
    '$other':{'.validate':False}}}}
p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
