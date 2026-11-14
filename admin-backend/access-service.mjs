// Privileged operations run only on the trusted backend, never in a browser bundle.
export class ApiError extends Error {
  constructor(status, code) { super(code); this.status=status; }
}
// App functionality an administrator can block per owner account. Absent keys stay allowed.
export const FEATURES=['medications','publish','deviceSettings','diagnostics'];
export class AccessService {
  constructor({auth,store,protectedAdminUid,now=Date.now}) {
    if(!protectedAdminUid) throw new Error('Protected administrator UID is required');
    Object.assign(this,{auth,store,protectedAdminUid,now});
  }
  async authorize(token) {
    let identity;
    try { identity=await this.auth.verifyIdToken(token,true); }
    catch { throw new ApiError(401,'INVALID_OR_REVOKED_SESSION'); }
    if(identity.uid!==this.protectedAdminUid || identity.dashboardAdmin!==true)
      throw new ApiError(403,'DASHBOARD_ADMIN_REQUIRED');
    return identity.uid;
  }
  async listUsers(token,pageToken) {
    await this.authorize(token);
    const page=await this.auth.listUsers(100,pageToken);
    const users=await Promise.all(page.users.map(async user=>({
      uid:user.uid,email:user.email??null,disabled:user.disabled,
      protected:user.uid===this.protectedAdminUid,access:await this.store.readAccess(user.uid)
    })));
    return {users,nextPageToken:page.pageToken??null};
  }
  async overview(token) {
    await this.authorize(token);
    return this.store.readDevices();
  }
  async changeAccess(token,uid,body) {
    const actor=await this.authorize(token);
    if(!/^[A-Za-z0-9_-]{1,128}$/.test(uid)) throw new ApiError(400,'INVALID_UID');
    if(uid===this.protectedAdminUid) throw new ApiError(409,'PRIMARY_ADMIN_PROTECTED');
    if(!body || Object.keys(body).sort().join(',')!=='enabled,expectedVersion' ||
      typeof body.enabled!=='boolean' || !Number.isSafeInteger(body.expectedVersion) || body.expectedVersion<1)
      throw new ApiError(400,'INVALID_ACCESS_CHANGE');
    const target=await this.auth.getUser(uid);
    // Administrative identities cannot accidentally enter the ordinary-account workflow.
    if(target.customClaims?.dashboardAdmin===true) throw new ApiError(409,'ADMIN_ACCOUNT_PROTECTED');
    const current=await this.store.readAccess(uid);
    if(!current || !['owner','device'].includes(current.role)) throw new ApiError(404,'ACCOUNT_NOT_PROVISIONED');
    const now=this.now();
    if(body.enabled) {
      // Database permission stays denied if enabling Authentication fails.
      await this.auth.updateUser(uid,{disabled:false});
    }
    const record=await this.store.changeAccess(uid,body.expectedVersion,old=>({
      ...old,enabled:body.enabled,version:old.version+1,updatedAt:now,updatedBy:actor,
      revokedAt:body.enabled?old.revokedAt:Math.max(old.revokedAt,Math.floor(now/1000))
    }));
    if(!record) throw new ApiError(409,'VERSION_CONFLICT');
    // Fail closed: record is denied before invalidating sessions. A later failure never reopens it.
    await this.store.audit({actor,target:uid,enabled:body.enabled,version:record.version,at:now,stage:'database-applied'});
    if(!body.enabled) {
      await this.auth.updateUser(uid,{disabled:true});
      await this.auth.revokeRefreshTokens(uid);
    }
    await this.store.audit({actor,target:uid,enabled:body.enabled,version:record.version,at:this.now(),stage:'completed'});
    return record;
  }
  async changeFeatures(token,uid,body) {
    const actor=await this.authorize(token);
    if(!/^[A-Za-z0-9_-]{1,128}$/.test(uid)) throw new ApiError(400,'INVALID_UID');
    if(uid===this.protectedAdminUid) throw new ApiError(409,'PRIMARY_ADMIN_PROTECTED');
    const features=body?.features;
    if(!body || Object.keys(body).sort().join(',')!=='expectedVersion,features' ||
      !Number.isSafeInteger(body.expectedVersion) || body.expectedVersion<1 ||
      !features || typeof features!=='object' || Array.isArray(features) || !Object.keys(features).length ||
      Object.entries(features).some(([name,value])=>!FEATURES.includes(name) || typeof value!=='boolean'))
      throw new ApiError(400,'INVALID_FEATURE_CHANGE');
    const target=await this.auth.getUser(uid);
    if(target.customClaims?.dashboardAdmin===true) throw new ApiError(409,'ADMIN_ACCOUNT_PROTECTED');
    const current=await this.store.readAccess(uid);
    if(!current || !['owner','device'].includes(current.role)) throw new ApiError(404,'ACCOUNT_NOT_PROVISIONED');
    // Only the Android owner uses the app; the ESP32 account has no app features to block.
    if(current.role!=='owner') throw new ApiError(409,'FEATURES_ONLY_FOR_OWNER');
    const now=this.now();
    const record=await this.store.changeAccess(uid,body.expectedVersion,old=>old.role!=='owner'?undefined:({
      ...old,features:{...old.features,...features},version:old.version+1,updatedAt:now,updatedBy:actor
    }));
    if(!record) throw new ApiError(409,'VERSION_CONFLICT');
    await this.store.audit({actor,target:uid,features,version:record.version,at:now,stage:'features-applied'});
    return record;
  }
}
