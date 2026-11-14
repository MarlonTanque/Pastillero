import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type ReactNode,
} from "react";
import { Icon } from "./Icon";
import { request, listen } from "./api";
import {
  clock,
  dayKey,
  doseStatus,
  fullDate,
  localInput,
  monday,
  moveWeek,
  newId,
  weekDays,
} from "./calendar";
import {
  defaults,
  type Action,
  type Feature,
  type Medication,
  type Occurrence,
  type Settings,
  type Snapshot,
  type View,
} from "./types";

const nav: { id: View; label: string; icon: string }[] = [
  { id: "home", label: "Inicio", icon: "home" },
  { id: "calendar", label: "Calendario", icon: "calendar" },
  { id: "medications", label: "Medicamentos", icon: "pill" },
  { id: "history", label: "Historial", icon: "history" },
  { id: "settings", label: "Ajustes", icon: "settings" },
];
const statusNames: Record<string, string> = {
  CONFIRMED: "Confirmada",
  MISSED: "Omitida",
  BLOCKED: "Sin blíster",
  RECOVERY: "Revisar reinicio",
  NO_EXIT: "Sin salida detectada",
  STARTED: "Entrega iniciada",
  PROGRAMADA: "Programada",
  SIN_REGISTRO: "Sin registro",
};
const BLOCKED = "Función deshabilitada por el administrador";
const route = (): View =>
  nav.find((x) => `#/${x.id}` === location.hash)?.id || "home";

