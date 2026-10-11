"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { EquipmentStatusBadge } from "@/components/Badges";
import { EquipmentForm } from "@/components/forms/EquipmentForm";
import { Modal } from "@/components/Modal";
import { EmptyState, ErrorMessage, Loading } from "@/components/States";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatTime } from "@/lib/format";
import { useLiveEvent } from "@/lib/live";
import { CAN } from "@/lib/permissions";
import {
  EQUIPMENT_KIND_LABELS,
  EQUIPMENT_STATUS_LABELS,
  type Equipment,
  type EquipmentReading,
  type Paginated,
} from "@/lib/types";

const selectClass =
  "rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100";

/** Every device, with its status and latest temperature, updating live. */
export default function EquipmentPage() {
  const { hasRole } = useAuth();
  const [devices, setDevices] = useState<Equipment[] | null>(null);
  const [kind, setKind] = useState("");
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [adding, setAdding] = useState(false);
  const [flash, setFlash] = useState("");

  const load = useCallback(() => {
    const params = new URLSearchParams({ page_size: "500" });
    if (kind) params.set("kind", kind);
    if (status) params.set("status", status);
    api<Paginated<Equipment>>(`/api/equipment/?${params}`)
      .then((page) => {
        setDevices(page.results);
        setError("");
      })
      .catch((err: Error) => setError(err.message));
  }, [kind, status]);

  useEffect(load, [load]);
  useLiveEvent("reload", load);

  // A device changed status: update it, keeping its latest reading (live messages don't carry it).
  useLiveEvent<Equipment>("equipment_update", (changed) => {
    setDevices((current) => {
      if (!current) return current;
      if (status && changed.status !== status) return current.filter((device) => device.id !== changed.id);
      const existing = current.find((device) => device.id === changed.id);
      if (!existing) return kind && changed.kind !== kind ? current : [...current, changed];
      const merged = { ...changed, latest_temperature: existing.latest_temperature, latest_reading_at: existing.latest_reading_at };
      return current.map((device) => (device.id === changed.id ? merged : device));
    });
  });

  // New telemetry: just refresh that device's latest temperature.
  useLiveEvent<EquipmentReading & { equipment: number }>("telemetry", (reading) => {
    setDevices((current) =>
      current &&
      current.map((device) =>
        device.id === reading.equipment
          ? { ...device, latest_temperature: reading.temperature, latest_reading_at: reading.recorded_at }
          : device,
      ),
    );
  });

  useEffect(() => {
    if (!flash) return;
    const timer = setTimeout(() => setFlash(""), 4000);
    return () => clearTimeout(timer);
  }, [flash]);

  const problems = devices?.filter((device) => device.status === "FAULT" || device.status === "WARNING").length ?? 0;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-800">Equipment</h1>
          <p className="text-slate-500">Every monitored device, updating live. Click a device for its readings and maintenance history.</p>
        </div>
        {hasRole(...CAN.manageEquipment) && (
          <button onClick={() => setAdding(true)} className="rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-sky-700">
            Add device
          </button>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <select className={selectClass} value={kind} onChange={(event) => setKind(event.target.value)}>
          <option value="">All kinds</option>
          {Object.entries(EQUIPMENT_KIND_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        <select className={selectClass} value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="">All statuses</option>
          {Object.entries(EQUIPMENT_STATUS_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>
        {devices && (
          <span className="text-sm text-slate-500">
            {devices.length} devices{problems ? ` · ${problems} need attention` : ""}
          </span>
        )}
      </div>

      {flash && <p className="text-sm text-emerald-700">✓ {flash}</p>}
      {error && <ErrorMessage message={error} />}
      {!error && devices === null && <Loading message="Loading equipment…" />}
      {devices?.length === 0 && <EmptyState title="No devices found" message="Try a different filter." />}

      {devices && devices.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Device</th>
                <th className="px-4 py-3">Kind</th>
                <th className="px-4 py-3">Location</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Temperature</th>
                <th className="px-4 py-3">Last serviced</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {devices.map((device) => (
                <tr key={device.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3">
                    <Link href={`/equipment/${device.id}`} className="font-medium text-sky-700 hover:underline">
                      {device.code}
                    </Link>
                    <p className="text-xs text-slate-500">{device.model_name}</p>
                  </td>
                  <td className="px-4 py-3 text-slate-600">{EQUIPMENT_KIND_LABELS[device.kind]}</td>
                  <td className="px-4 py-3 text-slate-600">{device.bed_code ?? device.unit_code ?? "—"}</td>
                  <td className="px-4 py-3">
                    <EquipmentStatusBadge status={device.status} />
                  </td>
                  <td className="px-4 py-3 text-slate-600">
                    {device.latest_temperature !== null ? `${device.latest_temperature} °C` : "—"}
                    {device.latest_reading_at && <span className="ml-1 text-xs text-slate-400">at {formatTime(device.latest_reading_at)}</span>}
                  </td>
                  <td className="px-4 py-3 text-slate-600">{device.last_serviced_at ? formatTime(device.last_serviced_at) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {adding && (
        <Modal title="Add a device" onClose={() => setAdding(false)}>
          <EquipmentForm
            onDone={(device) => {
              setAdding(false);
              setFlash(`${device.code} added.`);
              load();
            }}
            onCancel={() => setAdding(false)}
          />
        </Modal>
      )}
    </div>
  );
}
