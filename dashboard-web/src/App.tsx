import { useCallback, useEffect, useState, type FormEvent } from "react";
import { ApiError, type AdminApi } from "./api";
import {
  FEATURES,
  errorNames,
  eventNames,
  phaseName,
  relative,
} from "./labels";
import type {
  AccessRecord,
  AdminUser,
  Device,
  Devices,
  Feature,
} from "./types";

type Tab = "users" | "devices";
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

function Dashboard({ api }: { api: AdminApi }) {
  const [tab, setTab] = useState<Tab>("users"),
    [users, setUsers] = useState<AdminUser[]>(),
    [devices, setDevices] = useState<Devices>({}),
    [error, setError] = useState(""),
    [toast, setToast] = useState("");
  const load = useCallback(async () => {
    setError("");
    try {
      const [u, d] = await Promise.all([api.listUsers(), api.devices()]);
      setUsers(u);
      setDevices(d);
    } catch (e) {
      setError(message(e));
      if (e instanceof ApiError && e.status === 401) await api.signOut();
    }
  }, [api]);
  useEffect(() => {
    void load();
  }, [load]);
  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(""), 2600);
    return () => clearTimeout(t);
  }, [toast]);
  // Aplica un cambio del backend; ante conflicto de versión recarga para mostrar la decisión vigente.
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
      setToast(done);
    } catch (e) {
      setError(message(e));
      if (e instanceof ApiError && e.code === "VERSION_CONFLICT") await load();
    }
  };
  const emailOf = (uid?: string) =>
    users?.find((u) => u.uid === uid)?.email ?? uid ?? "—";
  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true">
            💊
          </span>
          <strong>Badi · Administración</strong>
          {api.demo && <span className="chip warn">Demostración</span>}
        </div>
        <nav className="tabs" aria-label="Secciones">
          {(["users", "devices"] as Tab[]).map((t) => (
            <button
              key={t}
              className={tab === t ? "tab active" : "tab"}
              aria-pressed={tab === t}
              onClick={() => setTab(t)}
            >
              {t === "users" ? "Usuarios y permisos" : "Dispositivos"}
            </button>
          ))}
        </nav>
        <div className="row">
          <span className="muted small">{api.email()}</span>
          <button className="ghost" onClick={() => void load()}>
            Actualizar
          </button>
          <button className="ghost" onClick={() => void api.signOut()}>
            Cerrar sesión
          </button>
        </div>
      </header>
      <main className="content">
        {error && (
          <p className="error banner" role="alert">
            {error}
            <button
              className="link"
              aria-label="Cerrar error"
              onClick={() => setError("")}
            >
              ✕
            </button>
          </p>
        )}
        {!users ? (
          <p className="muted">Cargando datos del backend…</p>
        ) : tab === "users" ? (
          <UsersView users={users} apply={apply} api={api} />
        ) : (
          <DevicesView devices={devices} emailOf={emailOf} />
        )}
      </main>
      {toast && (
        <div className="toast" role="status">
          {toast}
        </div>
      )}
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

function DevicesView({
  devices,
  emailOf,
}: {
  devices: Devices;
  emailOf: (uid?: string) => string;
}) {
  const entries = Object.entries(devices);
  if (!entries.length)
    return <p className="muted">No hay dispositivos registrados.</p>;
  return (
    <div className="devices">
      {entries.map(([id, d]) => (
        <DeviceCard key={id} id={id} device={d} emailOf={emailOf} />
      ))}
    </div>
  );
}

function DeviceCard({
  id,
  device,
  emailOf,
}: {
  id: string;
  device: Device;
  emailOf: (uid?: string) => string;
}) {
  const program = device.v2?.program,
    state = device.v2?.state ?? {},
    regimens = Object.values(program?.regimens ?? {}),
    events = Object.values(device.v2?.events ?? {})
      .sort((a, b) => b.actualAt - a.actualAt)
      .slice(0, 8);
  const positions = program?.positions ?? state.positions ?? 5;
  const fresh = !!state.updatedAt && Date.now() - state.updatedAt < 30000;
  return (
    <article className="card device">
      <header className="user-head">
        <div>
          <h2>{id}</h2>
          <span className="muted small">
            Responsable: {emailOf(device.ownerUid)} · ESP32:{" "}
            {emailOf(device.deviceUid)}
          </span>
        </div>
        <span className={`chip ${fresh ? "ok" : "warn"}`}>
          {fresh ? "En línea" : `Visto ${relative(state.updatedAt)}`}
        </span>
      </header>
      <div className="device-body">
        <Carousel positions={positions} regimens={regimens} />
        <dl className="facts">
          <dt>Fase</dt>
          <dd>{phaseName(state.phase)}</dd>
          <dt>Calibrado</dt>
          <dd>{state.calibrated ? "Sí" : "No"}</dd>
          <dt>Revisión</dt>
          <dd>
            {state.appliedRevision ?? "—"} aplicada / {program?.revision ?? "—"}{" "}
            publicada
          </dd>
          <dt>Modo</dt>
          <dd>
            {(state.simulation ?? program?.targetMode === "simulation")
              ? "Simulación"
              : "Hardware"}
          </dd>
          <dt>Almacenamiento</dt>
          <dd>{state.storageHealthy === false ? "Con fallas" : "Correcto"}</dd>
          <dt>Blíster</dt>
          <dd>{state.blisterPresent === false ? "Ausente" : "Presente"}</dd>
        </dl>
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
      {events.length ? (
        <ul className="list">
          {events.map((e) => (
            <li key={e.doseId + e.type}>
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

/** Cinco posiciones: 0 es el retorno vacío y 1..4 son compartimentos útiles. */
function Carousel({
  positions,
  regimens,
}: {
  positions: number;
  regimens: { compartment: number; name: string; enabled: boolean }[];
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
    </svg>
  );
}
