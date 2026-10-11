"use client";

import { useState } from "react";

import { api } from "@/lib/api";
import type { Admission } from "@/lib/types";

import { BedSelect } from "./BedSelect";
import { errorText, Field, FormFooter, inputClass } from "./fields";
import { emptyChoice, ensurePatient, PatientChooser, type PatientChoice } from "./PatientChooser";

type Props = {
  presetBed?: { id: number; code: string }; // opened from a free bed on the map
  presetPatient?: { id: number; name: string }; // opened from a patient's page
  onDone: (admission: Admission) => void;
  onCancel: () => void;
};

/** Register a new patient (or pick an existing one) and admit them to a free bed. */
export function AdmitForm({ presetBed, presetPatient, onDone, onCancel }: Props) {
  const [choice, setChoice] = useState<PatientChoice>(
    presetPatient
      ? { ...emptyChoice, mode: "existing", patientId: String(presetPatient.id), registeredName: presetPatient.name }
      : emptyChoice,
  );
  const [bedId, setBedId] = useState(presetBed ? String(presetBed.id) : "");
  const [reason, setReason] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const saved = await ensurePatient(choice);
      setChoice(saved.choice); // if admitting fails below, a retry won't register the patient again
      const admission = await api<Admission>("/api/hospital/admissions/", {
        method: "POST",
        body: JSON.stringify({ patient: saved.id, bed: Number(bedId), reason }),
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
      <PatientChooser choice={choice} onChange={setChoice} />

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
