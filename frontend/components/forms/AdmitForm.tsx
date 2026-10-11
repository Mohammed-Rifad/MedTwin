"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { Admission, Paginated, Patient } from "@/lib/types";

import { BedSelect } from "./BedSelect";
import { errorText, Field, FormFooter, inputClass } from "./fields";

type Props = {
  presetBed?: { id: number; code: string }; // opened from a free bed on the map
  presetPatient?: { id: number; name: string }; // opened from a patient's page
  onDone: (admission: Admission) => void;
  onCancel: () => void;
};

const today = new Date().toISOString().slice(0, 10);

/** Register a new patient (or pick an existing one) and admit them to a free bed. */
export function AdmitForm({ presetBed, presetPatient, onDone, onCancel }: Props) {
  const [mode, setMode] = useState<"new" | "existing">(presetPatient ? "existing" : "new");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [birthDate, setBirthDate] = useState("");
  const [sex, setSex] = useState("F");
  const [patientId, setPatientId] = useState(presetPatient ? String(presetPatient.id) : "");
  const [search, setSearch] = useState("");
  const [matches, setMatches] = useState<Patient[]>([]);
  const [bedId, setBedId] = useState(presetBed ? String(presetBed.id) : "");
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  // Searching for an existing patient who isn't admitted at the moment.
  useEffect(() => {
    if (mode !== "existing" || presetPatient || search.trim().length < 2) return;
    const timer = setTimeout(() => {
      api<Paginated<Patient>>(`/api/hospital/patients/?admitted=false&page_size=10&search=${encodeURIComponent(search.trim())}`)
        .then((page) => setMatches(page.results))
        .catch(() => setMatches([]));
    }, 300);
    return () => clearTimeout(timer);
  }, [mode, search, presetPatient]);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      let id = Number(patientId);
      if (mode === "new") {
        const patient = await api<Patient>("/api/hospital/patients/", {
          method: "POST",
          body: JSON.stringify({ first_name: firstName, last_name: lastName, date_of_birth: birthDate, sex }),
        });
        id = patient.id;
        setMode("existing"); // if admitting fails below, don't register the same person twice on retry
        setPatientId(String(id));
        setMatches([patient]);
      }
      const admission = await api<Admission>("/api/hospital/admissions/", {
        method: "POST",
        body: JSON.stringify({ patient: id, bed: Number(bedId), reason }),
      });
      onDone(admission);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4">
      {presetPatient ? (
        <p className="text-sm text-slate-600">
          Patient: <span className="font-medium text-slate-800">{presetPatient.name}</span>
        </p>
      ) : (
        <div className="flex gap-1 rounded-lg bg-slate-100 p-1 text-sm">
          {(["new", "existing"] as const).map((option) => (
            <button
              key={option}
              type="button"
              onClick={() => setMode(option)}
              className={`flex-1 rounded-md px-3 py-1.5 ${mode === option ? "bg-white font-medium shadow-sm" : "text-slate-600"}`}
            >
              {option === "new" ? "New patient" : "Existing patient"}
            </button>
          ))}
        </div>
      )}

      {mode === "new" && (
        <div className="grid grid-cols-2 gap-3">
          <Field label="First name">
            <input className={inputClass} value={firstName} onChange={(e) => setFirstName(e.target.value)} required autoFocus />
          </Field>
          <Field label="Last name">
            <input className={inputClass} value={lastName} onChange={(e) => setLastName(e.target.value)} required />
          </Field>
          <Field label="Date of birth">
            <input type="date" max={today} className={inputClass} value={birthDate} onChange={(e) => setBirthDate(e.target.value)} required />
          </Field>
          <Field label="Sex">
            <select className={inputClass} value={sex} onChange={(e) => setSex(e.target.value)}>
              <option value="F">Female</option>
              <option value="M">Male</option>
              <option value="O">Other</option>
            </select>
          </Field>
        </div>
      )}

      {mode === "existing" && !presetPatient && (
        <Field label="Find patient" hint="name or MRN, not currently admitted">
          <input className={inputClass} value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Type at least 2 letters…" autoFocus />
          {matches.length > 0 && (
            <select className={`${inputClass} mt-2`} value={patientId} onChange={(e) => setPatientId(e.target.value)} required>
              <option value="">Choose a patient…</option>
              {matches.map((patient) => (
                <option key={patient.id} value={patient.id}>
                  {patient.first_name} {patient.last_name} · {patient.mrn} · {patient.age} y
                </option>
              ))}
            </select>
          )}
        </Field>
      )}

      <Field label="Bed">
        {presetBed ? (
          <p className="text-sm font-normal text-slate-800">{presetBed.code}</p>
        ) : (
          <BedSelect value={bedId} onChange={setBedId} />
        )}
      </Field>

      <Field label="Reason for admission">
        <input className={inputClass} value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. Pneumonia" required />
      </Field>

      <FormFooter error={error} busy={busy} submitLabel="Admit patient" onCancel={onCancel} />
    </form>
  );
}
