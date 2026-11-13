// Deliberate administrative provisioning. Do not run until a dedicated account is selected.
import {readFileSync} from 'node:fs';
import {initializeApp,applicationDefault} from 'firebase-admin/app';
import {getAuth} from 'firebase-admin/auth';
import {getDatabase} from 'firebase-admin/database';
const config=JSON.parse(readFileSync(new URL('../private/dashboard-admin.local.json',import.meta.url),'utf8'));
if(config.projectId!=='pastillerobadi' || config.databaseUrl!=='https://pastillerobadi-default-rtdb.firebaseio.com' ||
  !/^[A-Za-z0-9_-]{1,128}$/.test(config.protectedAdminUid??'')) throw Error('Configure the dedicated project and primary administrator UID');
initializeApp({credential:applicationDefault(),projectId:config.projectId,databaseURL:config.databaseUrl});
const auth=getAuth(), database=getDatabase(), uid=config.protectedAdminUid;
const user=await auth.getUser(uid);
if(user.disabled) throw Error('Primary administrative account must be active');
const devices=(await database.ref('devices').get()).val()??{};
if(Object.values(devices).some(device=>[device.ownerUid,device.deviceUid].includes(uid)))
  throw Error('Use a dedicated administrative account, separate from Android and ESP32');
const lock=await database.ref('administration/protectedAdminUid').transaction(old=>
  old===null || old===uid?uid:undefined,undefined,false);
if(!lock.committed) throw Error('A different protected administrator is already configured');
await auth.setCustomUserClaims(uid,{...user.customClaims,dashboardAdmin:true});
console.log('Primary dashboard administrator provisioned; sign in again to refresh the claim. No credentials printed.');
