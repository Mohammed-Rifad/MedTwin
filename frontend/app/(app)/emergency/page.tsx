"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { TriageBadge } from "@/components/Badges";
import { ArrivalForm } from "@/components/forms/ArrivalForm";
import { EmergencyAdmitForm } from "@/components/forms/EmergencyAdmitForm";
import { errorText } from "@/components/forms/fields";
import { Modal } from "@/components/Modal";
import { EmptyState, ErrorMessage, Loading } from "@/components/States";
import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatHours, formatTime } from "@/lib/format";
import { useHospitalClock, useLiveEvent } from "@/lib/live";
import { CAN } from "@/lib/permissions";
import type { EmergencyArrival, Paginated } from "@/lib/types";

// How long each triage level should wait at most before being seen (common emergency-department targets).
const TARGET_MINUTES: Record<number, number> = { 1: 0, 2: 10, 3: 30, 4: 60, 5: 120 };

function byUrgency(a: EmergencyArrival, b: EmergencyArrival) {
  return a.triage_level - b.triage_level || a.arrived_at.localeCompare(b.arrived_at);
}

type Dialog = { kind: "log" } | { kind: "admit" | "send-home"; arrival: EmergencyArrival } | null;

/** The emergency department queue: who is waiting, most urgent first, with live waiting times. */
export default function EmergencyPage() {
  const { hasRole } = useAuth();
  const clock = useHospitalClock();
  const [queue, setQueue] = useState<EmergencyArrival[] | null>(null);
  const [error, setError] = useState("");
  const [dialog, setDialog] = useState<Dialog>(null);
  const [flash, setFlash] = useState("");

  const load = useCallback(() => {
    api<Paginated<EmergencyArrival>>("/api/hospital/emergency/?status=WAITING&page_size=500")
      .then((page) => {
        setQueue(page.results);
        setError("");
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(load, [load]);
  useLiveEvent("reload", load);

  // Someone arrived, was admitted, or left: keep the queue in step without reloading.
  useLiveEvent<EmergencyArrival>("emergency_update", (arrival) => {
    setQueue((current) => {
      if (!current) return current;
      const others = current.filter((item) => item.id !== arrival.id);
      return arrival.status === "WAITING" ? [...others, arrival].sort(byUrgency) : others;
    });
  });

  useEffect(() => {
    if (!flash) return;
    const timer = setTimeout(() => setFlash(""), 4000);
    return () => clearTimeout(timer);
  }, [flash]);

  // Waiting time uses hospital time while the simulator runs, otherwise the server's figure.
  function waitingMinutes(arrival: EmergencyArrival): number {
    if (clock) return Math.max(0, (Date.parse(clock.hospital_time) - Date.parse(arrival.arrived_at)) / 60_000);
    return arrival.waiting_minutes ?? 0;
  }

  function done(message: string) {
    setDialog(null);
    setFlash(message);
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-800">Emergency department</h1>
          <p className="text-slate-500">Patients waiting to be treated, most urgent first. Updates live.</p>
        </div>
        {hasRole(...CAN.logArrival) && (
          <button className="rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-sky-700" onClick={() => setDialog({ kind: "log" })}>
            Log arrival
          </button>
        )}
      </div>

      {flash && <p className="text-sm text-emerald-700">✓ {flash}</p>}
      {error && <ErrorMessage message={error} />}
      {!error && queue === null && <Loading message="Loading the queue…" />}

      {queue && (
        <div className="flex flex-wrap gap-2 text-sm text-slate-600">
          <span className="font-medium text-slate-800">{queue.length} waiting</span>
          {[1, 2, 3, 4, 5].map((level) => {
            const count = queue.filter((arrival) => arrival.triage_level === level).length;
            return count ? (
              <span key={level} className="flex items-center gap-1">
                · <TriageBadge level={level} /> × {count}
              </span>
            ) : null;
          })}
        </div>
      )}

      {queue?.length === 0 && (
        <EmptyState
          title="Nobody is waiting"
          message="The simulator moves patients into ED bays quickly. To see a queue, trigger a surge from the simulator controls."
        />
      )}

      {queue && queue.length > 0 && (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="w-full text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
              <tr>
                <th className="px-4 py-3">Triage</th>
                <th className="px-4 py-3">Patient</th>
                <th className="px-4 py-3">Complaint</th>
                <th className="px-4 py-3">Arrived</th>
                <th className="px-4 py-3">Waiting</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {queue.map((arrival) => {
                const minutes = waitingMinutes(arrival);
                const overdue = minutes > TARGET_MINUTES[arrival.triage_level];
                return (
                  <tr key={arrival.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <TriageBadge level={arrival.triage_level} />
                    </td>
                    <td className="px-4 py-3">
                      <Link href={`/patients/${arrival.patient}`} className="font-medium text-sky-700 hover:underline">
                        {arrival.patient_name}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{arrival.complaint}</td>
                    <td className="px-4 py-3 text-slate-600">{formatTime(arrival.arrived_at)}</td>
                    <td className={`px-4 py-3 font-medium ${overdue ? "text-red-600" : "text-slate-700"}`}>
                      {formatHours(minutes / 60)}
                      {overdue && <span className="ml-1 text-xs font-normal">over target</span>}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-2">
                        {hasRole(...CAN.admitFromEmergency) && (
                          <button
                            className="rounded-lg bg-sky-600 px-3 py-1 text-xs font-medium text-white hover:bg-sky-700"
                            onClick={() => setDialog({ kind: "admit", arrival })}
                          >
                            Admit
                          </button>
                        )}
                        {hasRole(...CAN.dischargeFromEmergency) && (
                          <button
                            className="rounded-lg border border-slate-300 px-3 py-1 text-xs text-slate-700 hover:bg-slate-100"
                            onClick={() => setDialog({ kind: "send-home", arrival })}
                          >
                            Send home
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {dialog?.kind === "log" && (
        <Modal title="Log an emergency arrival" onClose={() => setDialog(null)}>
          <ArrivalForm onDone={(arrival) => done(`${arrival.patient_name} added to the queue.`)} onCancel={() => setDialog(null)} />
        </Modal>
      )}
      {dialog?.kind === "admit" && (
        <Modal title={`Admit · ${dialog.arrival.patient_name}`} onClose={() => setDialog(null)}>
          <EmergencyAdmitForm
            arrival={dialog.arrival}
            onDone={(admission) => done(`${admission.patient_name} admitted to ${admission.bed_code}.`)}
            onCancel={() => setDialog(null)}
          />
        </Modal>
      )}
      {dialog?.kind === "send-home" && (
        <Modal title={`Send home · ${dialog.arrival.patient_name}`} onClose={() => setDialog(null)}>
          <SendHome arrival={dialog.arrival} onDone={() => done(`${dialog.arrival.patient_name} sent home from the ED.`)} onCancel={() => setDialog(null)} />
        </Modal>
      )}
    </div>
  );
}

/** Treated in the ED and going home, without needing a bed. */
function SendHome({ arrival, onDone, onCancel }: { arrival: EmergencyArrival; onDone: () => void; onCancel: () => void }) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function confirm() {
    setBusy(true);
    setError("");
    try {
      await api(`/api/hospital/emergency/${arrival.id}/discharge/`, { method: "POST" });
      onDone();
    } catch (err) {
      setError(errorText(err));
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-col gap-4">
      <p className="text-sm text-slate-600">
        {arrival.patient_name} was treated in the emergency department and doesn&apos;t need a bed. They will leave the queue.
      </p>
      {error && <ErrorMessage message={error} />}
      <div className="flex justify-end gap-2">
        <button onClick={onCancel} className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 hover:bg-slate-100">
          Cancel
        </button>
        <button onClick={confirm} disabled={busy} className="rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700 disabled:opacity-60">
          {busy ? "Saving…" : "Send home"}
        </button>
      </div>
    </div>
  );
}
