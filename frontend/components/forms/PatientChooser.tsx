"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { Paginated, Patient } from "@/lib/types";

import { Field, inputClass } from "./fields";

/** What the person filling in the form chose: a new patient's details, or an existing patient. */
export type PatientChoice = {
  mode: "new" | "existing";
  firstName: string;
  lastName: string;
  birthDate: string;
  sex: string;
  patientId: string;
  registeredName: string; // set once a new patient has been saved
};

export const emptyChoice: PatientChoice = {
  mode: "new",
  firstName: "",
  lastName: "",
  birthDate: "",
  sex: "F",
  patientId: "",
  registeredName: "",
};

const today = new Date().toISOString().slice(0, 10);

/**
 * Returns the chosen patient's id, registering them first if they're new.
 * Afterwards the choice points at the saved patient, so a retry never registers them twice.
 */
export async function ensurePatient(choice: PatientChoice): Promise<{ id: number; choice: PatientChoice }> {
  if (choice.mode === "existing") return { id: Number(choice.patientId), choice };
  const patient = await api<Patient>("/api/hospital/patients/", {
    method: "POST",
    body: JSON.stringify({
      first_name: choice.firstName,
      last_name: choice.lastName,
      date_of_birth: choice.birthDate,
      sex: choice.sex,
    }),
  });
  return {
    id: patient.id,
    choice: {
      ...choice,
      mode: "existing",
      patientId: String(patient.id),
      registeredName: `${patient.first_name} ${patient.last_name} (${patient.mrn})`,
    },
  };
}

/** "New patient" (name, date of birth, sex) or "Existing patient" (search among people not in a bed). */
export function PatientChooser({ choice, onChange }: { choice: PatientChoice; onChange: (choice: PatientChoice) => void }) {
  const [search, setSearch] = useState("");
  const [matches, setMatches] = useState<Patient[]>([]);
  const set = (changes: Partial<PatientChoice>) => onChange({ ...choice, ...changes });

  useEffect(() => {
    if (choice.mode !== "existing" || choice.registeredName || search.trim().length < 2) return;
    const timer = setTimeout(() => {
      api<Paginated<Patient>>(`/api/hospital/patients/?admitted=false&page_size=10&search=${encodeURIComponent(search.trim())}`)
        .then((page) => setMatches(page.results))
        .catch(() => setMatches([]));
    }, 300);
    return () => clearTimeout(timer);
  }, [choice.mode, choice.registeredName, search]);

  if (choice.registeredName) {
    return (
      <p className="text-sm text-slate-600">
        Patient: <span className="font-medium text-slate-800">{choice.registeredName}</span>
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <div className="flex gap-1 rounded-lg bg-slate-100 p-1 text-sm">
        {(["new", "existing"] as const).map((option) => (
          <button
            key={option}
            type="button"
            onClick={() => set({ mode: option })}
            className={`flex-1 rounded-md px-3 py-1.5 ${choice.mode === option ? "bg-white font-medium shadow-sm" : "text-slate-600"}`}
          >
            {option === "new" ? "New patient" : "Existing patient"}
          </button>
        ))}
      </div>

      {choice.mode === "new" ? (
        <div className="grid grid-cols-2 gap-3">
          <Field label="First name">
            <input className={inputClass} value={choice.firstName} onChange={(e) => set({ firstName: e.target.value })} required autoFocus />
          </Field>
          <Field label="Last name">
            <input className={inputClass} value={choice.lastName} onChange={(e) => set({ lastName: e.target.value })} required />
          </Field>
          <Field label="Date of birth">
            <input type="date" max={today} className={inputClass} value={choice.birthDate} onChange={(e) => set({ birthDate: e.target.value })} required />
          </Field>
          <Field label="Sex">
            <select className={inputClass} value={choice.sex} onChange={(e) => set({ sex: e.target.value })}>
              <option value="F">Female</option>
              <option value="M">Male</option>
              <option value="O">Other</option>
            </select>
          </Field>
        </div>
      ) : (
        <Field label="Find patient" hint="name or MRN, not currently admitted">
          <input className={inputClass} value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Type at least 2 letters…" autoFocus />
          {matches.length > 0 && (
            <select className={`${inputClass} mt-2`} value={choice.patientId} onChange={(e) => set({ patientId: e.target.value })} required>
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
    </div>
  );
}