function Modal({
  title,
  children,
  onClose,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null;
    (
      ref.current?.querySelector<HTMLElement>("input,select") ||
      ref.current?.querySelector<HTMLElement>("button")
    )?.focus();
    const key = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
      if (e.key === "Tab") {
        const items = Array.from(
          ref.current?.querySelectorAll<HTMLElement>(
            'button,input,select,textarea,[tabindex="0"]',
          ) || [],
        ).filter((x) => !x.hasAttribute("disabled"));
        const first = items[0],
          last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last?.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener("keydown", key);
    return () => {
      document.removeEventListener("keydown", key);
      previous?.focus();
    };
  }, [onClose]);
  return (
    <div
      className="modal-shade"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={ref}
        className="glass modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <div className="row spread">
          <h2 id="modal-title">{title}</h2>
          <button className="icon-button" aria-label="Cerrar" onClick={onClose}>
            <Icon name="close" />
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}
function DoseRow({ dose, data }: { dose: Occurrence; data: Snapshot }) {
  const status = doseStatus(dose.id, dose.scheduledAt, data.events, data.now);
  return (
    <div className="dose-row">
      <div className="dose-time">
        {clock(dose.scheduledAt)}
        <small>
          {dayKey(dose.scheduledAt) === dayKey(Date.now())
            ? "Hoy"
            : new Date(dose.scheduledAt).toLocaleDateString("es-MX", {
                day: "numeric",
                month: "short",
              })}
        </small>
      </div>
      <div className="pill-icon">
        <Icon name="pill" />
      </div>
      <div className="grow">
        <strong>{dose.name}</strong>
        <small>Compartimento {dose.compartment}</small>
      </div>
      <span
        className={`tag ${status === "MISSED" || status === "NO_EXIT" ? "tag-alert" : ""}`}
      >
        {statusNames[status] || status}
      </span>
    </div>
  );
}
function Compartments({
  positions,
  next,
}: {
  positions: number;
  next?: number;
}) {
  return (
    <svg
      viewBox="0 0 260 260"
      className="compartments"
      role="img"
      aria-label={`${positions} posiciones; cero reservado al retorno`}
    >
      <circle cx="130" cy="130" r="108" className="orbit" />
      {Array.from({ length: positions }, (_, i) => {
        const a = (i / positions) * 2 * Math.PI - Math.PI / 2,
          x = 130 + 83 * Math.cos(a),
          y = 130 + 83 * Math.sin(a);
        return (
          <g key={i}>
            <circle
              cx={x}
              cy={y}
              r="27"
              className={
                i === 0 ? "slot zero" : i === next ? "slot active" : "slot"
              }
            />
            <text
              x={x}
              y={y + 5}
              textAnchor="middle"
              className={i === next ? "slot-label selected" : "slot-label"}
            >
              {i === 0 ? "0" : `C${i}`}
            </text>
          </g>
        );
      })}
      <circle cx="130" cy="130" r="30" className="hub" />
      <path d="m120 132 7 7 14-17" className="hub-mark" />
      <text x="130" y="253" textAnchor="middle" className="diagram-caption">
        Cero reservado · referencia manual
      </text>
    </svg>
  );
}
function MedicationForm({
  initial,
  settings,
  onSave,
}: {
  initial?: Medication;
  settings: Settings;
  onSave: (m: Medication) => Promise<void>;
}) {
  const [m, setM] = useState<Medication>(
    initial || {
      id: newId(),
      name: "",
      mode: "daily",
      times: ["08:00"],
      zoneId: Intl.DateTimeFormat().resolvedOptions().timeZone,
      compartment: 1,
      intervalMinutes: 480,
      startAt: Date.now() + 180000,
      endAt: 0,
      enabled: true,
    },
  );
  const [times, setTimes] = useState(m.times.join(", ")),
    [error, setError] = useState(""),
    [saving, setSaving] = useState(false);
  const submit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      if (!m.name.trim()) throw new Error("Escribe el nombre del medicamento.");
      await onSave({
        ...m,
        times: times
          .split(",")
          .map((x) => x.trim())
          .filter(Boolean),
      });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };
  return (
    <form onSubmit={submit} className="form-grid">
      <label className="full">
        Nombre del medicamento
        <input
          maxLength={80}
          required
          value={m.name}
          onChange={(e) => setM({ ...m, name: e.target.value })}
          placeholder="Nombre de tu medicamento"
        />
      </label>
      <label>
        Compartimento
        <select
          value={m.compartment}
          onChange={(e) => setM({ ...m, compartment: +e.target.value })}
        >
          {Array.from({ length: settings.positions - 1 }, (_, i) => (
            <option key={i} value={i + 1}>
              Compartimento {i + 1}
            </option>
          ))}
        </select>
      </label>
      <label>
        Tipo de horario
        <select
          value={m.mode}
          onChange={(e) =>
            setM({ ...m, mode: e.target.value as Medication["mode"] })
          }
        >
          <option value="daily">Horas diarias</option>
          <option value="interval">Cada cierto intervalo</option>
        </select>
      </label>
      {m.mode === "daily" ? (
        <label className="full">
          Horas (24 h, separadas por coma)
          <input
            value={times}
            onChange={(e) => setTimes(e.target.value)}
            placeholder="08:00, 20:00"
            required
          />
          <small>Hasta seis horas independientes para este medicamento.</small>
        </label>
      ) : (
        <label className="full">
          Intervalo en minutos
          <input
            type="number"
            min={15}
            max={10080}
            value={m.intervalMinutes}
            onChange={(e) => setM({ ...m, intervalMinutes: +e.target.value })}
          />
          <small>El intervalo se cuenta desde el inicio de esta pauta.</small>
        </label>
      )}
      <label>
        Inicio
        <input
          type="datetime-local"
          required
          value={localInput(m.startAt)}
          onChange={(e) => {
            const n = +new Date(e.target.value);
            if (Number.isFinite(n)) setM({ ...m, startAt: n });
          }}
        />
      </label>
      <label>
        Fin opcional
        <input
          type="datetime-local"
          value={m.endAt ? localInput(m.endAt) : ""}
          onChange={(e) =>
            setM({
              ...m,
              endAt: e.target.value ? +new Date(e.target.value) : 0,
            })
          }
        />
      </label>
      <label className="full">
        Zona horaria
        <input
          value={m.zoneId}
          onChange={(e) => setM({ ...m, zoneId: e.target.value })}
        />
      </label>
      <label className="check-line full">
        <input
          type="checkbox"
          checked={m.enabled}
          onChange={(e) => setM({ ...m, enabled: e.target.checked })}
        />
        Pauta activa
      </label>
      {error && (
        <p className="form-error full" role="alert">
          {error}
        </p>
      )}
      <button className="primary full" disabled={saving} type="submit">
        {saving ? "Guardando…" : "Guardar medicamento"}
      </button>
      <p className="help full">
        Guardar conserva la pauta en este equipo. Publicar el plan solicita su
        sincronización.
      </p>
    </form>
  );
}

