import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { execFileSync, spawnSync } from 'node:child_process';
import { before, beforeEach, after, test } from 'node:test';
import assert from 'node:assert/strict';
import { initializeTestEnvironment, assertFails, assertSucceeds } from '@firebase/rules-unit-testing';
import { get, set, update, ref, goOffline, goOnline } from 'firebase/database';

// Solo acepta el emulador local declarado por Firebase CLI. Nunca usa la base de producción.
assert.equal(process.env.FIREBASE_DATABASE_EMULATOR_HOST, '127.0.0.1:9009');
const projectId = 'demo-pastillero';
const base = 'devices/pastillero-01/v2';
const fixtures = JSON.parse(readFileSync('../reports/integration-v2-programs.json', 'utf8'));
assert.ok(Date.now() - fixtures.generatedAt < 120000, 'Regenerar fixtures con Java justo antes de probar');
const copy = value => JSON.parse(JSON.stringify(value));
const executable = resolve('../reports/contract-controller.exe');
const receipts = [];
let env;
const db = uid => env.authenticatedContext(uid, { auth_time: Math.floor(Date.now() / 1000) }).database();

before(async () => {
  env = await initializeTestEnvironment({ projectId, database: {
    host: '127.0.0.1', port: 9009, rules: readFileSync('database.rules.json', 'utf8'),
  } });
});
beforeEach(async () => {
  await env.clearDatabase();
  // Semilla exclusiva del emulador: programa que supuestamente se aceptó antes de perder red.
  // Una escritura nueva de estas fechas pasadas debe rechazarse y se comprueba por separado.
  await env.withSecurityRulesDisabled(async context => set(ref(context.database()), {
    access: { users: {
      owner: { role: 'owner', enabled: true, revokedAt: 0, version: 1 },
      device: { role: 'device', enabled: true, revokedAt: 0, version: 1 },
    } },
    devices: { 'pastillero-01': { ownerUid: 'owner', deviceUid: 'device',
      v2: { program: fixtures.cached } } },
  }));
});
after(async () => {
  await env?.cleanup();
  writeFileSync('../reports/integration-v2-receipts.json', JSON.stringify({
    projectId, hardwareUsed: false, productionUsed: false,
    nativeProducer: 'ScheduleEngine.program', cppConsumer: 'pill::Controller.tick',
    cachedProgramSeededWithRulesDisabled: true,
    limitations: ['No Android UI or WorkManager process in this integration',
      'No ESP32 Wi-Fi, TLS, NTP, NVS, GPIO or mechanical execution',
      'Past cached program is a local fixture; new stale programs are rejected'],
    receipts,
  }, null, 2) + '\n');
});
function model(program, scenario = 'confirmed', done = []) {
  const result = JSON.parse(execFileSync(executable, [], {
    input: JSON.stringify({ program, scenario, done, now: Date.now() }), encoding: 'utf8',
    timeout: 10000, maxBuffer: 100000,
  }));
  assert.equal(result.hardwareUsed, false);
  assert.equal(result.simulation, true);
  receipts.push({ scenario, doseCount: Object.keys(program.doses).length,
    reservedCount: result.done?.length ?? 0, moves: result.moves ?? [],
    eventTypes: Object.values(result.events ?? {}).map(event => event.type) });
  return result;
}
async function readProgram() {
  return (await get(ref(db('device'), base + '/program'))).val();
}
async function publishEvents(result) {
  const device = db('device');
  for (const [key, event] of Object.entries(result.events ?? {})) {
    assert.equal(event.simulation, true);
    await assertSucceeds(set(ref(device, base + '/events/' + key), event));
  }
  return (await get(ref(db('owner'), base + '/events'))).val() ?? {};
}
function checkReturns(result, expected = 4) {
  const moves = result.moves ?? [];
  assert.equal(moves.length, expected * 2);
  for (let i = 1; i < moves.length; i += 2) assert.equal(moves[i], 0);
  assert.deepEqual(moves.filter((_, index) => index % 2 === 0).sort((a,b) => a-b),
    [640, 1280, 1920, 2560]);
}
async function freshRoot() {
  await env.withSecurityRulesDisabled(async context => set(ref(context.database(), base + '/program'), null));
}

test('Java genera un programa futuro que las reglas aceptan solo del responsable', async () => {
  await freshRoot();
  await assertFails(set(ref(db('device'), base + '/program'), fixtures.future));
  await assertFails(set(ref(db('owner'), base + '/program'), fixtures.cached));
  await assertSucceeds(set(ref(db('owner'), base + '/program'), fixtures.future));
  assert.deepEqual(await readProgram(), fixtures.future);
  const result = model(await readProgram(), 'not_due');
  assert.equal(result.moves?.length ?? 0, 0);
});

