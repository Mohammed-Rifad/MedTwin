"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

import { api } from "@/lib/api";
import { useLiveEvent } from "@/lib/live";
import { playAlarm } from "@/lib/sound";
import type { Alert } from "@/lib/types";

const SHOW_FOR_MS = 15_000;

/** Pop-ups in the corner for new critical alerts, with a sound. Each alert pops up once. */
export function AlertToasts() {
  const [toasts, setToasts] = useState<Alert[]>([]);
  const shown = useRef(new Set<number>());

  useLiveEvent<Alert>("alert_update", (alert) => {
    // Someone acknowledged or resolved it (here or on another screen): take the pop-up away.
    if (alert.status !== "OPEN") {
      setToasts((current) => current.filter((toast) => toast.id !== alert.id));
      return;
    }
    if (alert.severity !== "CRITICAL" || shown.current.has(alert.id)) return;
    shown.current.add(alert.id);
    setToasts((current) => [alert, ...current].slice(0, 4));
    playAlarm();
  });

  // Each pop-up disappears by itself after a while (the alert stays on the Alerts page).
  useEffect(() => {
    if (toasts.length === 0) return;
    const oldest = toasts[toasts.length - 1];
    const timer = setTimeout(() => setToasts((current) => current.filter((toast) => toast.id !== oldest.id)), SHOW_FOR_MS);
    return () => clearTimeout(timer);
  }, [toasts]);

  async function acknowledge(alert: Alert) {
    setToasts((current) => current.filter((toast) => toast.id !== alert.id));
    await api(`/api/alerts/${alert.id}/acknowledge/`, { method: "POST" }).catch(() => undefined);
  }

  if (toasts.length === 0) return null;
  return (
    <div className="fixed right-4 top-4 z-40 flex w-96 max-w-[calc(100vw-2rem)] flex-col gap-2" role="alert" aria-live="assertive">
      {toasts.map((alert) => (
        <div key={alert.id} className="rounded-xl border border-red-200 bg-white p-4 shadow-lg ring-4 ring-red-100">
          <p className="text-xs font-semibold uppercase tracking-wide text-red-600">Critical alert</p>
          <p className="mt-1 text-sm font-medium text-slate-800">{alert.message}</p>
          <div className="mt-3 flex gap-2">
            <button onClick={() => acknowledge(alert)} className="rounded-lg bg-red-600 px-3 py-1 text-xs font-medium text-white hover:bg-red-700">
              Acknowledge
            </button>
            <Link
              href={`/alerts?alert=${alert.id}`}
              onClick={() => setToasts((current) => current.filter((toast) => toast.id !== alert.id))}
              className="rounded-lg border border-slate-300 px-3 py-1 text-xs text-slate-700 hover:bg-slate-100"
            >
              View
            </Link>
            <button
              onClick={() => setToasts((current) => current.filter((toast) => toast.id !== alert.id))}
              className="ml-auto text-xs text-slate-400 hover:text-slate-600"
            >
              Dismiss
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
