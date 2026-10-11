"use client";

import Link from "next/link";

import { formatDateTime, formatTime } from "@/lib/format";
import type { Bed } from "@/lib/types";
import { useVitals } from "@/lib/useVitals";

import { bedLook } from "./FloorMap";
import { AdmissionActions, EmptyBedActions } from "./PatientActions";
import { ErrorMessage, Loading } from "./States";
import { VitalsChart } from "./VitalsChart";

/** The panel that opens when you click a bed on the map. */
export function BedPanel({ bed, onClose }: { bed: Bed; onClose: () => void }) {
  const admission = bed.current_admission;
  const { readings, error } = useVitals(admission?.id ?? null);
  const look = bedLook(bed);

  return (
    <aside className="flex flex-col gap-4 rounded-xl border border-slate-200 bg-white p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-wide text-slate-400">{bed.unit_code}</p>
          <h2 className="text-xl font-semibold text-slate-800">Bed {bed.code}</h2>
        </div>
        <button onClick={onClose} className="rounded-md px-2 py-1 text-slate-400 hover:bg-slate-100" aria-label="Close panel">
          ✕
        </button>
      </div>

      <span
        className="self-start rounded-full border px-2.5 py-0.5 text-xs font-medium"
        style={{ background: look.fill, borderColor: look.stroke, color: look.text === "#ffffff" ? look.stroke : look.text }}
      >
        {look.label}
        {!admission && bed.status_since && ` since ${formatTime(bed.status_since)}`}
      </span>

      {admission ? (
        <>
          <div>
            <Link href={`/patients/${admission.patient_id}`} className="text-lg font-medium text-sky-700 hover:underline">
              {admission.patient_name}
            </Link>
            <p className="text-sm text-slate-500">Admitted {formatDateTime(admission.admitted_at)}</p>
            <p className="text-sm text-slate-500">
              Risk: {admission.risk_level ? admission.risk_level.toLowerCase() : "not scored yet (arrives on Day 30)"}
            </p>
          </div>
          <AdmissionActions admissionId={admission.id} bedCode={bed.code} patientName={admission.patient_name} />
          <div>
            <h3 className="mb-2 text-sm font-semibold text-slate-700">Vital signs</h3>
            {error && <ErrorMessage message={error} />}
            {!error && readings === null && <Loading message="Loading vital signs…" />}
            {readings && <VitalsChart readings={readings} />}
          </div>
        </>
      ) : (
        <>
          <p className="text-sm text-slate-500">
            {bed.is_active ? "No patient in this bed." : "This bed is closed."}
          </p>
          <EmptyBedActions bed={bed} />
        </>
      )}
    </aside>
  );
}
