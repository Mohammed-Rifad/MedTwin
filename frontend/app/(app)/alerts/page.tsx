"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";

import { AlertStatusBadge, SeverityBadge } from "@/components/Badges";
import { errorText } from "@/components/forms/fields";
import { EmptyState, ErrorMessage, Loading } from "@/components/States";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatDateTime } from "@/lib/format";
import { useLiveEvent } from "@/lib/live";
import { CAN } from "@/lib/permissions";
import { ALERT_KIND_LABELS, type Alert, type Paginated } from "@/lib/types";

type Tab = "active" | "resolved";

const SEVERITY_RANK = { CRITICAL: 0, WARNING: 1, INFO: 2 } as const;

// Active alerts: unanswered first, then most severe, then newest. Resolved: newest first.
function sortAlerts(tab: Tab) {
  return (a: Alert, b: Alert) => {
    if (tab === "active") {
      const open = Number(b.status === "OPEN") - Number(a.status === "OPEN");
      if (open) return open;
      const severity = SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity];
      if (severity) return severity;
    }
    return b.created_at.localeCompare(a.created_at);
  };
}

const selectClass =
  "rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100";

function AlertsView() {
  const { hasRole } = useAuth();
  const router = useRouter();
  const selectedId = Number(useSearchParams().get("alert")) || null; // e.g. /alerts?alert=12
  const [tab, setTab] = useState<Tab>("active");
  const [severity, setSeverity] = useState("");
  const [kind, setKind] = useState("");
  const [alerts, setAlerts] = useState<Alert[] | null>(null);
  const [selected, setSelected] = useState<Alert | null>(null);
  const [error, setError] = useState("");

  const matchesView = useCallback(
    (alert: Alert) =>
      (tab === "active" ? alert.status !== "RESOLVED" : alert.status === "RESOLVED") &&
      (!severity || alert.severity === severity) &&
      (!kind || alert.kind === kind),
    [tab, severity, kind],
  );

  const load = useCallback(() => {
    const params = new URLSearchParams({ active: String(tab === "active"), page_size: "200", ordering: "-created_at" });
    if (severity) params.set("severity", severity);
    if (kind) params.set("kind", kind);
    api<Paginated<Alert>>(`/api/alerts/?${params}`)
      .then((page) => {
        setAlerts(page.results.sort(sortAlerts(tab)));
        setError("");
      })
      .catch((err: Error) => setError(err.message));
  }, [tab, severity, kind]);

  useEffect(load, [load]);
  useLiveEvent("reload", load);

  // Opened from a pop-up or a link (/alerts?alert=12): show that alert in the side panel.
  useEffect(() => {
    if (!selectedId) return;
    api<Alert>(`/api/alerts/${selectedId}/`)
      .then(setSelected)
      .catch(() => setSelected(null));
  }, [selectedId]);

  // Put a changed alert into the list (or take it out), and refresh the side panel if it's showing.
  const applyChange = useCallback(
    (alert: Alert) => {
      setAlerts((current) => {
        if (!current) return current;
        const others = current.filter((item) => item.id !== alert.id);
        return (matchesView(alert) ? [...others, alert] : others).sort(sortAlerts(tab));
      });
      setSelected((current) => (current?.id === alert.id ? alert : current));
    },
    [matchesView, tab],
  );

  useLiveEvent<Alert>("alert_update", applyChange);

  const select = (alert: Alert | null) => {
    setSelected(alert);
    router.replace(alert ? `/alerts?alert=${alert.id}` : "/alerts", { scroll: false });
  };

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-2xl font-semibold text-slate-800">Alerts</h1>
        <p className="text-slate-500">Problems the hospital noticed by itself. Acknowledge to say “I’m on it”; resolve when it’s dealt with.</p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="flex gap-1 rounded-lg bg-slate-100 p-1 text-sm">
          {(["active", "resolved"] as const).map((option) => (
            <button
              key={option}
              onClick={() => setTab(option)}
              className={`rounded-md px-3 py-1.5 ${tab === option ? "bg-white font-medium shadow-sm" : "text-slate-600"}`}
            >
              {option === "active" ? "Active" : "Resolved"}
            </button>
          ))}
        </div>
        <select className={selectClass} value={severity} onChange={(event) => setSeverity(event.target.value)}>
          <option value="">All severities</option>
          <option value="CRITICAL">Critical</option>
          <option value="WARNING">Warning</option>
        </select>
        <select className={selectClass} value={kind} onChange={(event) => setKind(event.target.value)}>
          <option value="">All kinds</option>
          {Object.entries(ALERT_KIND_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {error && <ErrorMessage message={error} />}
      {!error && alerts === null && <Loading message="Loading alerts…" />}
      {alerts?.length === 0 && (
        <EmptyState
          title={tab === "active" ? "No active alerts" : "No resolved alerts"}
          message={tab === "active" ? "All quiet. New problems will appear here instantly." : undefined}
        />
      )}

      {alerts && alerts.length > 0 && (
        <div className="grid items-start gap-4 xl:grid-cols-[1fr_24rem]">
          <ul className="flex flex-col divide-y divide-slate-100 overflow-hidden rounded-xl border border-slate-200 bg-white">
            {alerts.map((alert) => (
              <li
                key={alert.id}
                onClick={() => select(alert)}
                className={`flex cursor-pointer flex-wrap items-center gap-3 px-4 py-3 hover:bg-slate-50 ${
                  selected?.id === alert.id ? "bg-sky-50" : ""
                }`}
              >
                <SeverityBadge severity={alert.severity} />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium text-slate-800">{alert.message}</p>
                  <p className="text-xs text-slate-500">
                    {ALERT_KIND_LABELS[alert.kind] ?? alert.kind} · {formatDateTime(alert.created_at)}
                    {alert.acknowledged_by && ` · acknowledged by ${alert.acknowledged_by}`}
                  </p>
                </div>
                <AlertStatusBadge status={alert.status} />
                {hasRole(...CAN.handleAlerts) && alert.status !== "RESOLVED" && (
                  <AlertButtons alert={alert} onChanged={applyChange} compact />
                )}
              </li>
            ))}
          </ul>
          {selected && <AlertDetail alert={selected} onClose={() => select(null)} onChanged={applyChange} />}
        </div>
      )}
    </div>
  );
}

/** Acknowledge / Resolve buttons. */
function AlertButtons({ alert, onChanged, compact = false }: { alert: Alert; onChanged: (alert: Alert) => void; compact?: boolean }) {
  const [error, setError] = useState("");
  const size = compact ? "px-2.5 py-1 text-xs" : "px-3 py-1.5 text-sm";

  async function act(action: "acknowledge" | "resolve", event: React.MouseEvent) {
    event.stopPropagation(); // don't also open the side panel
    setError("");
    try {
      onChanged(await api<Alert>(`/api/alerts/${alert.id}/${action}/`, { method: "POST" }));
    } catch (err) {
      setError(errorText(err));
    }
  }

  return (
    <div className="flex flex-col items-end gap-1">
      <div className="flex gap-2">
        {alert.status === "OPEN" && (
          <button onClick={(event) => act("acknowledge", event)} className={`rounded-lg bg-amber-500 font-medium text-white hover:bg-amber-600 ${size}`}>
            Acknowledge
          </button>
        )}
        <button onClick={(event) => act("resolve", event)} className={`rounded-lg border border-slate-300 bg-white text-slate-700 hover:bg-slate-100 ${size}`}>
          Resolve
        </button>
      </div>
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}

/** The side panel: what the alert is about, and its timeline. */
function AlertDetail({ alert, onClose, onChanged }: { alert: Alert; onClose: () => void; onChanged: (alert: Alert) => void }) {
  const { hasRole } = useAuth();
  const timeline: [string, string | null, string | null][] = [
    ["Raised", alert.created_at, null],
    ["Last seen", alert.last_seen_at, null],
    ["Acknowledged", alert.acknowledged_at, alert.acknowledged_by],
    ["Resolved", alert.resolved_at, alert.resolved_at ? alert.resolved_by ?? "the system (problem cleared)" : null],
  ];

  return (
    <aside className="flex flex-col gap-4 rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex flex-wrap gap-2">
          <SeverityBadge severity={alert.severity} />
          <AlertStatusBadge status={alert.status} />
        </div>
        <button onClick={onClose} className="rounded-md px-2 py-1 text-slate-400 hover:bg-slate-100" aria-label="Close panel">
          ✕
        </button>
      </div>
      <div>
        <p className="text-xs uppercase tracking-wide text-slate-400">{ALERT_KIND_LABELS[alert.kind] ?? alert.kind}</p>
        <p className="mt-1 font-medium text-slate-800">{alert.message}</p>
        {alert.value !== null && <p className="text-sm text-slate-500">Latest value: {alert.value}</p>}
      </div>

      <div className="text-sm text-slate-600">
        {alert.patient_id && (
          <p>
            Patient in bed {alert.bed}:{" "}
            <Link href={`/patients/${alert.patient_id}`} className="text-sky-700 hover:underline">
              open patient record
            </Link>
          </p>
        )}
        {alert.equipment_code && <p>Device: {alert.equipment_code}</p>}
        {alert.unit_code && <p>Unit: {alert.unit_code}</p>}
      </div>

      <ol className="flex flex-col gap-2 border-l-2 border-slate-200 pl-4 text-sm">
        {timeline.map(([label, time, who]) => (
          <li key={label} className={time ? "text-slate-700" : "text-slate-400"}>
            <span className="font-medium">{label}</span>
            {time ? ` · ${formatDateTime(time)}` : " · not yet"}
            {time && who && <span className="text-slate-500"> · by {who}</span>}
          </li>
        ))}
      </ol>

      {hasRole(...CAN.handleAlerts) && alert.status !== "RESOLVED" && <AlertButtons alert={alert} onChanged={onChanged} />}
    </aside>
  );
}

export default function AlertsPage() {
  // useSearchParams() needs a Suspense boundary in the App Router.
  return (
    <Suspense fallback={<Loading message="Loading alerts…" />}>
      <AlertsView />
    </Suspense>
  );
}
