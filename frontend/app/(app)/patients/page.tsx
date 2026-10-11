"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { AdmitButton } from "@/components/PatientActions";
import { EmptyState, ErrorMessage, Loading } from "@/components/States";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/format";
import type { Paginated, Patient, Unit } from "@/lib/types";

const PAGE_SIZE = 25;

const selectClass =
  "rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-100";

export default function PatientsPage() {
  const [typed, setTyped] = useState(""); // what's in the search box right now
  const [search, setSearch] = useState(""); // what we actually search for (after a short pause)
  const [admitted, setAdmitted] = useState("true");
  const [unit, setUnit] = useState("");
  const [page, setPage] = useState(1);
  const [units, setUnits] = useState<Unit[]>([]);
  const [result, setResult] = useState<Paginated<Patient> | null>(null);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0); // bumped after admitting someone, to refresh the list

  useEffect(() => {
    api<Paginated<Unit>>("/api/hospital/units/?page_size=100")
      .then((unitPage) => setUnits(unitPage.results))
      .catch(() => undefined);
  }, []);

  // Wait until typing pauses for 300 ms before searching, instead of one request per key press.
  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(typed.trim());
      setPage(1);
    }, 300);
    return () => clearTimeout(timer);
  }, [typed]);

  useEffect(() => {
    let cancelled = false;
    const params = new URLSearchParams({ page: String(page), page_size: String(PAGE_SIZE), ordering: "last_name" });
    if (search) params.set("search", search);
    if (admitted) params.set("admitted", admitted);
    if (unit) params.set("unit", unit);
    api<Paginated<Patient>>(`/api/hospital/patients/?${params}`)
      .then((data) => {
        if (cancelled) return;
        setResult(data);
        setError("");
      })
      .catch((err: Error) => !cancelled && setError(err.message));
    return () => {
      cancelled = true;
    };
  }, [search, admitted, unit, page, reloadKey]);

  const pages = result ? Math.max(1, Math.ceil(result.count / PAGE_SIZE)) : 1;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-800">Patients</h1>
          <p className="text-slate-500">Search by name or MRN, or narrow the list by unit.</p>
        </div>
        <AdmitButton onDone={() => setReloadKey((key) => key + 1)} />
      </div>

      <div className="flex flex-wrap gap-3">
        <input
          className={`${selectClass} w-72`}
          placeholder="Search name or MRN…"
          value={typed}
          onChange={(event) => setTyped(event.target.value)}
        />
        <select
          className={selectClass}
          value={admitted}
          onChange={(event) => {
            setAdmitted(event.target.value);
            setPage(1);
          }}
        >
          <option value="true">Currently admitted</option>
          <option value="false">Not admitted</option>
          <option value="">All patients</option>
        </select>
        <select
          className={selectClass}
          value={unit}
          onChange={(event) => {
            setUnit(event.target.value);
            setPage(1);
          }}
        >
          <option value="">All units</option>
          {units.map((u) => (
            <option key={u.id} value={u.id}>
              {u.name}
            </option>
          ))}
        </select>
      </div>

      {error && <ErrorMessage message={error} />}
      {!error && result === null && <Loading message="Loading patients…" />}
      {result?.count === 0 && <EmptyState title="No patients found" message="Try a different search or filter." />}
      {result && result.count > 0 && (
        <>
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <table className="w-full text-left text-sm">
              <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="px-4 py-3">Patient</th>
                  <th className="px-4 py-3">MRN</th>
                  <th className="px-4 py-3">Age / sex</th>
                  <th className="px-4 py-3">Bed</th>
                  <th className="px-4 py-3">Admitted</th>
                  <th className="px-4 py-3">Risk</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {result.results.map((patient) => {
                  const stay = patient.current_admission;
                  return (
                    <tr key={patient.id} className="hover:bg-slate-50">
                      <td className="px-4 py-3">
                        <Link href={`/patients/${patient.id}`} className="font-medium text-sky-700 hover:underline">
                          {patient.first_name} {patient.last_name}
                        </Link>
                      </td>
                      <td className="px-4 py-3 font-mono text-xs text-slate-600">{patient.mrn}</td>
                      <td className="px-4 py-3 text-slate-600">
                        {patient.age} / {patient.sex}
                      </td>
                      <td className="px-4 py-3 text-slate-600">{stay?.bed ?? "—"}</td>
                      <td className="px-4 py-3 text-slate-600">{stay ? formatDateTime(stay.admitted_at) : "—"}</td>
                      <td className="px-4 py-3 text-slate-600">{stay?.risk_level ? stay.risk_level.toLowerCase() : "—"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <div className="flex items-center justify-between text-sm text-slate-600">
            <span>
              {result.count} patients · page {page} of {pages}
            </span>
            <div className="flex gap-2">
              <button
                disabled={page <= 1}
                onClick={() => setPage(page - 1)}
                className="rounded-lg border border-slate-300 px-3 py-1.5 hover:bg-slate-100 disabled:opacity-40"
              >
                Previous
              </button>
              <button
                disabled={page >= pages}
                onClick={() => setPage(page + 1)}
                className="rounded-lg border border-slate-300 px-3 py-1.5 hover:bg-slate-100 disabled:opacity-40"
              >
                Next
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
