import { useCallback, useEffect, useRef, useState } from "react";
import { bySeverity, conditions, newEvents, type Alert } from "./alerts";
import { sounds } from "./sound";
import type { Devices } from "./types";

const ALARM_EVERY_MS = 3000;
const TOAST_MS = 6000;
const LOG_LIMIT = 100;

/**
 * Estado de alertas del panel:
 * - `active`: condiciones vigentes de los sensores + eventos críticos aún sin reconocer.
 * - `log`: historial de lo ocurrido (aparición, resolución, eventos y comandos).
 * - Las críticas sin reconocer suenan en bucle y hacen parpadear el título de la pestaña.
 */
export function useAlerts(muted: boolean) {
  const [active, setActive] = useState<Alert[]>([]),
    [log, setLog] = useState<Alert[]>([]),
    [toasts, setToasts] = useState<Alert[]>([]),
    [acked, setAcked] = useState<ReadonlySet<string>>(new Set());
  const previous = useRef<Devices>(undefined),
    firstSeen = useRef(new Map<string, number>()),
    mutedRef = useRef(muted),
    activeRef = useRef(active);
  mutedRef.current = muted;
  activeRef.current = active;

  const notify = useCallback((items: Alert[]) => {
    if (!items.length) return;
    setLog((l) => [...items, ...l].slice(0, LOG_LIMIT));
    setToasts((t) =>
      [
        ...items.filter((a) => a.severity !== "info" || a.source !== "sensor"),
        ...t,
      ].slice(0, 4),
    );
    // La sirena crítica la gestiona el efecto de alarma; aquí solo avisos puntuales.
    if (mutedRef.current) return;
    if (items.some((a) => a.severity === "warning")) sounds.warning();
    else if (items.some((a) => a.severity === "success")) sounds.success();
  }, []);

  /** Procesa una lectura de dispositivos (más alertas del sistema, p. ej. backend caído). */
  const ingest = useCallback(
    (devices: Devices, now: number, extra: Alert[] = []) => {
      const seen = firstSeen.current;
      const current = [...conditions(devices, now), ...extra].map((a) => ({
        ...a,
        at: seen.get(a.id) ?? a.at,
      }));
      const ids = new Set(current.map((a) => a.id));
      const onset = current.filter((a) => !seen.has(a.id));
      const resolved: Alert[] = [];
      for (const [id] of seen)
        if (!ids.has(id)) {
          const old = activeRef.current.find((a) => a.id === id);
          seen.delete(id);
          if (old && old.severity !== "info")
            resolved.push({
              ...old,
              id: `${id}:resuelta:${now}`,
              severity: "success",
              title: `Resuelto: ${old.title}`,
              detail: "La condición dejó de presentarse.",
              at: now,
            });
        }
      onset.forEach((a) => seen.set(a.id, a.at));
      // Una condición resuelta que reaparece vuelve a alarmar.
      if (resolved.length)
        setAcked(
          (s) =>
            new Set(
              [...s].filter((id) => ids.has(id) || id.includes(":event:")),
            ),
        );
      const events =
        devices === previous.current
          ? []
          : newEvents(previous.current, devices);
      previous.current = devices;
      setActive((prev) =>
        [
          ...current,
          ...prev.filter((a) => a.source === "event"),
          ...events.filter(
            (e) => e.severity === "critical" || e.severity === "warning",
          ),
        ]
          .filter((a, i, all) => all.findIndex((b) => b.id === a.id) === i)
          .sort(bySeverity),
      );
      notify([...onset, ...events, ...resolved].sort(bySeverity));
    },
    [notify],
  );
  /** Confirmación o rechazo de un comando del administrador. */
  const command = useCallback(
    (severity: "success" | "warning", title: string, detail: string) =>
      notify([
        {
          id: `command:${Date.now()}:${Math.random()}`,
          severity,
          title,
          detail,
          at: Date.now(),
          source: "command",
        },
      ]),
    [notify],
  );

  const ack = useCallback((id: string) => {
    setAcked((s) => new Set(s).add(id));
    // Los eventos reconocidos salen de activas; las condiciones siguen visibles hasta resolverse.
    setActive((a) => a.filter((x) => x.id !== id || x.source !== "event"));
  }, []);
  const ackAll = useCallback(() => {
    setAcked((s) => new Set([...s, ...activeRef.current.map((a) => a.id)]));
    setActive((a) => a.filter((x) => x.source !== "event"));
  }, []);
  const dismissToast = useCallback(
    (id: string) => setToasts((t) => t.filter((x) => x.id !== id)),
    [],
  );

  useEffect(() => {
    if (!toasts.length) return;
    const t = setTimeout(() => setToasts((l) => l.slice(0, -1)), TOAST_MS);
    return () => clearTimeout(t);
  }, [toasts]);

  const pending = active.filter(
    (a) =>
      !acked.has(a.id) &&
      (a.severity === "critical" || a.severity === "warning"),
  );
  const alarming = pending.some((a) => a.severity === "critical");

  // Alarma sonora en bucle mientras haya críticas sin reconocer.
  useEffect(() => {
    if (!alarming || muted) return;
    sounds.alarm();
    const t = setInterval(sounds.alarm, ALARM_EVERY_MS);
    return () => clearInterval(t);
  }, [alarming, muted]);

  // Alarma visual en la pestaña del navegador, útil si el panel está en segundo plano.
  useEffect(() => {
    const base = document.title;
    if (!alarming) return;
    let on = false;
    const t = setInterval(() => {
      on = !on;
      document.title = on ? `⚠ ALERTA (${pending.length}) · Badi` : base;
    }, 1000);
    return () => {
      clearInterval(t);
      document.title = base;
    };
  }, [alarming, pending.length]);

  return {
    active,
    log,
    toasts,
    acked,
    pending,
    alarming,
    ingest,
    command,
    ack,
    ackAll,
    dismissToast,
  };
}