test('programa Java cacheado → reglas → Controller → cuatro confirmaciones y Room-compatible JSON', async () => {
  const result = model(await readProgram());
  checkReturns(result);
  const events = await publishEvents(result);
  assert.equal(Object.values(events).filter(e => e.type === 'CONFIRMED').length, 4);
  assert.equal(Object.values(events).filter(e => e.type === 'STARTED').length, 4);
  for (const event of Object.values(events)) {
    assert.equal(event.compartment, fixtures.cached.regimens[event.medicationId].compartment);
  }
});

test('las omisiones se registran después del margen y no mueven el motor ficticio', async () => {
  const result = model(await readProgram(), 'missed');
  assert.equal(result.moves?.length ?? 0, 0);
  const events = await publishEvents(result);
  assert.equal(Object.values(events).length, 4);
  assert.ok(Object.values(events).every(e => e.type === 'MISSED'));
});

test('ausencia de blíster produce BLOCKED y ninguna confirmación', async () => {
  const result = model(await readProgram(), 'blocked');
  assert.equal(result.moves?.length ?? 0, 0);
  const events = await publishEvents(result);
  assert.equal(Object.values(events).length, 4);
  assert.ok(Object.values(events).every(e => e.type === 'BLOCKED'));
});

test('ausencia de salida produce NO_EXIT tras retornar al cero', async () => {
  const result = model(await readProgram(), 'no_exit');
  checkReturns(result);
  const events = await publishEvents(result);
  assert.equal(Object.values(events).filter(e => e.type === 'NO_EXIT').length, 4);
  assert.equal(Object.values(events).filter(e => e.type === 'CONFIRMED').length, 0);
});

test('repetir un programa y subir otra vez los mismos eventos conserva identidades', async () => {
  const program = await readProgram(), first = model(program);
  const before = await publishEvents(first);
  assert.deepEqual(await publishEvents(first), before);
  const replay = model(program, 'confirmed', first.done);
  assert.equal(replay.moves?.length ?? 0, 0);
  assert.equal(Object.keys(replay.events ?? {}).length, 0);
});

test('reiniciar el modelo con STARTED reservado impide repetir esa entrega', async () => {
  const program = await readProgram(), interrupted = model(program, 'interrupted');
  assert.equal(interrupted.moves.length, 1);
  assert.equal(interrupted.done.length, 1);
  await publishEvents(interrupted);
  const afterRestart = model(program, 'confirmed', interrupted.done);
  assert.equal(afterRestart.moves.length, 6);
  const events = await publishEvents(afterRestart);
  assert.equal(Object.values(events).filter(e => e.type === 'STARTED').length, 4);
  assert.equal(Object.values(events).filter(e => e.type === 'CONFIRMED').length, 3);
  // No se inventa RECOVERY: esa parte pertenece al adaptador NVS del firmware, aún sin ejecutar.
});

test('fallo al reservar la dosis bloquea antes del primer movimiento', async () => {
  const result = model(await readProgram(), 'reservation_failure');
  assert.equal(result.state, 7);
  assert.equal(result.moves?.length ?? 0, 0);
  assert.equal(result.done?.length ?? 0, 0);
});

test('reloj inválido o falta de calibración no habilitan entregas nuevas', async () => {
  const program = await readProgram();
  for (const scenario of ['invalid_clock', 'uncalibrated']) {
    const result = model(program, scenario);
    assert.equal(result.moves?.length ?? 0, 0);
    assert.equal(Object.keys(result.events ?? {}).length, 0);
  }
});

test('el ejecutable de QA rechaza modo físico antes de procesar dosis', async () => {
  const program = copy(await readProgram());
  program.targetMode = 'hardware';
  const result = spawnSync(executable, [], { input: JSON.stringify({ program }), encoding: 'utf8' });
  assert.equal(result.status, 2);
  assert.match(result.stderr, /Only simulation protocol V2/);
});

test('una edición offline obsoleta no reemplaza al ganador remoto', async () => {
  const first = db('owner'), second = db('owner');
  const local = copy(fixtures.cached), remote = copy(fixtures.cached);
  local.revision = remote.revision = 2;
  local.token = 'edicion-local'; remote.token = 'edicion-remota';
  goOffline(first);
  const pending = set(ref(first, base + '/program'), local).then(() => true, () => false);
  try {
    await assertSucceeds(set(ref(second, base + '/program'), remote));
  } finally { goOnline(first); }
  assert.equal(await pending, false);
  assert.equal((await readProgram()).token, 'edicion-remota');
});

test('revocar al dispositivo impide acceso con su sesión anterior y conserva al responsable', async () => {
  const device = db('device');
  await assertSucceeds(get(ref(device, base + '/program')));
  await env.withSecurityRulesDisabled(async context => update(ref(context.database(), 'access/users/device'), { enabled: false }));
  await assertFails(get(ref(device, base + '/program')));
  await assertSucceeds(get(ref(db('owner'), base + '/program')));
});
