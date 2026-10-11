"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { EquipmentStatusBadge, SeverityBadge } from "@/components/Badges";
import { EquipmentForm } from "@/components/forms/EquipmentForm";
import { errorText, Field, FormFooter, inputClass } from "@/components/forms/fields";
import { MetricCharts, type Metric } from "@/components/MetricCharts";
import { Modal } from "@/components/Modal";
import { ErrorMessage, Loading } from "@/components/States";
import { api, ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatDate, formatDateTime } from "@/lib/format";
import { useLiveEvent } from "@/lib/live";
import { CAN } from "@/lib/permissions";
import {
  EQUIPMENT_KIND_LABELS,
  type Alert,
  type EquipmentDetail,
  type EquipmentReading,
  type MaintenanceLog,
  type Paginated,
} from "@/lib/types";

const TELEMETRY: Metric<EquipmentReading>[] = [
  { key: "temperature", label: "Internal temperature", unit: "°C", color: "#ef4444" },
  { key: "error_count", label: "Errors per reading", unit: "", color: "#7c3aed" },
  { key: "pressure", label: "Airway pressure", unit: "cmH₂O", color: "#0284c7" },
];

const HISTORY = 300; // about two days of readings (one every 10 hospital minutes)

type Dialog = "start" | "finish" | "edit" | null;

