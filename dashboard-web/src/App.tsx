import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import { ApiError, type AdminApi, type SimKind } from "./api";
import { OFFLINE_MS, type Alert, type Severity } from "./alerts";
import {
  FEATURES,
  errorNames,
  eventNames,
  phaseName,
  relative,
} from "./labels";
import { loadMuted, saveMuted, sounds } from "./sound";
import type {
  AccessRecord,
  AdminUser,
  Device,
  Devices,
  Feature,
} from "./types";
import { useAlerts } from "./useAlerts";

type Tab = "users" | "devices" | "alerts";
const roleNames = { owner: "Responsable (app)", device: "Pastillero (ESP32)" };
const message = (e: unknown) =>
  e instanceof ApiError
    ? (errorNames[e.code] ?? `Error ${e.status}: ${e.code}`)
    : "No se pudo completar la operación.";

export function App({ api }: { api: AdminApi }) {
  const [session, setSession] = useState<boolean>();
  useEffect(() => api.onSession(setSession), [api]);
  if (session === undefined)
    return <main className="center muted">Cargando…</main>;
  return session ? <Dashboard api={api} /> : <Login api={api} />;
}

function Login({ api }: { api: AdminApi }) {
  const [email, setEmail] = useState(""),
    [password, setPassword] = useState(""),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    // El clic de inicio de sesión habilita el audio para las alarmas posteriores.
    sounds.unlock();
    setBusy(true);
    setError("");
    try {
      await api.signIn(email, password);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? message(err)
          : "Correo o contraseña incorrectos.",
      );
    } finally {
      setBusy(false);
    }
  };
  return (
    <main className="center">
      <form className="card login" onSubmit={submit}>
        <span className="brand-mark" aria-hidden="true">
          💊
        </span>
        <h1>Badi · Administración</h1>
        <p className="muted">
          Panel para el administrador. Los responsables usan la app Android.
        </p>
        {api.demo ? (
          <p className="notice">
            Modo demostración: datos ficticios, sin Firebase ni dispositivo.
          </p>
        ) : (
          <>
            <label>
              Correo
              <input
                type="email"
                required
                autoComplete="username"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </label>
            <label>
              Contraseña
              <input
                type="password"
                required
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </label>
          </>
        )}
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <button className="primary" disabled={busy}>
          {busy
            ? "Entrando…"
            : api.demo
              ? "Entrar a la demostración"
              : "Entrar"}
        </button>
      </form>
    </main>
  );
}

const POLL_MS = 5000;
const severityNames: Record<Severity, string> = {
  critical: "Crítica",
  warning: "Advertencia",
  info: "Aviso",
  success: "Confirmación",
};
const severityIcons: Record<Severity, string> = {
  critical: "⛔",
  warning: "⚠️",
  info: "ℹ️",
  success: "✅",
};
const time = (ms: number) =>
  new Date(ms).toLocaleTimeString("es-MX", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });

function Dashboard({ api }: { api: AdminApi }) {
  const [tab, setTab] = useState<Tab>("users"),
    [users, setUsers] = useState<AdminUser[]>(),
    [devices, setDevices] = useState<Devices>({}),
    [loadError, setLoadError] = useState(""),
    [lastUpdate, setLastUpdate] = useState<number>(),
    [online, setOnline] = useState(true),
    [now, setNow] = useState(Date.now()),
    [muted, setMuted] = useState(loadMuted);
  const alerts = useAlerts(muted);
  const { ingest } = alerts;
  const latest = useRef<Devices>({});
  // Lectura en vivo: consulta el backend cada cinco segundos y evalúa sensores y eventos nuevos.
  const load = useCallback(async () => {
    try {
      const [u, d] = await Promise.all([api.listUsers(), api.devices()]);
      latest.current = d;
      setUsers(u);
      setDevices(d);
      setLastUpdate(Date.now());
      setOnline(true);
      setLoadError("");
      ingest(d, Date.now());
    } catch (e) {
      if (e instanceof ApiError && e.status === 401)
        return void (await api.signOut());
      setOnline(false);
      setLoadError(message(e));
      ingest(latest.current, Date.now(), [
        {
          id: "system:backend",
          severity: "critical",
          title: "Sin conexión con el backend",
          detail: message(e),
          at: Date.now(),
          source: "system",
        },
      ]);
    }
  }, [api, ingest]);
  useEffect(() => {
    void load();
    const poll = setInterval(() => void load(), POLL_MS),
      tick = setInterval(() => setNow(Date.now()), 1000);
    return () => {
      clearInterval(poll);
      clearInterval(tick);
    };
  }, [load]);
  // Aplica un cambio del backend y confirma en pantalla y con sonido; ante conflicto recarga.
  const apply = async (
    uid: string,
    change: () => Promise<AccessRecord>,
    done: string,
  ) => {
    try {
      const access = await change();
      setUsers((list) =>
        list?.map((u) =>
          u.uid === uid ? { ...u, access, disabled: !access.enabled } : u,
        ),
      );
      alerts.command("success", "Comando confirmado", done);
    } catch (e) {
      alerts.command("warning", "Comando rechazado", message(e));
      if (e instanceof ApiError && e.code === "VERSION_CONFLICT") await load();
    }
  };
  const toggleSound = () => {
    sounds.unlock();
    setMuted((m) => {
      saveMuted(!m);
      if (m) sounds.success();
      return !m;
    });
  };
  const emailOf = (uid?: string) =>
    users?.find((u) => u.uid === uid)?.email ?? uid ?? "—";
  const top = alerts.pending[0];
  const tabs: [Tab, string][] = [
    ["users", "Usuarios y permisos"],
    ["devices", "Dispositivos"],
    ["alerts", "Alertas"],
  ];
  return (
    <div className={`shell ${alerts.alarming ? "alarming" : ""}`}>
      <div className="sticky">
        <header className="topbar">
          <div className="brand">
            <span className="brand-mark" aria-hidden="true">
              💊
            </span>
            <strong>Badi · Administración</strong>
            {api.demo && <span className="chip warn">Demostración</span>}
          </div>
          <nav className="tabs" aria-label="Secciones">
            {tabs.map(([t, label]) => (
              <button
                key={t}
                className={tab === t ? "tab active" : "tab"}
                aria-pressed={tab === t}
                onClick={() => setTab(t)}
              >
                {label}
                {t === "alerts" && alerts.pending.length > 0 && (
                  <span
                    className={`count ${alerts.alarming ? "critical" : "warning"}`}
                    aria-label={`${alerts.pending.length} sin reconocer`}
                  >
                    {alerts.pending.length}
                  </span>
                )}
              </button>
            ))}
          </nav>
          <div className="row">
            <span
              className={`live ${online ? "on" : "off"}`}
              title="Actualización automática cada 5 s"
            >
              <span className="live-dot" aria-hidden="true" />
              {online
                ? `En vivo · ${lastUpdate ? relative(lastUpdate, now) : "conectando"}`
                : "Sin conexión"}
            </span>
            <button
              className="ghost icon"
              aria-pressed={!muted}
              aria-label={
                muted ? "Activar sonido de alarmas" : "Silenciar alarmas"
              }
              title={muted ? "Sonido desactivado" : "Sonido activado"}
              onClick={toggleSound}
            >
              {muted ? "🔇" : "🔊"}
            </button>
            <span className="muted small">{api.email()}</span>
            <button className="ghost" onClick={() => void load()}>
              Actualizar
            </button>
            <button className="ghost" onClick={() => void api.signOut()}>
              Cerrar sesión
            </button>
          </div>
        </header>
        {top && (
          <div className={`alarm-banner ${top.severity}`} role="alert">
            <span className="alarm-icon" aria-hidden="true">
              {severityIcons[top.severity]}
            </span>
            <div className="alarm-text">
              <strong>{top.title}</strong>
              <span>
                {top.deviceId ? `${top.deviceId} · ` : ""}
                {top.detail}
              </span>
            </div>
            {alerts.pending.length > 1 && (
              <span className="chip">+{alerts.pending.length - 1} más</span>
            )}
            <button onClick={() => alerts.ack(top.id)}>Reconocer</button>
            {tab !== "alerts" && (
              <button className="ghost" onClick={() => setTab("alerts")}>
                Ver alertas
              </button>
            )}
          </div>
        )}
      </div>
      <main className="content">
        {!users ? (
          <p className={loadError ? "error" : "muted"}>
            {loadError || "Cargando datos del backend…"}
          </p>
        ) : tab === "users" ? (
          <UsersView users={users} apply={apply} api={api} />
        ) : tab === "devices" ? (
          <DevicesView
            devices={devices}
            emailOf={emailOf}
            active={alerts.active}
            acked={alerts.acked}
            now={now}
            api={api}
          />
        ) : (
          <AlertsView alerts={alerts} now={now} />
        )}
      </main>
      <div className="toasts" aria-live="polite">
        {alerts.toasts.map((t) => (
          <div key={t.id} className={`toast ${t.severity}`} role="status">
            <span aria-hidden="true">{severityIcons[t.severity]}</span>
            <div>
              <strong>{t.title}</strong>
              <small>{t.detail}</small>
            </div>
            <button
              className="link"
              aria-label="Cerrar aviso"
              onClick={() => alerts.dismissToast(t.id)}
            >
              ✕
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}

function AlertsView({
  alerts,
  now,
}: {
  alerts: ReturnType<typeof useAlerts>;
  now: number;
}) {
  return (
    <div className="alerts-grid">
      <section className="card">
        <header className="user-head">
          <h2>Alertas activas</h2>
          <button disabled={!alerts.pending.length} onClick={alerts.ackAll}>
            Reconocer todas
          </button>
        </header>
        {alerts.active.length ? (
          <ul className="alert-list">
            {alerts.active.map((a) => {
              const done = alerts.acked.has(a.id);
              return (
                <li
                  key={a.id}
                  className={`alert-item ${a.severity} ${done ? "acked" : ""}`}
                >
                  <span className={`sev ${a.severity}`}>
                    {severityNames[a.severity]}
                  </span>
                  <div>
                    <strong>{a.title}</strong>
                    <small className="muted">
                      {a.deviceId ? `${a.deviceId} · ` : ""}desde{" "}
                      {relative(a.at, now)} · {a.detail}
                    </small>
                  </div>
                  {a.severity === "critical" || a.severity === "warning" ? (
                    done ? (
                      <span className="muted small">Reconocida</span>
                    ) : (
                      <button onClick={() => alerts.ack(a.id)}>
                        Reconocer
                      </button>
                    )
                  ) : (
                    <span />
                  )}
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="all-clear">
            ✅ Todo en orden: ningún sensor reporta problemas.
          </p>
        )}
      </section>
      <section className="card">
        <h2>Historial de notificaciones</h2>
        {alerts.log.length ? (
          <ul className="list log">
            {alerts.log.map((a) => (
              <li key={a.id}>
                <span
                  className={`sev-dot ${a.severity}`}
                  aria-label={severityNames[a.severity]}
                />
                <span>
                  <strong>{a.title}</strong>{" "}
                  <span className="muted small">{a.detail}</span>
                </span>
                <span className="muted small">{time(a.at)}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted small">Sin notificaciones en esta sesión.</p>
        )}
      </section>
    </div>
  );
}

function UsersView({
  users,
  api,
  apply,
}: {
  users: AdminUser[];
  api: AdminApi;
  apply: (
    uid: string,
    change: () => Promise<AccessRecord>,
    done: string,
  ) => Promise<void>;
}) {
  const [busy, setBusy] = useState<string>(),
    [confirming, setConfirming] = useState<AdminUser>();
  const run = async (
    uid: string,
    change: () => Promise<AccessRecord>,
    done: string,
  ) => {
    setBusy(uid);
    await apply(uid, change, done);
    setBusy(undefined);
  };
  const owners = users.filter((u) => u.access?.role === "owner");
  const blocked = owners.reduce(
    (n, u) =>
      n + FEATURES.filter((f) => u.access?.features?.[f.id] === false).length,
    0,
  );
  return (
    <>
      <section className="stats">
        <Stat label="Cuentas" value={users.length} />
        <Stat label="Responsables" value={owners.length} />
        <Stat
          label="Bloqueadas"
          value={users.filter((u) => u.access && !u.access.enabled).length}
        />
        <Stat label="Funciones restringidas" value={blocked} />
      </section>
      <p className="muted small">
        Los cambios se aplican en la app del responsable en cuanto recibe la
        actualización de Firebase. Una función sin restricción está permitida.
      </p>
      <div className="users">
        {users.map((u) => {
          const a = u.access;
          return (
            <article
              key={u.uid}
              className={`card user ${a && !a.enabled ? "off" : ""}`}
            >
              <header className="user-head">
                <div>
                  <h2>{u.email ?? "Sin correo"}</h2>
                  <code className="muted small">{u.uid}</code>
                </div>
                <div className="row">
                  {u.protected ? (
                    <span className="chip">Administrador principal</span>
                  ) : a ? (
                    <>
                      <span className="chip">{roleNames[a.role]}</span>
                      <span className={`chip ${a.enabled ? "ok" : "bad"}`}>
                        {a.enabled ? "Activa" : "Bloqueada"}
                      </span>
                    </>
                  ) : (
                    <span className="chip">Sin registro de acceso</span>
                  )}
                </div>
              </header>
              {a && !u.protected && (
                <>
                  {a.role === "owner" ? (
                    <div
                      className="features"
                      aria-label={`Funciones de ${u.email ?? u.uid}`}
                    >
                      {FEATURES.map((f) => {
                        const on = a.features?.[f.id] !== false;
                        return (
                          <label
                            key={f.id}
                            className={`feature ${on ? "" : "blocked"}`}
                          >
                            <span>
                              <strong>{f.name}</strong>
                              <small className="muted">{f.detail}</small>
                            </span>
                            <span className="switch">
                              <input
                                type="checkbox"
                                role="switch"
                                aria-label={`${f.name} para ${u.email ?? u.uid}`}
                                checked={on}
                                disabled={busy === u.uid || !a.enabled}
                                onChange={(e) =>
                                  void run(
                                    u.uid,
                                    () =>
                                      api.setFeatures(
                                        u.uid,
                                        { [f.id]: e.target.checked } as Partial<
                                          Record<Feature, boolean>
                                        >,
                                        a.version,
                                      ),
                                    `${f.name}: ${e.target.checked ? "permitido" : "bloqueado"}`,
                                  )
                                }
                              />
                              <span aria-hidden="true" />
                            </span>
                          </label>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="muted small">
                      La cuenta del ESP32 no usa la app; solo se puede bloquear
                      o habilitar.
                    </p>
                  )}
                  <footer className="user-foot">
                    <span className="muted small">
                      Versión {a.version} · último cambio{" "}
                      {relative(a.updatedAt)}
                    </span>
                    {a.enabled ? (
                      <button
                        className="danger"
                        disabled={busy === u.uid}
                        onClick={() => setConfirming(u)}
                      >
                        Bloquear cuenta
                      </button>
                    ) : (
                      <button
                        disabled={busy === u.uid}
                        onClick={() =>
                          void run(
                            u.uid,
                            () => api.setAccess(u.uid, true, a.version),
                            "Cuenta habilitada",
                          )
                        }
                      >
                        Habilitar cuenta
                      </button>
                    )}
                  </footer>
                </>
              )}
            </article>
          );
        })}
      </div>
      {confirming?.access && (
        <div
          className="overlay"
          role="dialog"
          aria-modal="true"
          aria-labelledby="confirm-title"
        >
          <div className="card modal">
            <h2 id="confirm-title">
              ¿Bloquear {confirming.email ?? confirming.uid}?
            </h2>
            <p>
              Se cierra su acceso a Firebase y se revocan sus sesiones. La app
              conserva su historial local y el pastillero mantiene el plan ya
              guardado. Para recuperar el acceso, la persona deberá iniciar
              sesión de nuevo.
            </p>
            <div className="row end">
              <button
                className="ghost"
                onClick={() => setConfirming(undefined)}
              >
                Cancelar
              </button>
              <button
                className="danger"
                onClick={() => {
                  const u = confirming;
                  setConfirming(undefined);
                  void run(
                    u.uid,
                    () => api.setAccess(u.uid, false, u.access!.version),
                    "Cuenta bloqueada",
                  );
                }}
              >
                Bloquear
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="card stat">
      <strong>{value}</strong>
      <span className="muted small">{label}</span>
    </div>
  );
}

const simulations: [SimKind, string][] = [
  ["deliver", "Entrega completa"],
  ["missed", "Dosis omitida"],
  ["blister", "Sin blíster"],
  ["failure", "Fallo del motor"],
  ["offline", "Desconexión"],
  ["restore", "Restablecer"],
];

function DevicesView({
  devices,
  emailOf,
  active,
  acked,
  now,
  api,
}: {
  devices: Devices;
  emailOf: (uid?: string) => string;
  active: Alert[];
  acked: ReadonlySet<string>;
  now: number;
  api: AdminApi;
}) {
  const entries = Object.entries(devices);
  return (
    <>
      {api.simulate && (
        <section className="card simulator">
          <div>
            <h2>Simulador de la demostración</h2>
            <p className="muted small">
              Provoca cambios en los sensores del pastillero ficticio para ver
              alertas y alarmas.
            </p>
          </div>
          <div className="row">
            {simulations.map(([kind, label]) => (
              <button
                key={kind}
                className={kind === "restore" ? "primary" : ""}
                onClick={() => api.simulate!(kind)}
              >
                {label}
              </button>
            ))}
          </div>
        </section>
      )}
      {!entries.length ? (
        <p className="muted">No hay dispositivos registrados.</p>
      ) : (
        <div className="devices">
          {entries.map(([id, d]) => (
            <DeviceCard
              key={id}
              id={id}
              device={d}
              emailOf={emailOf}
              alerts={active.filter((a) => a.deviceId === id)}
              acked={acked}
              now={now}
            />
          ))}
        </div>
      )}
    </>
  );
}

type Tone = "ok" | "warn" | "bad" | "busy" | "neutral";
function DeviceCard({
  id,
  device,
  emailOf,
  alerts,
  acked,
  now,
}: {
  id: string;
  device: Device;
  emailOf: (uid?: string) => string;
  alerts: Alert[];
  acked: ReadonlySet<string>;
  now: number;
}) {
  const program = device.v2?.program,
    state = device.v2?.state ?? {},
    regimens = Object.values(program?.regimens ?? {}),
    events = Object.values(device.v2?.events ?? {}).sort(
      (a, b) => b.actualAt - a.actualAt,
    ),
    recent = events.slice(0, 8);
  const positions = program?.positions ?? state.positions ?? 5;
  const fresh = !!state.updatedAt && now - state.updatedAt < OFFLINE_MS;
  const phase = state.phase;
  // Compartimento en curso: el de la última entrega iniciada mientras el ciclo no termina.
  const current =
    phase !== undefined && phase >= 1 && phase <= 4
      ? events.find((e) => e.type === "STARTED")?.compartment
      : undefined;
  const critical = alerts.some((a) => a.severity === "critical");
  const unacked = alerts.some(
    (a) => a.severity === "critical" && !acked.has(a.id),
  );
  const behind =
    !!program?.revision && (state.appliedRevision ?? 0) < program.revision;
  const sensors: [string, string, Tone][] = [
    [
      "Conexión",
      fresh ? "En línea" : `Sin señal ${relative(state.updatedAt, now)}`,
      fresh ? "ok" : "bad",
    ],
    [
      "Fase",
      phaseName(phase),
      phase === 7 || phase === 5
        ? "bad"
        : phase === 6
          ? "warn"
          : phase && phase >= 1
            ? "busy"
            : "ok",
    ],
    [
      "Calibración",
      state.calibrated ? "Calibrado" : "Sin calibrar",
      state.calibrated ? "ok" : "warn",
    ],
    [
      "Blíster",
      state.blisterPresent === false ? "Ausente" : "Presente",
      state.blisterPresent === false ? "warn" : "ok",
    ],
    [
      "Almacenamiento",
      state.storageHealthy === false ? "Con fallas" : "Correcto",
      state.storageHealthy === false ? "bad" : "ok",
    ],
    [
      "Sensor de salida",
      state.exitDetected ? "Pastilla detectada" : "Sin detección",
      state.exitDetected ? "busy" : "neutral",
    ],
    [
      "Servo",
      state.servoOpen ? "Abierto" : "Cerrado",
      state.servoOpen ? "busy" : "neutral",
    ],
    [
      "Bomba",
      state.pumpActive ? "Activa" : "Inactiva",
      state.pumpActive ? "busy" : "neutral",
    ],
    [
      "Revisión",
      `${state.appliedRevision ?? "—"} / ${program?.revision ?? "—"}`,
      behind ? "warn" : "ok",
    ],
  ];
  return (
    <article
      className={`card device ${critical ? "critical" : ""} ${unacked ? "flashing" : ""}`}
    >
      <header className="user-head">
        <div>
          <h2>{id}</h2>
          <span className="muted small">
            Responsable: {emailOf(device.ownerUid)} · ESP32:{" "}
            {emailOf(device.deviceUid)} ·{" "}
            {state.simulation ? "Simulación" : "Hardware"}
          </span>
        </div>
        <span
          className={`chip ${critical ? "bad" : alerts.length ? "warn" : "ok"}`}
        >
          {critical
            ? "Atención requerida"
            : alerts.length
              ? `${alerts.length} aviso(s)`
              : "Sin alertas"}
        </span>
      </header>
      <div className="device-body">
        <Carousel positions={positions} regimens={regimens} current={current} />
        <div className="sensors" aria-label={`Sensores de ${id}`}>
          {sensors.map(([label, value, tone]) => (
            <div key={label} className={`sensor ${tone}`}>
              <small>{label}</small>
              <strong>{value}</strong>
            </div>
          ))}
        </div>
      </div>
      <h3>Pautas</h3>
      {regimens.length ? (
        <ul className="list">
          {regimens
            .sort((a, b) => a.compartment - b.compartment)
            .map((r) => (
              <li key={r.id} className={r.enabled ? "" : "off"}>
                <span className={`slot-dot c${r.compartment}`}>
                  C{r.compartment}
                </span>
                <strong>{r.name}</strong>
                <span className="muted small">
                  {r.mode === "daily"
                    ? (r.times ?? []).join(", ")
                    : `cada ${(r.intervalMinutes ?? 0) / 60} h`}
                  {r.enabled ? "" : " · inactiva"}
                </span>
              </li>
            ))}
        </ul>
      ) : (
        <p className="muted small">Sin plan publicado.</p>
      )}
      <h3>Eventos recientes</h3>
      {recent.length ? (
        <ul className="list">
          {recent.map((e) => (
            <li
              key={e.doseId + e.type}
              className={`event ${eventTone[e.type] ?? ""}`}
            >
              <span className={`slot-dot c${e.compartment}`}>
                C{e.compartment}
              </span>
              <strong>{eventNames[e.type] ?? e.type}</strong>
              <span className="muted small">
                {new Date(e.actualAt).toLocaleString("es-MX", {
                  dateStyle: "short",
                  timeStyle: "short",
                })}
                {e.simulation ? " · simulado" : ""}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted small">Sin eventos.</p>
      )}
    </article>
  );
}
const eventTone: Record<string, string> = {
  MISSED: "bad",
  BLOCKED: "bad",
  RECOVERY: "bad",
  NO_EXIT: "warn",
  CONFIRMED: "ok",
};

/** Cinco posiciones: 0 es el retorno vacío y 1..4 son compartimentos útiles. */
function Carousel({
  positions,
  regimens,
  current,
}: {
  positions: number;
  regimens: { compartment: number; name: string; enabled: boolean }[];
  current?: number;
}) {
  return (
    <svg
      viewBox="0 0 220 220"
      className="carousel"
      role="img"
      aria-label={`${positions} posiciones; cero reservado al retorno`}
    >
      <circle cx="110" cy="110" r="96" className="orbit" />
      {Array.from({ length: positions }, (_, i) => {
        const a = (i / positions) * 2 * Math.PI - Math.PI / 2,
          x = 110 + 70 * Math.cos(a),
          y = 110 + 70 * Math.sin(a);
        const names = regimens
          .filter((r) => r.compartment === i && r.enabled)
          .map((r) => r.name);
        return (
          <g key={i}>
            <title>
              {i === 0
                ? "Posición 0: retorno, sin dosis"
                : `Compartimento ${i}: ${names.join(", ") || "libre"}`}
            </title>
            {i === current && (
              <circle cx={x} cy={y} r="31" className="slot-ring" />
            )}
            <circle
              cx={x}
              cy={y}
              r="25"
              className={
                i === 0
                  ? "slot zero"
                  : names.length
                    ? `slot used c${i}`
                    : "slot"
              }
            />
            <text x={x} y={y + 5} textAnchor="middle" className="slot-label">
              {i === 0 ? "0" : `C${i}`}
            </text>
          </g>
        );
      })}
      <circle cx="110" cy="110" r="24" className="hub" />
      {current !== undefined && (
        <text x="110" y="114" textAnchor="middle" className="hub-label">
          C{current}
        </text>
      )}
    </svg>
  );
}
