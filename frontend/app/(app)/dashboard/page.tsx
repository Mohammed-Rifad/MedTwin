"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { ErrorMessage, Loading } from "@/components/States";
import { api } from "@/lib/api";
import { useLiveEvent } from "@/lib/live";
import { ALERT_KIND_LABELS, EQUIPMENT_STATUS_LABELS, type EquipmentStatus, type HospitalSummary } from "@/lib/types";

const REFRESH_AT_MOST_EVERY_MS = 2_000;

/** One headline number, with a line of context underneath. Click to open the related page. */
function Kpi({ label, value, detail, href, tone = "normal" }: { label: string; value: string | number; detail: string; href: string; tone?: "normal" | "warn" | "bad" }) {
  const color = tone === "bad" ? "text-red-600" : tone === "warn" ? "text-amber-600" : "text-slate-800";
  return (
    <Link href={href} className="rounded-xl border border-slate-200 bg-white p-5 hover:border-sky-300">
      <p className="text-sm text-slate-500">{label}</p>
      <p className={`mt-1 text-3xl font-semibold ${color}`}>{value}</p>
      <p className="mt-1 text-xs text-slate-500">{detail}</p>
    </Link>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5">
      <h2 className="mb-3 font-semibold text-slate-800">{title}</h2>
      {children}
    </section>
  );
}

function ComingLater({ what, day }: { what: string; day: number }) {
  return (
    <div className="flex h-48 items-center justify-center rounded-lg border border-dashed border-slate-300 text-center text-sm text-slate-500">
      {what}
      <br />
      arrives on Day {day}, when the ML models are connected.
    </div>
  );
}

/** The hospital at a glance: key numbers and charts, kept up to date live. */
export default function DashboardPage() {
  const [summary, setSummary] = useState<HospitalSummary | null>(null);
  const [error, setError] = useState("");
  const pending = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(() => {
    api<HospitalSummary>("/api/twin/summary/")
      .then((data) => {
        setSummary(data);
        setError("");
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(load, [load]);

  // Many changes can arrive in a burst (e.g. a surge). Refresh once after a short pause, not for every message.
  const refreshSoon = useCallback(() => {
    if (pending.current) return;
    pending.current = setTimeout(() => {
      pending.current = null;
      load();
    }, REFRESH_AT_MOST_EVERY_MS);
  }, [load]);

  useEffect(() => () => {
    if (pending.current) clearTimeout(pending.current);
  }, []);

  useLiveEvent("bed_update", refreshSoon);
  useLiveEvent("emergency_update", refreshSoon);
  useLiveEvent("alert_update", refreshSoon);
  useLiveEvent("equipment_update", refreshSoon);
  useLiveEvent("reload", load);

  if (error) return <ErrorMessage message={error} />;
  if (!summary) return <Loading message="Loading the dashboard…" />;

  const { icu, beds, emergency, alerts, equipment, today } = summary;
  const critical = alerts.by_severity.CRITICAL ?? 0;
  const urgentWaiting = (emergency.by_triage["1"] ?? 0) + (emergency.by_triage["2"] ?? 0);
  const faults = equipment.by_status.FAULT ?? 0;
  const inMaintenance = equipment.by_status.MAINTENANCE ?? 0;

  const unitChart = summary.units.map((unit) => ({
    name: unit.name,
    Occupied: unit.occupied,
    Cleaning: unit.cleaning,
    Free: unit.capacity - unit.occupied - unit.cleaning,
  }));
  const alertChart = Object.entries(alerts.by_kind)
    .map(([kind, count]) => ({ name: ALERT_KIND_LABELS[kind] ?? kind, Alerts: count }))
    .sort((a, b) => b.Alerts - a.Alerts);
  const statuses: EquipmentStatus[] = ["OK", "WARNING", "MAINTENANCE", "FAULT"];

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-800">Dashboard</h1>
        <p className="text-slate-500">The hospital at a glance. Updates live. Click a number to see the details.</p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <Kpi
          label="ICU occupancy"
          value={`${icu.percent}%`}
          detail={`${icu.occupied} of ${icu.capacity} beds`}
          href="/"
          tone={icu.percent >= 100 ? "bad" : icu.percent >= 85 ? "warn" : "normal"}
        />
        <Kpi label="Free beds" value={beds.free} detail={`${beds.cleaning} being cleaned · ${beds.occupied} occupied`} href="/" tone={beds.free === 0 ? "bad" : "normal"} />
        <Kpi
          label="Waiting in the ED"
          value={emergency.waiting}
          detail={urgentWaiting ? `${urgentWaiting} urgent (triage 1–2)` : "none urgent"}
          href="/emergency"
          tone={urgentWaiting ? "bad" : emergency.waiting ? "warn" : "normal"}
        />
        <Kpi
          label="Open alerts"
          value={alerts.open}
          detail={`${critical} critical · ${alerts.acknowledged} being handled`}
          href="/alerts"
          tone={critical ? "bad" : alerts.open ? "warn" : "normal"}
        />
        <Kpi label="Devices in fault" value={faults} detail={`${inMaintenance} in maintenance · ${equipment.total} in total`} href="/equipment" tone={faults ? "bad" : "normal"} />
      </div>

      <p className="text-sm text-slate-500">
        Today so far: <span className="font-medium text-slate-700">{today.admissions}</span> admissions,{" "}
        <span className="font-medium text-slate-700">{today.discharges}</span> discharges.
      </p>

      <div className="grid gap-4 xl:grid-cols-2">
        <Card title="Beds by unit">
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={unitChart} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" allowDecimals={false} />
                <YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="Occupied" stackId="beds" fill="#10b981" isAnimationActive={false} />
                <Bar dataKey="Cleaning" stackId="beds" fill="#7dd3fc" isAnimationActive={false} />
                <Bar dataKey="Free" stackId="beds" fill="#e2e8f0" isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Active alerts by kind">
          {alertChart.length === 0 ? (
            <p className="py-20 text-center text-sm text-slate-500">No active alerts. All quiet.</p>
          ) : (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={alertChart} layout="vertical" margin={{ left: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" allowDecimals={false} />
                  <YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="Alerts" fill="#f59e0b" isAnimationActive={false} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </Card>

        <Card title="ICU forecast (next 72 hours)">
          <ComingLater what="The ICU occupancy forecast" day={30} />
        </Card>

        <Card title="Patient risk">
          <ComingLater what="The risk distribution of admitted patients" day={30} />
        </Card>

        <Card title="Equipment">
          <ul className="grid grid-cols-2 gap-3 sm:grid-cols-4">
            {statuses.map((status) => (
              <li key={status} className="rounded-lg bg-slate-50 p-3 text-center">
                <p className="text-2xl font-semibold text-slate-800">{equipment.by_status[status] ?? 0}</p>
                <p className="text-xs text-slate-500">{EQUIPMENT_STATUS_LABELS[status]}</p>
              </li>
            ))}
          </ul>
        </Card>
      </div>
    </div>
  );
}