/** One device: its live telemetry, maintenance history, active alerts, and (for admins) maintenance and editing. */
export default function EquipmentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const deviceId = Number(id);
  const { hasRole } = useAuth();
  const [device, setDevice] = useState<EquipmentDetail | null>(null);
  const [readings, setReadings] = useState<EquipmentReading[] | null>(null);
  const [logs, setLogs] = useState<MaintenanceLog[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [error, setError] = useState("");
  const [dialog, setDialog] = useState<Dialog>(null);

  const loadDevice = useCallback(() => {
    api<EquipmentDetail>(`/api/equipment/${deviceId}/`)
      .then(setDevice)
      .catch((err) => setError(err instanceof ApiError && err.status === 404 ? "This device doesn't exist." : err.message));
    api<Paginated<MaintenanceLog>>(`/api/equipment/${deviceId}/maintenance-logs/?page_size=20`)
      .then((page) => setLogs(page.results))
      .catch(() => undefined);
    api<Paginated<Alert>>(`/api/alerts/?equipment=${deviceId}&active=true`)
      .then((page) => setAlerts(page.results))
      .catch(() => undefined);
  }, [deviceId]);

  useEffect(loadDevice, [loadDevice]);

  useEffect(() => {
    api<Paginated<EquipmentReading>>(`/api/equipment/${deviceId}/readings/?page_size=${HISTORY}`)
      .then((page) => setReadings([...page.results].reverse())) // the API sends newest first
      .catch(() => setReadings([]));
  }, [deviceId]);

  useLiveEvent<EquipmentReading & { equipment: number }>("telemetry", (reading) => {
    if (reading.equipment !== deviceId) return;
    setReadings((current) => current && [...current, reading].slice(-HISTORY));
  });
  useLiveEvent<{ id: number }>("equipment_update", (changed) => changed.id === deviceId && loadDevice());
  useLiveEvent<Alert>("alert_update", (alert) => alert.equipment === deviceId && loadDevice());

  if (error) return <ErrorMessage message={error} />;
  if (!device) return <Loading message="Loading device…" />;

  const isAdmin = hasRole(...CAN.manageEquipment);
  const close = () => setDialog(null);
  const finished = () => {
    setDialog(null);
    loadDevice();
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Link href="/equipment" className="text-sm text-sky-700 hover:underline">
            ← All equipment
          </Link>
          <h1 className="mt-1 flex items-center gap-3 text-2xl font-semibold text-slate-800">
            {device.code} <EquipmentStatusBadge status={device.status} />
          </h1>
          <p className="text-slate-500">
            {EQUIPMENT_KIND_LABELS[device.kind]}
            {device.model_name && ` · ${device.model_name}`}
            {` · ${device.bed_code ?? device.unit_code ?? "not assigned"}`}
          </p>
        </div>
        {isAdmin && (
          <div className="flex gap-2">
            {device.status === "MAINTENANCE" ? (
              <button onClick={() => setDialog("finish")} className="rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-emerald-700">
                Finish maintenance
              </button>
            ) : (
              <button onClick={() => setDialog("start")} className="rounded-lg bg-amber-500 px-3 py-1.5 text-sm font-medium text-white hover:bg-amber-600">
                Start maintenance
              </button>
            )}
            <button onClick={() => setDialog("edit")} className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100">
              Edit
            </button>
          </div>
        )}
      </div>

      {alerts.length > 0 && (
        <section className="rounded-xl border border-red-200 bg-red-50 p-4">
          <h2 className="mb-2 text-sm font-semibold text-red-800">Active alerts</h2>
          <ul className="flex flex-col gap-1.5">
            {alerts.map((alert) => (
              <li key={alert.id} className="flex items-center gap-2 text-sm text-slate-700">
                <SeverityBadge severity={alert.severity} />
                <Link href={`/alerts?alert=${alert.id}`} className="hover:underline">
                  {alert.message}
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}

      {device.open_maintenance && (
        <p className="rounded-lg bg-slate-100 px-4 py-3 text-sm text-slate-700">
          In maintenance since {formatDateTime(device.open_maintenance.started_at)}: {device.open_maintenance.reason}
          {device.open_maintenance.started_by && ` (started by ${device.open_maintenance.started_by})`}. No readings are sent while in maintenance.
        </p>
      )}

      <div className="grid items-start gap-6 xl:grid-cols-[24rem_1fr]">
        <section className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-3 text-lg font-semibold text-slate-800">Live readings</h2>
          {readings === null ? <Loading message="Loading readings…" /> : <MetricCharts readings={readings} metrics={TELEMETRY} empty="No readings yet." />}
        </section>

        <div className="flex flex-col gap-6">
          <section className="rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="mb-3 text-lg font-semibold text-slate-800">Details</h2>
            <dl className="grid grid-cols-[10rem_1fr] gap-y-2 text-sm">
              <dt className="text-slate-500">Installed</dt>
              <dd className="text-slate-800">{formatDate(device.installed_on)}</dd>
              <dt className="text-slate-500">Last serviced</dt>
              <dd className="text-slate-800">{formatDateTime(device.last_serviced_at)}</dd>
              <dt className="text-slate-500">Running hours</dt>
              <dd className="text-slate-800">{device.latest_reading ? Math.round(device.latest_reading.running_hours).toLocaleString() : "—"}</dd>
              <dt className="text-slate-500">Anomaly score</dt>
              <dd className="text-slate-800">{device.anomaly_score ?? "not scored yet (arrives on Day 29)"}</dd>
            </dl>
          </section>

          <section className="rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="mb-3 text-lg font-semibold text-slate-800">Maintenance history</h2>
            {logs.length === 0 ? (
              <p className="text-sm text-slate-500">No maintenance recorded.</p>
            ) : (
              <ul className="flex flex-col divide-y divide-slate-100 text-sm">
                {logs.map((log) => (
                  <li key={log.id} className="py-2">
                    <p className="font-medium text-slate-800">{log.reason}</p>
                    <p className="text-slate-500">
                      {formatDateTime(log.started_at)} → {log.finished_at ? formatDateTime(log.finished_at) : "in progress"}
                      {log.started_by && ` · by ${log.started_by}`}
                    </p>
                    {log.notes && <p className="text-slate-600">{log.notes}</p>}
                  </li>
                ))}
              </ul>
            )}
          </section>
        </div>
      </div>

      {dialog === "start" && (
        <Modal title={`Start maintenance · ${device.code}`} onClose={close}>
          <MaintenanceForm action="start" deviceId={device.id} onDone={finished} onCancel={close} />
        </Modal>
      )}
      {dialog === "finish" && (
        <Modal title={`Finish maintenance · ${device.code}`} onClose={close}>
          <MaintenanceForm action="finish" deviceId={device.id} onDone={finished} onCancel={close} />
        </Modal>
      )}
      {dialog === "edit" && (
        <Modal title={`Edit · ${device.code}`} onClose={close}>
          <EquipmentForm device={device} onDone={finished} onCancel={close} />
        </Modal>
      )}
    </div>
  );
}

/** Start maintenance (with a reason) or finish it (with optional notes). */
function MaintenanceForm({
  action,
  deviceId,
  onDone,
  onCancel,
}: {
  action: "start" | "finish";
  deviceId: number;
  onDone: () => void;
  onCancel: () => void;
}) {
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await api(`/api/equipment/${deviceId}/${action}-maintenance/`, {
        method: "POST",
        body: JSON.stringify(action === "start" ? { reason: text } : { notes: text }),
      });
      onDone();
    } catch (err) {
      setError(errorText(err));
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4">
      <p className="text-sm text-slate-600">
        {action === "start"
          ? "The device stops sending readings until maintenance is finished."
          : "The device goes back to OK, any alerts about it close, and its readings resume."}
      </p>
      <Field label={action === "start" ? "Reason" : "Notes"} hint={action === "finish" ? "optional" : undefined}>
        <input
          className={inputClass}
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder={action === "start" ? "e.g. Temperature rising" : "e.g. Fan replaced"}
          required={action === "start"}
          autoFocus
        />
      </Field>
      <FormFooter error={error} busy={busy} submitLabel={action === "start" ? "Start maintenance" : "Finish maintenance"} onCancel={onCancel} />
    </form>
  );
}
