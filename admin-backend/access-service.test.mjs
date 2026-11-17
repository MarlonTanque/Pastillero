import {test} from 'node:test';
import assert from 'node:assert/strict';
import {AccessService} from './access-service.mjs';
function fixture() {
  const rows={owner:{role:'owner',enabled:true,version:1,revokedAt:0},device:{role:'device',enabled:true,version:1,revokedAt:0}};
  const calls=[],audit=[];
  const auth={
    async verifyIdToken(token,revoked) {assert.equal(revoked,true);if(token==='revoked') throw Error('revoked');return token==='admin'?{uid:'primary',dashboardAdmin:true}:{uid:token,dashboardAdmin:token==='impostor'};},
    async getUser(uid) {return {uid,customClaims:uid==='secondary'?{dashboardAdmin:true}:{}};},
    async updateUser(uid,value) {calls.push([uid,value]);},
    async revokeRefreshTokens(uid) {calls.push(['revoke',uid]);},
    async listUsers() {return {users:[{uid:'owner',email:'owner@example.test',disabled:false}]};}
  };
  const store={async readAccess(uid){return rows[uid]??null;},async readDevices(){return {'device-1':{}};},
    async changeAccess(uid,version,transform){if(rows[uid].version!==version)return null;return rows[uid]=transform(rows[uid]);},async audit(event){audit.push(event);}};
  return {service:new AccessService({auth,store,protectedAdminUid:'primary',now:()=>1800000000000}),rows,calls,audit,auth};
}
test('administrator must have both the protected UID and server-issued claim',async()=>{
  const {service}=fixture();
  for(const token of ['owner','device','impostor','primary']) await assert.rejects(()=>service.overview(token),{status:403});
  assert.deepEqual(await service.overview('admin'),{'device-1':{}});
});
test('revoked administrative sessions are denied',async()=>{await assert.rejects(()=>fixture().service.overview('revoked'),{status:401});});
test('owner and device cannot administer access',async()=>{
  const {service,rows}=fixture();await assert.rejects(()=>service.changeAccess('owner','device',{enabled:false,expectedVersion:1}),{status:403});assert.equal(rows.device.enabled,true);
});
test('primary and other administrative accounts cannot be disabled by this API',async()=>{
  const {service}=fixture();for(const uid of ['primary','secondary']) await assert.rejects(()=>service.changeAccess('admin',uid,{enabled:false,expectedVersion:1}),{status:409});
});
test('disable closes database permission, invalidates sessions and records audit',async()=>{
  const {service,rows,calls,audit}=fixture();await service.changeAccess('admin','owner',{enabled:false,expectedVersion:1});
  assert.equal(rows.owner.enabled,false);assert.equal(rows.owner.revokedAt,1800000000);assert.equal(rows.owner.version,2);
  assert.deepEqual(calls,[['owner',{disabled:true}],['revoke','owner']]);assert.equal(audit.length,2);
});
test('auth failure after disable never restores database permission',async()=>{
  const {service,rows,auth}=fixture();auth.updateUser=async()=>{throw Error('network');};
  await assert.rejects(()=>service.changeAccess('admin','owner',{enabled:false,expectedVersion:1}));assert.equal(rows.owner.enabled,false);
});
test('restoring access preserves role and session cutoff',async()=>{
  const {service,rows}=fixture();await service.changeAccess('admin','device',{enabled:false,expectedVersion:1});
  await service.changeAccess('admin','device',{enabled:true,expectedVersion:2});
  assert.equal(rows.device.enabled,true);assert.equal(rows.device.role,'device');assert.equal(rows.device.revokedAt,1800000000);
});
test('stale concurrent changes conflict instead of silently replacing a newer decision',async()=>{
  const {service}=fixture();const results=await Promise.allSettled([1,2].map(()=>service.changeAccess('admin','owner',{enabled:false,expectedVersion:1})));
  assert.equal(results.filter(x=>x.status==='fulfilled').length,1);assert.equal(results.find(x=>x.status==='rejected').reason.status,409);
});
test('client cannot inject a role or arbitrary fields',async()=>{
  const {service}=fixture();for(const body of [{enabled:false,expectedVersion:1,role:'admin'},{enabled:'false',expectedVersion:1},{enabled:false,expectedVersion:0}])
    await assert.rejects(()=>service.changeAccess('admin','owner',body),{status:400});
});
test('unprovisioned account cannot be silently given access',async()=>{await assert.rejects(()=>fixture().service.changeAccess('admin','unknown',{enabled:true,expectedVersion:1}),{status:404});});
test('user listing omits privileged claims and password material',async()=>{
  const data=await fixture().service.listUsers('admin');assert.equal(data.users.length,1);assert.equal(data.users[0].access.role,'owner');
  assert.equal(JSON.stringify(data).includes('password'),false);assert.equal(JSON.stringify(data).includes('customClaims'),false);
});
test('backend fails closed without a configured protected administrator',()=>{assert.throws(()=>new AccessService({auth:{},store:{},protectedAdminUid:''}));});
test('administrator blocks and restores individual app features with audit',async()=>{
  const {service,rows,audit,calls}=fixture();
  await service.changeFeatures('admin','owner',{features:{publish:false,diagnostics:false},expectedVersion:1});
  assert.deepEqual(rows.owner.features,{publish:false,diagnostics:false});assert.equal(rows.owner.version,2);assert.equal(rows.owner.enabled,true);
  await service.changeFeatures('admin','owner',{features:{publish:true},expectedVersion:2});
  assert.deepEqual(rows.owner.features,{publish:true,diagnostics:false});assert.equal(rows.owner.role,'owner');
  assert.equal(audit.length,2);assert.equal(audit[0].stage,'features-applied');assert.deepEqual(calls,[]);
});
test('feature changes require the administrator and the current version',async()=>{
  const {service,rows}=fixture();
  await assert.rejects(()=>service.changeFeatures('owner','owner',{features:{publish:false},expectedVersion:1}),{status:403});
  await assert.rejects(()=>service.changeFeatures('admin','owner',{features:{publish:false},expectedVersion:5}),{status:409});
  assert.equal(rows.owner.features,undefined);
});
test('feature changes reject unknown features, non-booleans and extra fields',async()=>{
  const {service}=fixture();
  for(const body of [{features:{admin:true},expectedVersion:1},{features:{publish:'false'},expectedVersion:1},{features:{},expectedVersion:1},
    {features:[],expectedVersion:1},{features:{publish:false},expectedVersion:1,enabled:true},{features:{publish:false}}])
    await assert.rejects(()=>service.changeFeatures('admin','owner',body),{status:400});
});
test('features apply only to ordinary owner accounts',async()=>{
  const {service}=fixture();
  await assert.rejects(()=>service.changeFeatures('admin','device',{features:{publish:false},expectedVersion:1}),{status:409});
  for(const uid of ['primary','secondary']) await assert.rejects(()=>service.changeFeatures('admin',uid,{features:{publish:false},expectedVersion:1}),{status:409});
  await assert.rejects(()=>service.changeFeatures('admin','unknown',{features:{publish:false},expectedVersion:1}),{status:404});
});
