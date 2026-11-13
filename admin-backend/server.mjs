import {createServer} from 'node:http';
import {readFileSync} from 'node:fs';
import {initializeApp,applicationDefault} from 'firebase-admin/app';
import {getAuth} from 'firebase-admin/auth';
import {getDatabase} from 'firebase-admin/database';
import {AccessService,ApiError} from './access-service.mjs';

const config=JSON.parse(readFileSync(new URL('../private/dashboard-admin.local.json',import.meta.url),'utf8'));
if(config.projectId!=='pastillerobadi' || config.databaseUrl!=='https://pastillerobadi-default-rtdb.firebaseio.com')
  throw new Error('Dedicated Firebase project required');
if(!config.protectedAdminUid) throw new Error('Configure the dedicated primary dashboard administrator before starting');
// ADC must come from the host identity. Do not distribute a service-account JSON key.
initializeApp({credential:applicationDefault(),projectId:config.projectId,databaseURL:config.databaseUrl});
const database=getDatabase();
const store={
  async readAccess(uid) {return (await database.ref('access/users/'+uid).get()).val();},
  async readDevices() {return (await database.ref('devices').get()).val()??{};},
  async changeAccess(uid,expectedVersion,transform) {
    const result=await database.ref('access/users/'+uid).transaction(old=>{
      if(!old || old.version!==expectedVersion || !['owner','device'].includes(old.role)) return;
      return transform(old);
    },undefined,false);
    return result.committed?result.snapshot.val():null;
  },
  async audit(event) {await database.ref('administration/audit').push(event);}
};
const service=new AccessService({auth:getAuth(),store,protectedAdminUid:config.protectedAdminUid});
async function bodyJson(request) {
  let body='';
  for await(const chunk of request) {
    body+=chunk;
    if(Buffer.byteLength(body)>2048) throw new ApiError(413,'BODY_TOO_LARGE');
  }
  try {return JSON.parse(body);} catch {throw new ApiError(400,'INVALID_JSON');}
}
const server=createServer(async(request,response)=>{
  response.setHeader('Cache-Control','no-store');
  response.setHeader('X-Content-Type-Options','nosniff');
  response.setHeader('Content-Type','application/json; charset=utf-8');
  try {
    // Future web frontend is served on the same origin. No permissive CORS/cookies.
    if(request.headers.origin && request.headers.origin!==config.origin) throw new ApiError(403,'ORIGIN_DENIED');
    const header=request.headers.authorization??'';
    if(!header.startsWith('Bearer ') || header.length>8192) throw new ApiError(401,'BEARER_REQUIRED');
    const token=header.slice(7), url=new URL(request.url,'http://localhost');
    let result;
    if(request.method==='GET' && url.pathname==='/api/users') result=await service.listUsers(token,url.searchParams.get('pageToken')??undefined);
    else if(request.method==='GET' && url.pathname==='/api/devices') result=await service.overview(token);
    else if(request.method==='PATCH' && /^\/api\/users\/[A-Za-z0-9_-]{1,128}\/access$/.test(url.pathname)) {
      // Authenticate before accepting/parsing a mutation payload.
      await service.authorize(token);
      result=await service.changeAccess(token,url.pathname.split('/')[3],await bodyJson(request));
    } else throw new ApiError(404,'NOT_FOUND');
    response.end(JSON.stringify(result));
  } catch(error) {
    response.statusCode=error instanceof ApiError?error.status:503;
    response.end(JSON.stringify({error:error instanceof ApiError?error.message:'SERVICE_UNAVAILABLE'}));
  }
});
server.requestTimeout=15000;server.headersTimeout=10000;
server.listen(8787,'127.0.0.1',()=>console.log('Administration API listening on loopback; no hardware commands'));
