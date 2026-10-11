"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { AdmissionActions, AdmitButton } from "@/components/PatientActions";
import { ErrorMessage, Loading } from "@/components/States";
import { VitalsChart } from "@/components/VitalsChart";
import { api, ApiError } from "@/lib/api";
import { formatDate, formatDateTime, formatHours } from "@/lib/format";
import { OUTCOME_LABELS, SEX_LABELS, type Bed, type Paginated, type PatientDetail } from "@/lib/types";
import { useVitals } from "@/lib/useVitals";

/** One patient's record: details, current stay with live vital signs, and earlier stays. */
export default function PatientPage() {
  const { id } = useParams<{ id: string }>();
  const [patient, setPatient] = useState<PatientDetail | null>(null);
  const [mapBedId, setMapBedId] = useState<number | null>(null);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0); // bumped after an action (admit, transfer, discharge…)
  const reload = () => setReloadKey((key) => key + 1);

  useEffect(() => {
    let cancelled = false;
    api<PatientDetail>(`/api/hospital/patients/${id}/`)
      .then((data) => !cancelled && setPatient(data))
      .catch((err) => {
        if (cancelled) return;
        setError(err instanceof ApiError && err.status === 404 ? "This patient doesn't exist." : err.message);
      });
    return () => {
      cancelled = true;
    };
  }, [id, reloadKey]);

  const current = patient?.admissions.find((admission) => admission.discharged_at === null) ?? null;
  const { readings, error: vitalsError } = useVitals(current?.id ?? null);

  // Find the current bed's id, so "Show on map" can open the map with this bed selected.
  useEffect(() => {
    if (!current) return;
    api<Paginated<Bed>>(`/api/hospital/beds/?search=${encodeURIComponent(current.bed_code)}`)
      .then((page) => setMapBedId(page.results.find((bed) => bed.code === current.bed_code)?.id ?? null))
      .catch(() => undefined);
  }, [current]);

  if (error) return <ErrorMessage message={error} />;
  if (!patient) return <Loading message="Loading patient…" />;

  const earlier = patient.admissions.filter((admission) => admission.discharged_at !== null);

  return (
    <div className="flex flex-col gap-6">
      <div>
        <Link href="/patients" className="text-sm text-sky-700 hover:underline">
          ← All patients
        </Link>
        <h1 className="mt-1 text-2xl font-semibold text-slate-800">
          {patient.first_name} {patient.last_name}
        </h1>
        <p className="text-slate-500">
          {patient.mrn} · {patient.age} years · {SEX_LABELS[patient.sex]} · born {formatDate(patient.date_of_birth)}
        </p>
      </div>

      <div className="grid items-start gap-6 xl:grid-cols-[1fr_24rem]">
        <section className="rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="mb-3 text-lg font-semibold text-slate-800">Current stay</h2>
          {current ? (
            <>
              <dl className="grid grid-cols-[10rem_1fr] gap-y-2 text-sm">
                <dt className="text-slate-500">Bed</dt>
                <dd className="text-slate-800">
                  {current.bed_code} ({current.unit})
                  {mapBedId && (
                    <Link href={`/?bed=${mapBedId}`} className="ml-3 text-sky-700 hover:underline">
                      Show on map
                    </Link>
                  )}
                </dd>
                <dt className="text-slate-500">Reason</dt>
                <dd className="text-slate-800">{current.reason || "—"}</dd>
                <dt className="text-slate-500">Admitted</dt>
                <dd className="text-slate-800">{formatDateTime(current.admitted_at)}</dd>
                <dt className="text-slate-500">Length of stay</dt>
                <dd className="text-slate-800">{formatHours(current.length_of_stay_hours)}</dd>
                <dt className="text-slate-500">Expected discharge</dt>
                <dd className="text-slate-800">{formatDateTime(current.expected_discharge_at)}</dd>
                <dt className="text-slate-500">Risk</dt>
                <dd className="text-slate-800">
                  {current.risk_level ? current.risk_level.toLowerCase() : "not scored yet (arrives on Day 30)"}
                </dd>
              </dl>
              <div className="mt-4">
                <AdmissionActions
                  admissionId={current.id}
                  bedCode={current.bed_code}
                  patientName={`${patient.first_name} ${patient.last_name}`}
                  onChanged={reload}
                />
              </div>
            </>
          ) : (
            <div className="flex flex-col gap-3">
              <p className="text-sm text-slate-500">Not currently admitted.</p>
              <AdmitButton
                patient={{ id: patient.id, name: `${patient.first_name} ${patient.last_name}` }}
                label="Admit"
                onDone={reload}
              />
            </div>
          )}
        </section>

        {current && (
          <section className="rounded-xl border border-slate-200 bg-white p-5">
            <h2 className="mb-3 text-lg font-semibold text-slate-800">Vital signs</h2>
            {vitalsError && <ErrorMessage message={vitalsError} />}
            {!vitalsError && readings === null && <Loading message="Loading vital signs…" />}
            {readings && <VitalsChart readings={readings} />}
          </section>
        )}
      </div>

      <section className="rounded-xl border border-slate-200 bg-white p-5">
        <h2 className="mb-3 text-lg font-semibold text-slate-800">Earlier stays</h2>
        {earlier.length === 0 ? (
          <p className="text-sm text-slate-500">No earlier stays.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="py-2 pr-4">Admitted</th>
                  <th className="py-2 pr-4">Discharged</th>
                  <th className="py-2 pr-4">Last bed</th>
                  <th className="py-2 pr-4">Length</th>
                  <th className="py-2 pr-4">Reason</th>
                  <th className="py-2">Outcome</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {earlier.map((stay) => (
                  <tr key={stay.id}>
                    <td className="py-2 pr-4">{formatDateTime(stay.admitted_at)}</td>
                    <td className="py-2 pr-4">{formatDateTime(stay.discharged_at)}</td>
                    <td className="py-2 pr-4">{stay.bed_code}</td>
                    <td className="py-2 pr-4">{formatHours(stay.length_of_stay_hours)}</td>
                    <td className="py-2 pr-4">{stay.reason || "—"}</td>
                    <td className="py-2">{OUTCOME_LABELS[stay.outcome]}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