export function App() {
  const [view, setView] = useState<View>(route),
    [data, setData] = useState<Snapshot>(),
    [week, setWeek] = useState(monday),
    [selected, setSelected] = useState(dayKey(Date.now()));
  const [theme, setTheme] = useState(
      () => localStorage.getItem("badi-theme") || "light",
    ),
    [error, setError] = useState(""),
    [toast, setToast] = useState(""),
    [busy, setBusy] = useState(false);
  const [editing, setEditing] = useState<Medication | null | undefined>(
      undefined,
    ),
    [deleting, setDeleting] = useState<Medication>();
  const [reconciling, setReconciling] = useState(false);
  const [settings, setSettings] = useState<Settings>(defaults),
    [historyFilter, setHistoryFilter] = useState("all");
  useEffect(() => {
    window.__badiBack = () => {
      if (editing !== undefined) {
        setEditing(undefined);
        return true;
      }
      if (deleting) {
        setDeleting(undefined);
        return true;
      }
      if (reconciling) {
        setReconciling(false);
        return true;
      }
      return false;
    };
    return () => {
      delete window.__badiBack;
    };
  }, [editing, deleting, reconciling]);
  useEffect(() => {
    const fn = () => setView(route());
    window.addEventListener("hashchange", fn);
    return () => window.removeEventListener("hashchange", fn);
  }, []);
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("badi-theme", theme);
  }, [theme]);
  useEffect(() => listen(setData), []);
  useEffect(() => {
    request("snapshot", { weekStart: +week })
      .then(setData)
      .catch((e) => setError(e.message));
  }, [week]);
  useEffect(() => {
    if (data) setSettings(data.settings);
  }, [
    data?.settings.positions,
    data?.settings.horizonDays,
    data?.settings.ledEnabled,
    data?.settings.buzzerEnabled,
    data?.settings.lcdEnabled,
    data?.settings.exitSensorEnabled,
    data?.settings.servoEnabled,
    data?.settings.pumpEnabled,
    data?.settings.pumpDurationMs,
  ]);
  useEffect(() => {
    const timer = setInterval(() => {
      request("snapshot", { weekStart: +week })
        .then(setData)
        .catch(() => {});
    }, 15000);
    return () => clearInterval(timer);
  }, [week]);
  useEffect(() => {
    if (toast) {
      const t = setTimeout(() => setToast(""), 4000);
      return () => clearTimeout(t);
    }
  }, [toast]);
  const act = async (
    action: Action,
    payload: Record<string, unknown> = {},
    message = "Cambios guardados",
  ) => {
    setBusy(true);
    setError("");
    try {
      const result = await request(action, payload);
      if (result?.medications) setData(result);
      setToast(message);
    } catch (e) {
      setError((e as Error).message);
      throw e;
    } finally {
      setBusy(false);
    }
  };
  const doAction = (
    action: Action,
    payload: Record<string, unknown> = {},
    message?: string,
  ) => {
    void act(action, payload, message).catch(() => {});
  };
  const now = Date.now(),
    next = data?.occurrences.find(
      (x) =>
        x.scheduledAt >= now &&
        !data.events.some((e) => e.doseId === x.id && e.type !== "STARTED"),
    );
  const today =
    data?.occurrences.filter((x) => dayKey(x.scheduledAt) === dayKey(now)) ||
    [];
  const can = (feature: Feature) => data?.features?.[feature] !== false;
  const freshness =
    data?.device.updatedAt && now - data.device.updatedAt < 30000;
  const navTo = (id: View) => {
    location.hash = `/${id}`;
  };
  const changeWeek = (delta: number) => {
    const next = moveWeek(week, delta);
    setWeek(next);
    setSelected(dayKey(next));
  };
  if (!data)
    return (
      <main className="loading">
        <span className="brand-mark">
          <Icon name="pill" size={30} />
        </span>
        <h1>Pastillero Badi</h1>
        <p role="status">{error || "Preparando tus horarios…"}</p>
        {error && (
          <button onClick={() => location.reload()}>Volver a intentar</button>
        )}
      </main>
    );
  return (
    <div className="app-shell">
      <aside className="sidebar glass">
        <a className="brand" href="#/home" aria-label="Badi, inicio">
          <span className="brand-mark">
            <Icon name="pill" size={27} />
          </span>
          <span>
            Badi<small>Tu rutina, en orden.</small>
          </span>
        </a>
        <nav aria-label="Navegación principal">
          {nav.map((x) => (
            <a
              key={x.id}
              href={`#/${x.id}`}
              className={view === x.id ? "nav-item current" : "nav-item"}
              aria-current={view === x.id ? "page" : undefined}
            >
              <Icon name={x.icon} />
              <span>{x.label}</span>
              {x.id === "medications" && (
                <small>
                  {data.medications.filter((m) => m.enabled).length}
                </small>
              )}
            </a>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="safe-note">
            <Icon name="shield" />
            <strong>Modo simulación</strong>
            <small>Sin movimientos ni salidas físicas.</small>
          </div>
          <button
            className="subtle account"
            onClick={() =>
              doAction(data.signedIn ? "signOut" : "signIn", {}, "")
            }
          >
            <Icon name="logout" />
            <span>
              {data.signedIn ? "Cerrar sesión" : "Entrar a mi cuenta"}
            </span>
          </button>
          <small className="version">Pastillero Badi · 2.0</small>
        </div>
      </aside>
      <main className="main-content">
        <header className="topbar">
          <div className="breadcrumb">
            Mi pastillero <span>/</span> {nav.find((x) => x.id === view)?.label}
          </div>
          <div className="row">
            <span className={`connection-pill ${freshness ? "online" : ""}`}>
              <span className="dot" />
              {freshness ? "Dispositivo reciente" : "Sin señal reciente"}
            </span>
            <button
              className="icon-button"
              aria-label={
                theme === "light" ? "Activar tema oscuro" : "Activar tema claro"
              }
              onClick={() => setTheme(theme === "light" ? "dark" : "light")}
            >
              <Icon name={theme === "light" ? "moon" : "sun"} />
            </button>
            <div className="avatar" aria-label="Perfil Badi">
              B
            </div>
          </div>
        </header>
        {data.preview && (
          <div className="notice">
            <Icon name="shield" size={18} />
            Vista web de demostración. Usa el APK para guardar en Room y
            conectar con Firebase.
          </div>
        )}
        {error && (
          <div className="error-banner" role="alert">
            <span>{error}</span>
            <button
              className="icon-button"
              aria-label="Cerrar error"
              onClick={() => setError("")}
            >
              <Icon name="close" size={18} />
            </button>
          </div>
        )}
        <section className="page-heading">
          <div>
            <p className="eyebrow">PASTILLERO INTELIGENTE</p>
            <h1>
              {view === "home"
                ? "Un día más, a tu ritmo."
                : view === "calendar"
                  ? "Cada dosis, en su momento."
                  : view === "medications"
                    ? "Tus medicamentos."
                    : view === "history"
                      ? "Tu historial, siempre contigo."
                      : "Hecho a tu medida."}
            </h1>
            <p className="muted">
              {view === "home"
                ? fullDate(now)
                : view === "calendar"
                  ? "Consulta la semana y organiza cada pauta con fechas reales."
                  : view === "medications"
                    ? "Horarios e intervalos independientes para cada medicamento."
                    : view === "history"
                      ? "Eventos guardados en este equipo, también sin conexión."
                      : "Preferencias del pastillero y de sus avisos."}
            </p>
          </div>
          {view !== "settings" && view !== "history" && can("medications") && (
            <button className="primary" onClick={() => setEditing(null)}>
              <Icon name="plus" size={19} />
              Agregar medicamento
            </button>
          )}
        </section>
        {view === "home" && (
          <>
            <div className="home-grid">
              <section className="hero glass">
                <div className="row spread">
                  <span className="tag tag-green">
                    <span className="dot" />
                    TU PRÓXIMA DOSIS
                  </span>
                  <Icon name="pill" size={28} />
                </div>
                <div className="hero-time">
                  {next ? clock(next.scheduledAt) : "Todo por organizar"}
                  {next && <span> h</span>}
                </div>
                <h2>{next?.name || "Comienza con tu primer medicamento"}</h2>
                <p>
                  {next
                    ? `${fullDate(next.scheduledAt)} · Compartimento ${next.compartment}`
                    : "Guarda una pauta y verás aquí tu próxima dosis."}
                </p>
                <div className="hero-footer">
                  <span className="small-icon">
                    <Icon name="bell" size={19} />
                  </span>
                  <span>
                    {next
                      ? "La toma se confirma con el botón físico."
                      : "Horarios claros. Seguimiento en un solo lugar."}
                  </span>
                  <button
                    className="circle-button"
                    aria-label="Ver calendario"
                    onClick={() => navTo("calendar")}
                  >
                    <Icon name="arrow" />
                  </button>
                </div>
              </section>
              <section className="glass device-card">
                <div className="row spread">
                  <h2>Tu pastillero</h2>
                  <span className="tag">SIMULACIÓN</span>
                </div>
                <Compartments
                  positions={data.settings.positions}
                  next={next?.compartment}
                />
                <div className="device-caption">
                  <strong>
                    {data.settings.positions} posiciones ·{" "}
                    {data.settings.positions - 1} de dosis
                  </strong>
                  <small>
                    {data.device.calibrated
                      ? "Referencia calibrada"
                      : "Referencia física pendiente de calibración"}
                  </small>
                </div>
              </section>
            </div>
            <div className="stat-grid">
              <div className="glass stat">
                <span className="stat-icon">
                  <Icon name="pill" />
                </span>
                <div>
                  <strong>
                    {data.medications.filter((m) => m.enabled).length}
                  </strong>
                  <small>Medicamentos activos</small>
                </div>
              </div>
              <div className="glass stat">
                <span className="stat-icon">
                  <Icon name="calendar" />
                </span>
                <div>
                  <strong>{data.occurrences.length}</strong>
                  <small>Dosis de la semana visible</small>
                </div>
              </div>
              <div className="glass stat">
                <span className="stat-icon">
                  <Icon name="check" />
                </span>
                <div>
                  <strong>
                    {
                      data.events.filter(
                        (e) => e.type === "CONFIRMED" && !e.simulation,
                      ).length
                    }
                  </strong>
                  <small>Confirmaciones físicas</small>
                </div>
              </div>
            </div>
            <section className="glass section-card">
              <div className="row spread">
                <div>
                  <p className="eyebrow">TU RUTINA</p>
                  <h2>Para hoy</h2>
                </div>
                <button
                  className="text-button"
                  onClick={() => navTo("calendar")}
                >
                  Ver semana <Icon name="arrow" size={16} />
                </button>
              </div>
              {today.length ? (
                today.map((d) => <DoseRow key={d.id} dose={d} data={data} />)
              ) : (
                <div className="empty-inline">
                  <Icon name="calendar" size={32} />
                  <p>No hay dosis programadas para hoy.</p>
                  {can("medications") && (
                    <button
                      className="text-button"
                      onClick={() => setEditing(null)}
                    >
                      Crear una pauta
                    </button>
                  )}
                </div>
              )}
            </section>
          </>
        )}
        {view === "calendar" && (
          <section className="glass section-card calendar-card">
            <div className="row spread wrap">
              <div>
                <h2>
                  {week.toLocaleDateString("es-MX", {
                    month: "long",
                    year: "numeric",
                  })}
                </h2>
                <p className="muted small">
                  {data.occurrences.length} dosis en esta semana ·{" "}
                  {Intl.DateTimeFormat().resolvedOptions().timeZone}
                </p>
              </div>
              <div className="row">
                <button
                  className="icon-button"
                  aria-label="Semana anterior"
                  onClick={() => changeWeek(-1)}
                >
                  <Icon name="back" />
                </button>
                <button
                  className="secondary"
                  onClick={() => {
                    setWeek(monday());
                    setSelected(dayKey(now));
                  }}
                >
                  Hoy
                </button>
                <button
                  className="icon-button"
                  aria-label="Semana siguiente"
                  onClick={() => changeWeek(1)}
                >
                  <Icon name="arrow" />
                </button>
              </div>
            </div>
            <div className="week-strip" aria-label="Días de la semana">
              {weekDays(week).map((d) => {
                const k = dayKey(d),
                  count = data.occurrences.filter(
                    (x) => dayKey(x.scheduledAt) === k,
                  ).length;
                return (
                  <button
                    key={k}
                    className={`day-button ${selected === k ? "selected" : ""} ${k === dayKey(now) ? "today" : ""}`}
                    aria-pressed={selected === k}
                    onClick={() => setSelected(k)}
                  >
                    <span>
                      {d.toLocaleDateString("es-MX", { weekday: "short" })}
                    </span>
                    <strong>{d.getDate()}</strong>
                    <small>{count ? `${count} dosis` : "—"}</small>
                  </button>
                );
              })}
            </div>
            <div className="day-heading">
              <h3>{fullDate(+new Date(`${selected}T12:00:00`))}</h3>
              <span className="tag">
                {
                  data.occurrences.filter(
                    (x) => dayKey(x.scheduledAt) === selected,
                  ).length
                }{" "}
                dosis
              </span>
            </div>
            {data.occurrences
              .filter((x) => dayKey(x.scheduledAt) === selected)
              .map((d) => (
                <DoseRow key={d.id} dose={d} data={data} />
              ))}
            {!data.occurrences.some(
              (x) => dayKey(x.scheduledAt) === selected,
            ) && (
              <div className="empty-inline">
                <Icon name="calendar" size={36} />
                <p>Este día está libre de dosis.</p>
                <small>
                  Las pautas activas aparecerán aquí en su fecha
                  correspondiente.
                </small>
              </div>
            )}
          </section>
        )}
        {view === "medications" && (
          <div className="med-grid">
            {data.medications.map((m, i) => (
              <article className="glass medication-card" key={m.id}>
                <div className="row spread">
                  <span className={`med-symbol color-${i % 3}`}>
                    <Icon name="pill" size={26} />
                  </span>
                  <span className="tag">
                    {m.enabled ? "Activa" : "En pausa"}
                  </span>
                </div>
                <h2>{m.name}</h2>
                <p className="muted">Compartimento {m.compartment}</p>
                <div className="schedule-summary">
                  <Icon name="calendar" size={18} />
                  <span>
                    {m.mode === "daily"
                      ? m.times.join(" · ")
                      : `Cada ${m.intervalMinutes} minutos`}
                  </span>
                </div>
                <small className="muted">
                  Desde {fullDate(m.startAt)} · {m.zoneId}
                </small>
                {can("medications") && (
                  <div className="med-actions">
                    <button
                      className="text-button"
                      onClick={() => setEditing(m)}
                    >
                      <Icon name="edit" size={16} />
                      Editar pauta
                    </button>
                    <button
                      className="icon-button danger"
                      aria-label={`Eliminar ${m.name}`}
                      onClick={() => setDeleting(m)}
                    >
                      <Icon name="trash" size={18} />
                    </button>
                  </div>
                )}
              </article>
            ))}
            {!data.medications.length && (
              <section className="glass empty-card">
                <span className="empty-icon">
                  <Icon name="pill" size={40} />
                </span>
                <h2>Una rutina empieza con un paso.</h2>
                <p>
                  Agrega tu primer medicamento y define sus propios horarios.
                </p>
                {can("medications") && (
                  <button className="primary" onClick={() => setEditing(null)}>
                    <Icon name="plus" size={18} />
                    Agregar medicamento
                  </button>
                )}
              </section>
            )}
          </div>
        )}
        {view === "history" && (
          <section className="glass section-card">
            <div className="row spread wrap">
              <h2>Registro de eventos</h2>
              <select
                aria-label="Filtrar historial"
                value={historyFilter}
                onChange={(e) => setHistoryFilter(e.target.value)}
              >
                <option value="all">Todos los eventos</option>
                <option value="physical">Solo físicos</option>
                <option value="simulation">Solo simulación</option>
                <option value="MISSED">Dosis omitidas</option>
              </select>
            </div>
            <p className="muted small">
              La salida detectada y la confirmación física son registros
              distintos. Una simulación no cuenta como toma real.
            </p>
            {data.events
              .filter(
                (e) =>
                  historyFilter === "all" ||
                  (historyFilter === "physical" && !e.simulation) ||
                  (historyFilter === "simulation" && e.simulation) ||
                  e.type === historyFilter,
              )
              .map((e) => (
                <div className="event-row" key={e.id}>
                  <span
                    className={`event-dot ${e.type === "MISSED" || e.type === "NO_EXIT" ? "alert" : ""}`}
                  />
                  <div className="grow">
                    <strong>
                      {statusNames[e.type] || e.type}{" "}
                      <span className="tag">
                        {e.simulation ? "SIMULACIÓN" : "FÍSICO"}
                      </span>
                    </strong>
                    <small>
                      {data.medications.find((m) => m.id === e.medicationId)
                        ?.name || `Compartimento ${e.compartment}`}{" "}
                      · Programada {fullDate(e.scheduledAt)}{" "}
                      {clock(e.scheduledAt)}
                    </small>
                    <small>
                      Registrada{" "}
                      {e.actualAt > 1700000000000
                        ? `${fullDate(e.actualAt)} ${clock(e.actualAt)}`
                        : "Reloj sin sincronizar"}
                      {e.type === "CONFIRMED"
                        ? ` · diferencia ${Math.round((e.actualAt - e.scheduledAt) / 1000)} s`
                        : ""}
                    </small>
                  </div>
                </div>
              ))}
            {!data.events.length && (
              <div className="empty-inline">
                <Icon name="history" size={38} />
                <p>Todavía no hay eventos guardados.</p>
                <small>
                  Los registros recibidos se conservan en este equipo.
                </small>
              </div>
            )}
          </section>
        )}
        {view === "settings" && (
          <div className="settings-grid">
            <section className="glass section-card">
              <h2>Distribución y programación</h2>
              <p className="muted small">
                El cero se conserva como posición ciega de retorno, como en el
                montaje original.
              </p>
              <div className="form-grid">
                <label>
                  Posiciones totales
                  <select
                    value={settings.positions}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        positions: +e.target.value as 4 | 5,
                      })
                    }
                  >
                    <option value={4}>4 posiciones · 3 de dosis</option>
                    <option value={5}>5 posiciones · 4 de dosis</option>
                  </select>
                </label>
                <label>
                  Días a publicar
                  <input
                    type="number"
                    min={1}
                    max={7}
                    value={settings.horizonDays}
                    onChange={(e) =>
                      setSettings({ ...settings, horizonDays: +e.target.value })
                    }
                  />
                </label>
              </div>
              <p className="help">
                Hasta 96 dosis por plan. Si se supera el límite, se informa el
                error y no se recorta la programación. Cambiar la geometría
                exige recalibrar el dispositivo.
              </p>
              <h3>Avisos</h3>
              {(["ledEnabled", "buzzerEnabled"] as const).map((k) => (
                <label className="toggle-row" key={k}>
                  <span>
                    <strong>
                      {k === "ledEnabled"
                        ? "Indicadores LED"
                        : "Avisador sonoro"}
                    </strong>
                    <small>
                      {k === "ledEnabled"
                        ? "Espera de confirmación y alertas"
                        : "Aviso breve mientras haya espera o alerta"}
                    </small>
                  </span>
                  <input
                    type="checkbox"
                    role="switch"
                    checked={settings[k]}
                    onChange={(e) =>
                      setSettings({ ...settings, [k]: e.target.checked })
                    }
                  />
                </label>
              ))}
              <h3>Periféricos opcionales</h3>
              <p className="help">
                Estas preferencias no habilitan salidas bloqueadas en el
                firmware. Todos los periféricos nuevos están desactivados por
                defecto.
              </p>
              {(
                [
                  ["lcdEnabled", "Pantalla LCD 16 × 2"],
                  ["exitSensorEnabled", "Sensor de salida"],
                  ["servoEnabled", "Compuerta con servomotor"],
                  ["pumpEnabled", "Agua después de confirmar"],
                ] as const
              ).map(([k, label]) => (
                <label className="toggle-row" key={k}>
                  <span>
                    <strong>{label}</strong>
                  </span>
                  <input
                    type="checkbox"
                    role="switch"
                    checked={settings[k]}
                    onChange={(e) =>
                      setSettings({ ...settings, [k]: e.target.checked })
                    }
                  />
                </label>
              ))}
              {settings.pumpEnabled && (
                <label>
                  Tiempo de bomba (ms)
                  <input
                    type="number"
                    min={500}
                    max={5000}
                    step={100}
                    value={settings.pumpDurationMs}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        pumpDurationMs: +e.target.value,
                      })
                    }
                  />
                </label>
              )}
              {!can("deviceSettings") && <p className="help">{BLOCKED}</p>}
              <button
                className="primary"
                disabled={busy || !can("deviceSettings")}
                onClick={() =>
                  doAction(
                    "savePreferences",
                    settings as unknown as Record<string, unknown>,
                  )
                }
              >
                Guardar ajustes
              </button>
            </section>
            <section className="glass section-card sync-card">
              <span className="sync-icon">
                <Icon name="wifi" size={32} />
              </span>
              <h2>Conexión y privacidad</h2>
              <p>{data.connection}</p>
              <p className="help">
                El historial y las pautas se guardan primero en Room. Firebase
                utiliza la cuenta vinculada y sus permisos.
              </p>
              <div className="detail-line">
                <span>Sesión</span>
                <strong>
                  {data.authorized
                    ? "Responsable autorizado"
                    : data.signedIn
                      ? "Comprobando permisos"
                      : "Modo local"}
                </strong>
              </div>
              <div className="detail-line">
                <span>Revisión publicada</span>
                <strong>{data.revision}</strong>
              </div>
              <div className="detail-line">
                <span>Revisión aplicada</span>
                <strong>
                  {data.device.appliedRevision ?? "Sin telemetría V2"}
                </strong>
              </div>
              <p className="help">{data.programStatus}</p>
              {can("diagnostics") && (
                <>
                  <button
                    className="secondary"
                    onClick={() =>
                      doAction(
                        "ping",
                        {},
                        "Comprobación guardada; esperando respuesta",
                      )
                    }
                  >
                    Comprobar conexión
                  </button>
                  <p className="help">{data.pingStatus || "Sin solicitudes"}</p>
                </>
              )}
              {can("publish") && (
                <button
                  className="secondary"
                  onClick={() => doAction("retry", {}, "Reintento solicitado")}
                >
                  Reintentar sincronización
                </button>
              )}
              <button
                className="text-button"
                onClick={() =>
                  doAction(data.signedIn ? "signOut" : "signIn", {}, "")
                }
              >
                {data.signedIn ? "Cerrar sesión" : "Entrar a mi cuenta"}
              </button>
              {can("diagnostics") && (
                <button
                  className="text-button"
                  onClick={() => doAction("nativeView", {}, "")}
                >
                  Abrir vista clásica
                </button>
              )}
              <button
                className="text-button"
                disabled={!data.authorized || busy || !can("publish")}
                onClick={() => setReconciling(true)}
              >
                Revisar programa remoto
              </button>
            </section>
          </div>
        )}
        <footer className="glass publish-bar">
          <div>
            <span className={`dot ${data.pending ? "pending-dot" : ""}`} />
            <div>
              <strong>
                {data.pending
                  ? "Tienes cambios pendientes"
                  : "Tu programación, en orden"}
              </strong>
              <small>{can("publish") ? data.programStatus : BLOCKED}</small>
            </div>
          </div>
          <button
            className="primary"
            disabled={busy || !can("publish")}
            onClick={() =>
              doAction(
                "publish",
                {},
                data.authorized
                  ? "Plan guardado para sincronizar"
                  : "Plan validado en modo local",
              )
            }
          >
            <Icon name="check" size={18} />
            {busy
              ? "Procesando…"
              : data.authorized
                ? "Publicar plan"
                : "Validar plan local"}
          </button>
        </footer>
        <p className="page-footnote">
          <Icon name="shield" size={13} />
          Pastillero Badi · Confirmación en el dispositivo · Simulación activa
        </p>
      </main>
      {editing !== undefined && (
        <Modal
          title={editing ? "Editar medicamento" : "Un nuevo medicamento"}
          onClose={() => setEditing(undefined)}
        >
          <MedicationForm
            initial={editing || undefined}
            settings={data.settings}
            onSave={async (m) => {
              await act(
                "saveMedication",
                m as unknown as Record<string, unknown>,
              );
              setEditing(undefined);
            }}
          />
        </Modal>
      )}
      {reconciling && (
        <Modal
          title="Revisar la sincronización"
          onClose={() => setReconciling(false)}
        >
          <p>
            Si hay dos ediciones del plan, elige cuál conservar. El historial de
            eventos permanece en este equipo.
          </p>
          <p className="help">
            Traer el programa remoto reemplaza las pautas locales. Conservar las
            locales actualiza su revisión para que puedas revisarlas y
            publicarlas después.
          </p>
          <div className="form-grid">
            <button
              className="secondary full"
              disabled={busy}
              onClick={() => {
                void act("reload", {}, "Programa remoto revisado")
                  .then(() => setReconciling(false))
                  .catch(() => {});
              }}
            >
              Traer pautas remotas
            </button>
            <button
              className="primary full"
              disabled={busy}
              onClick={() => {
                void act(
                  "rebase",
                  {},
                  "Pautas locales conservadas; revisa y publica",
                )
                  .then(() => setReconciling(false))
                  .catch(() => {});
              }}
            >
              Conservar pautas locales
            </button>
          </div>
        </Modal>
      )}
      {deleting && (
        <Modal
          title="Eliminar esta pauta"
          onClose={() => setDeleting(undefined)}
        >
          <p>
            Se retirará <strong>{deleting.name}</strong> de tus próximas
            programaciones. El historial ya guardado se conserva.
          </p>
          <div className="row end">
            <button
              className="secondary"
              onClick={() => setDeleting(undefined)}
            >
              Conservar
            </button>
            <button
              className="primary danger-button"
              onClick={() => {
                void act(
                  "deleteMedication",
                  { id: deleting.id },
                  "Pauta eliminada; historial conservado",
                )
                  .then(() => setDeleting(undefined))
                  .catch(() => {});
              }}
            >
              Eliminar pauta
            </button>
          </div>
        </Modal>
      )}
      {toast && (
        <div role="status" className="toast">
          <Icon name="check" size={18} />
          {toast}
        </div>
      )}
    </div>
  );
}
