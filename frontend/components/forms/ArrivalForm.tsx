"use client";

import { useState } from "react";

import { api } from "@/lib/api";
import { TRIAGE_LABELS, type EmergencyArrival } from "@/lib/types";

import { errorText, Field, FormFooter, inputClass } from "./fields";
import { emptyChoice, ensurePatient, PatientChooser, type PatientChoice } from "./PatientChooser";

/** A nurse logs someone arriving at the emergency department, with their triage level. */
export function ArrivalForm({ onDone, onCancel }: { onDone: (arrival: EmergencyArrival) => void; onCancel: () => void }) {
  const [choice, setChoice] = useState<PatientChoice>(emptyChoice);
  const [triage, setTriage] = useState("3");
  const [complaint, setComplaint] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      const saved = await ensurePatient(choice);
      setChoice(saved.choice);
      const arrival = await api<EmergencyArrival>("/api/hospital/emergency/", {
        method: "POST",
        body: JSON.stringify({ patient: saved.id, triage_level: Number(triage), complaint }),
      });
      onDone(arrival);
    } catch (err) {
      setError(errorText(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4">
      <PatientChooser choice={choice} onChange={setChoice} />
      <Field label="Triage level" hint="1 = most urgent">
        <select className={inputClass} value={triage} onChange={(e) => setTriage(e.target.value)}>
          {[1, 2, 3, 4, 5].map((level) => (
            <option key={level} value={level}>
              {level} · {TRIAGE_LABELS[level]}
            </option>
          ))}
        </select>
      </Field>
      <Field label="Main complaint">
        <input className={inputClass} value={complaint} onChange={(e) => setComplaint(e.target.value)} placeholder="e.g. Chest pain" required />
      </Field>
      <FormFooter error={error} busy={busy} submitLabel="Log arrival" onCancel={onCancel} />
    </form>
  );
}
