import { readFileSync, existsSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { resolve } from 'node:path';
import { after, before, beforeEach, test } from 'node:test';
import assert from 'node:assert/strict';
import { initializeTestEnvironment, assertFails, assertSucceeds } from '@firebase/rules-unit-testing';
import { ref, set, get, update, runTransaction, goOffline, goOnline } from 'firebase/database';
let env;
const path='devices/pastillero-01';
const at=()=>Date.now()+3600000;
const plan=(revision=1,id='dose-1')=>({targetMode:'simulation',revision,token:'draft-'+revision,doses:{[id]:{scheduledAt:at(),compartment:1}}});
const event=()=>({doseId:'dose-1',type:'STARTED',scheduledAt:at(),actualAt:Date.now(),compartment:1,simulation:true});
const db=uid=>env.authenticatedContext(uid,{auth_time:Math.floor(Date.now()/1000)}).database();
const command=(type='PING')=>{const now=Date.now();return {type,requestedBy:'owner',requestedAt:now,expiresAt:now+600000,targetMode:'simulation',planRevision:type==='PING'?0:2};};
const result=c=>({status:'COMPLETED',reason:'OK',requestedAt:c.requestedAt,executedAt:Date.now(),planRevision:2,simulation:true});
before(async()=>{env=await initializeTestEnvironment({projectId:'demo-pastillero',database:{host:'127.0.0.1',port:9009,rules:readFileSync('database.rules.json','utf8')}});});
beforeEach(async()=>{await env.clearDatabase();await env.withSecurityRulesDisabled(async c=>set(ref(c.database()),{devices:{'pastillero-01':{ownerUid:'owner',deviceUid:'device'}},access:{users:{owner:{role:'owner',enabled:true,revokedAt:0,version:1},device:{role:'device',enabled:true,revokedAt:0,version:1}}}}));});
after(async()=>{await env?.cleanup();});

const v2path=path+'/v2';
const v2settings=(positions=5)=>({positions,horizonDays:7,pumpDurationMs:2000,ledEnabled:true,buzzerEnabled:true,lcdEnabled:false,exitSensorEnabled:false,servoEnabled:false,pumpEnabled:false});
const v2plan=()=>{const t=at();return {version:2,revision:1,token:'v2-one',targetMode:'simulation',positions:5,settings:v2settings(),windowStart:t,windowEnd:t+604800000,
  regimens:{'med-a':{id:'med-a',name:'Pauta QA',mode:'daily',times:['08:00'],zoneId:'UTC',compartment:4,intervalMinutes:480,startAt:t,endAt:0,enabled:true}},
  doses:{'v2-dose':{medicationId:'med-a',scheduledAt:t,compartment:4}}};};

test('V2 five spaces reserve zero and permit the fourth medicine compartment',async()=>{
  await assertSucceeds(set(ref(db('owner'),v2path+'/program'),v2plan()));
  assert.equal((await get(ref(db('device'),v2path+'/program/positions'))).val(),5);
  assert.equal((await get(ref(db('device'),path+'/plan'))).exists(),false);
});
test('V2 four-position compatibility rejects compartment four and zero',async()=>{
  const p=v2plan();p.positions=4;p.settings.positions=4;await assertFails(set(ref(db('owner'),v2path+'/program'),p));
  p.positions=p.settings.positions=5;p.doses['v2-dose'].compartment=0;await assertFails(set(ref(db('owner'),v2path+'/program'),p));
});
test('V2 anonymous, foreign account and device cannot publish programs',async()=>{
  await assertFails(get(ref(env.unauthenticatedContext().database(),v2path)));
  await assertFails(get(ref(db('stranger'),v2path)));
  await assertFails(set(ref(db('device'),v2path+'/program'),v2plan()));
});
test('V2 invalid protocol, preferences and extra credential fields are denied',async()=>{
  const q=ref(db('owner'),v2path+'/program');let p=v2plan();p.version=1;await assertFails(set(q,p));
  p=v2plan();p.settings.pumpDurationMs=5001;await assertFails(set(q,p));
  p=v2plan();p.settings.buzzerEnabled='yes';await assertFails(set(q,p));
  p=v2plan();p.password='not-a-real-secret';await assertFails(set(q,p));
});
test('V2 dose identity is immutable across revisions and cannot detach from medicine',async()=>{
  const q=ref(db('owner'),v2path+'/program'),p=v2plan();await assertSucceeds(set(q,p));
  const next=structuredClone(p);next.revision=2;next.token='v2-two';await assertSucceeds(set(q,next));
  next.revision=3;next.token='v2-three';next.doses['v2-dose'].scheduledAt+=1000;await assertFails(set(q,next));
});
test('V2 validates medication reference and matching compartment',async()=>{
  const q=ref(db('owner'),v2path+'/program');let p=v2plan();p.doses['v2-dose'].medicationId='missing';await assertFails(set(q,p));
  p=v2plan();p.regimens['med-a'].compartment=2;await assertFails(set(q,p));
});
test('V2 new exit failure event is immutable and only device can record it',async()=>{
  const e={...event(),doseId:'v2-dose',type:'NO_EXIT',medicationId:'med-a',compartment:4};
  const key=v2path+'/events/v2-dose-SIM-NO_EXIT';await assertFails(set(ref(db('owner'),key),e));
  await assertSucceeds(set(ref(db('device'),key),e));await assertSucceeds(set(ref(db('device'),key),e));
  await assertFails(set(ref(db('device'),key),{...e,medicationId:'different'}));
});
test('V2 telemetry requires protocol, positions and boolean peripheral states',async()=>{
  const s={phase:0,calibrated:false,appliedRevision:0,updatedAt:Date.now(),simulation:true,storageHealthy:true,blisterPresent:true,protocolVersion:2,positions:5,exitDetected:false,pumpActive:false,servoOpen:false};
  await assertFails(set(ref(db('owner'),v2path+'/state'),s));await assertSucceeds(set(ref(db('device'),v2path+'/state'),s));
  await assertFails(set(ref(db('device'),v2path+'/state'),{...s,positions:6}));
  await assertFails(set(ref(db('device'),v2path+'/state'),{...s,pumpActive:'yes'}));
});
test('V2 transaction retry recognizes same token without an extra revision',async()=>{
  const owner=db('owner'),q=ref(owner,v2path+'/program'),p=v2plan();goOffline(owner);const queued=set(q,p);goOnline(owner);await assertSucceeds(queued);
  const result=await runTransaction(q,current=>current?.token===p.token?undefined:{...p,revision:2});
  assert.equal(result.committed,false);assert.equal((await get(q)).child('revision').val(),1);
});
test('V2 mode change requires clearing existing future schedules first',async()=>{
  const q=ref(db('owner'),v2path+'/program'),p=v2plan();await assertSucceeds(set(q,p));
  await assertFails(set(q,{...p,revision:2,token:'hardware-change',targetMode:'hardware'}));
  await assertSucceeds(set(q,{...p,revision:2,token:'cleared',doses:null,regimens:null}));
  await assertSucceeds(set(q,{...p,revision:3,token:'mode-ready',targetMode:'hardware',doses:null,regimens:null}));
});
test('V2 PING results use V2 request identity and cannot confirm a dose',async()=>{
  const c=command();await assertSucceeds(set(ref(db('owner'),v2path+'/commandRequests/v2-ping'),c));
  await assertSucceeds(set(ref(db('device'),v2path+'/commandResults/simulation/v2-ping'),{...result(c),planRevision:0}));
  assert.equal((await get(ref(db('owner'),v2path+'/events'))).exists(),false);
  await assertFails(set(ref(db('owner'),v2path+'/commandRequests/bad'),{...c,type:'DISPENSE'}));
});
test('V2 access revocation cuts both client roles without changing local history',async()=>{
  await env.withSecurityRulesDisabled(async c=>set(ref(c.database(),'access/users/owner/enabled'),false));
  await assertFails(set(ref(db('owner'),v2path+'/program'),v2plan()));
  await env.withSecurityRulesDisabled(async c=>set(ref(c.database(),'access/users/device/enabled'),false));
  await assertFails(get(ref(db('device'),v2path)));
});

test('owner requests a command; device responds; retries are immutable and separate from dose confirmation',async()=>{
  const c=command(), q=ref(db('owner'),path+'/commandRequests/ping-1');
  await assertSucceeds(set(q,c)); await assertSucceeds(set(q,c));
  await assertFails(set(q,{...c,type:'APPLY_PLAN',planRevision:2})); await assertFails(set(q,null));
  const r=ref(db('device'),path+'/commandResults/simulation/ping-1'), value=result(c);
  await assertSucceeds(set(r,value)); await assertSucceeds(set(r,value));
  await assertFails(set(r,{...value,executedAt:value.executedAt+1})); await assertFails(set(r,null));
  await assertFails(set(ref(db('owner'),path+'/commandResults/simulation/ping-1'),value));
  assert.equal((await get(ref(db('owner'),path+'/events'))).exists(),false);
});
test('invalid, expired, oversized TTL and impersonated commands are denied',async()=>{
  const q=ref(db('owner'),path+'/commandRequests/bad'), c=command();
  await assertFails(set(q,{...c,type:'DISPENSE'}));
  await assertFails(set(q,{...c,requestedBy:'device'}));
  await assertFails(set(q,{...c,expiresAt:c.requestedAt+600001}));
  await assertFails(set(q,{...c,requestedAt:Date.now()-1200000,expiresAt:Date.now()-600000}));
  await assertFails(set(q,{...c,targetMode:'all'}));
  await assertFails(set(q,{...c,planRevision:1}));
  await assertFails(set(q,{...c,extra:true}));
  await assertFails(set(ref(db('device'),path+'/commandRequests/device-forged'),c));
});
test('results require matching request and cannot claim another mode or unapplied revision',async()=>{
  const c=command('APPLY_PLAN'); await set(ref(db('owner'),path+'/commandRequests/apply'),c);
  await assertFails(set(ref(db('device'),path+'/commandResults/hardware/apply'),{...result(c),simulation:false}));
  await assertFails(set(ref(db('device'),path+'/commandResults/simulation/no-request'),result(c)));
  const r=ref(db('device'),path+'/commandResults/simulation/apply');
  await assertFails(set(r,{...result(c),simulation:false}));
  await assertFails(set(r,{...result(c),planRevision:1}));
  await assertFails(set(r,{...result(c),requestedAt:c.requestedAt+1}));
  await assertSucceeds(set(r,result(c)));
});
test('offline queue reconnects with one stable request; repeated upload produces one cloud entry',async()=>{
  const owner=db('owner'), c=command(); const q=ref(owner,path+'/commandRequests/reconnect-id');
  goOffline(owner);
  const queued=set(q,c); goOnline(owner); await assertSucceeds(queued);
  await assertSucceeds(set(q,c));
  const snapshot=await get(ref(db('device'),path+'/commandRequests'));
  assert.equal(snapshot.size,1); assert.equal(snapshot.child('reconnect-id/type').val(),'PING');
});

test('Firebase emulator request is processed by the real firmware C++ command validator on PC',
  {skip:!existsSync('../reports/command-bridge.exe')},async()=>{
  const c=command('APPLY_PLAN');
  await set(ref(db('owner'),path+'/plan'),{targetMode:'simulation',revision:1,token:'draft-one'});
  await set(ref(db('owner'),path+'/plan'),{targetMode:'simulation',revision:2,token:'draft-two'});
  await set(ref(db('owner'),path+'/commandRequests/bridge'),c);
  const received=(await get(ref(db('device'),path+'/commandRequests/bridge'))).val();
  const applied=(await get(ref(db('device'),path+'/plan/revision'))).val();
  const reason=execFileSync(resolve('../reports/command-bridge.exe'),[received.type,received.targetMode,'1',
      String(received.requestedAt),String(received.expiresAt),String(Date.now()),String(received.planRevision),String(applied)],{encoding:'utf8'}).trim();
  assert.equal(reason,'OK');
  await set(ref(db('device'),path+'/commandResults/simulation/bridge'),{...result(c),reason,planRevision:applied});
  assert.equal((await get(ref(db('owner'),path+'/commandResults/simulation/bridge/status'))).val(),'COMPLETED');
});
test('anonymous and unrelated user cannot read',async()=>{
  await assertFails(get(ref(env.unauthenticatedContext().database(),path)));
  await assertFails(get(ref(db('stranger'),path)));
});
test('owner publishes and device reads',async()=>{
  await assertSucceeds(set(ref(db('owner'),path+'/plan'),plan()));
  await assertSucceeds(get(ref(db('device'),path+'/plan')));
});
test('device cannot modify schedules and owner cannot impersonate physical confirmation',async()=>{
  await assertFails(set(ref(db('device'),path+'/plan'),plan()));
  await assertFails(set(ref(db('owner'),path+'/events/dose-1-SIM-STARTED'),event()));
});
test('immutable events accept identical retry and reject tamper or deletion',async()=>{
  const r=ref(db('device'),path+'/events/dose-1-SIM-STARTED');const e=event();
  await assertSucceeds(set(r,e));await assertSucceeds(set(r,e));
  await assertFails(set(r,{...e,actualAt:e.actualAt+1}));await assertFails(set(r,null));
});
test('simulation cannot reserve the physical event key',async()=>{
  const database=db('device'), e=event();
  await assertFails(set(ref(database,path+'/events/dose-1-STARTED'),e));
  await assertSucceeds(set(ref(database,path+'/events/dose-1-SIM-STARTED'),e));
  await assertSucceeds(set(ref(database,path+'/events/dose-1-STARTED'),{...e,simulation:false}));
});
test('identity mapping cannot be changed by clients',async()=>{
  await assertFails(set(ref(db('owner'),path+'/deviceUid'),'owner'));
  await assertFails(set(ref(db('device'),path+'/ownerUid'),'device'));
});
test('invalid compartment, missing fields and unknown fields are rejected',async()=>{
  const r=ref(db('owner'),path+'/plan');const p=plan();p.doses['dose-1'].compartment=4;
  await assertFails(set(r,p));await assertFails(set(r,{revision:1}));
  await assertFails(set(r,{...plan(),admin:true}));
});
test('revision prevents stale writer and permits increment',async()=>{
  const r=ref(db('owner'),path+'/plan');await assertSucceeds(set(r,plan()));
  await assertFails(set(r,plan()));await assertSucceeds(set(r,plan(2,'dose-2')));
});
test('nested writes cannot bypass plan revision',async()=>{
  const database=db('owner');await set(ref(database,path+'/plan'),plan());
  await assertFails(set(ref(database,path+'/plan/doses/injected'),{scheduledAt:at()+600000,compartment:2}));
  await assertFails(set(ref(database,path+'/plan/doses/dose-1'),null));
});
test('existing dose cannot be silently rescheduled with the same ID',async()=>{
  const r=ref(db('owner'),path+'/plan');const p=plan();await set(r,p);
  await assertFails(set(r,{...p,revision:2,doses:{'dose-1':{scheduledAt:at()+600000,compartment:2}}}));
});
test('empty plan is supported and whole-plan deletion is denied',async()=>{
  const r=ref(db('owner'),path+'/plan');await assertSucceeds(set(r,{targetMode:'simulation',revision:1,token:'empty'}));
  await assertFails(set(r,null));
});

test('changing plan mode requires clearing all old schedules first',async()=>{
  const r=ref(db('owner'),path+'/plan'); const p=plan(); await set(r,p);
  await assertFails(set(r,{...p,targetMode:'hardware',revision:2}));
  await assertSucceeds(set(r,{targetMode:'simulation',revision:2,token:'cleared'}));
  await assertSucceeds(set(r,{...plan(3,'hardware-dose'),targetMode:'hardware'}));
  await assertFails(set(r,{...plan(4,'bad-mode'),targetMode:'all'}));
});
test('old newly introduced dose and future event timestamps are rejected',async()=>{
  const p=plan();p.doses['dose-1'].scheduledAt=Date.now()-1;
  await assertFails(set(ref(db('owner'),path+'/plan'),p));
  await assertFails(set(ref(db('device'),path+'/events/dose-1-SIM-STARTED'),{...event(),actualAt:Date.now()+120000}));
});
test('concurrent editors preserve a single winner',async()=>{
  const a=db('owner'),b=env.authenticatedContext('owner',{auth_time:Math.floor(Date.now()/1000)}).database();
  let results=await Promise.allSettled([set(ref(a,path+'/plan'),plan(1,'a')),set(ref(b,path+'/plan'),plan(1,'b'))]);
  assert.equal(results.filter(r=>r.status==='fulfilled').length,1);
  assert.equal((await get(ref(a,path+'/plan/revision'))).val(),1);
});


test('revocation denies a still-valid owner token immediately; clients cannot re-enable themselves',async()=>{
  const owner=db('owner'); await assertSucceeds(get(ref(owner,path)));
  await env.withSecurityRulesDisabled(async c=>update(ref(c.database(),'access/users/owner'),{enabled:false,revokedAt:Math.floor(Date.now()/1000)}));
  await assertFails(get(ref(owner,path))); await assertFails(set(ref(owner,path+'/plan'),plan()));
  await assertFails(set(ref(owner,'access/users/owner/enabled'),true));
  assert.equal((await get(ref(owner,'access/users/owner/enabled'))).val(),false);
  await assertSucceeds(get(ref(db('device'),path)));
});
test('ordinary accounts cannot read other access records or administrative audit',async()=>{
  await assertFails(get(ref(db('owner'),'access/users/device')));
  await assertFails(get(ref(db('device'),'access/users')));
  await assertFails(get(ref(db('owner'),'administration')));
  await assertFails(set(ref(db('owner'),'administration/protectedAdminUid'),'owner'));
});
test('clients cannot acquire dashboard authority by claims or metadata',async()=>{
  const forged=env.authenticatedContext('stranger',{dashboardAdmin:true}).database();
  await assertFails(get(ref(forged,'devices')));
  await assertFails(set(ref(db('owner'),'access/users/owner/role'),'admin'));
  await assertFails(get(ref(env.authenticatedContext('primary',{dashboardAdmin:true}).database(),'devices')));
});
test('revoked device loses cloud access without changing owner privileges',async()=>{
  await env.withSecurityRulesDisabled(async c=>update(ref(c.database(),'access/users/device'),{enabled:false}));
  await assertFails(get(ref(db('device'),path)));
  await assertFails(set(ref(db('device'),path+'/events/dose-1-SIM-STARTED'),event()));
  await assertSucceeds(get(ref(db('owner'),path)));
});
test('reenabling does not revive a token from before the session cutoff',async()=>{
  const cutoff=Math.floor(Date.now()/1000);
  await env.withSecurityRulesDisabled(async c=>update(ref(c.database(),'access/users/owner'),{enabled:true,revokedAt:cutoff}));
  await assertFails(get(ref(env.authenticatedContext('owner',{auth_time:cutoff-1}).database(),path)));
  await assertSucceeds(get(ref(env.authenticatedContext('owner',{auth_time:cutoff+1}).database(),path)));
});
test('missing access entry is denied even for a UID bound to the device',async()=>{
  await env.withSecurityRulesDisabled(async c=>set(ref(c.database(),'access/users/owner'),null));
  await assertFails(get(ref(db('owner'),path)));
});
