"use client";

import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { CAN } from "@/lib/permissions";

import { AdmitForm } from "./forms/AdmitForm";
import { DischargeForm } from "./forms/DischargeForm";
import { errorText } from "./forms/fields";
import { TransferForm } from "./forms/TransferForm";
import { VitalsForm } from "./forms/VitalsForm";
import { Modal } from "./Modal";
import { ErrorMessage } from "./States";

type Form = "vitals" | "transfer" | "discharge" | "admit" | null;

const buttonClass = "rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100";
const primaryClass = "rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-sky-700";

/** A short "done" message that disappears after a few seconds. */
function useFlash(): [string, (message: string) => void] {
  const [flash, setFlash] = useState("");
  useEffect(() => {
    if (!flash) return;
    const timer = setTimeout(() => setFlash(""), 4000);
    return () => clearTimeout(timer);
  }, [flash]);
  return [flash, setFlash];
}

function Flash({ message }: { message: string }) {
  return message ? <p className="text-sm text-emerald-700">✓ {message}</p> : null;
}

/** Buttons for a patient who is in a bed: record vitals, transfer, discharge (each only for allowed roles). */
export function AdmissionActions({
  admissionId,
  bedCode,
  patientName,
  onChanged,
}: {
  admissionId: number;
  bedCode: string;
  patientName: string;
  onChanged?: () => void;
}) {
  const { hasRole } = useAuth();
  const [form, setForm] = useState<Form>(null);
  const [flash, setFlash] = useFlash();

  function finished(message: string) {
    setForm(null);
    setFlash(message);
    onChanged?.();
  }

  const close = () => setForm(null);
  const buttons = [
    hasRole(...CAN.recordVitals) && (
      <button key="vitals" className={primaryClass} onClick={() => setForm("vitals")}>
        Record vitals
      </button>
    ),
    hasRole(...CAN.transfer) && (
      <button key="transfer" className={buttonClass} onClick={() => setForm("transfer")}>
        Transfer
      </button>
    ),
    hasRole(...CAN.discharge) && (
      <button key="discharge" className={buttonClass} onClick={() => setForm("discharge")}>
        Discharge
      </button>
    ),
  ].filter(Boolean);

  if (buttons.length === 0 && !flash) return null;

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-2">{buttons}</div>
      <Flash message={flash} />

      {form === "vitals" && (
        <Modal title={`Record vital signs · ${patientName}`} onClose={close}>
          <VitalsForm admissionId={admissionId} onDone={() => finished("Vital signs saved.")} onCancel={close} />
        </Modal>
      )}
      {form === "transfer" && (
        <Modal title={`Transfer · ${patientName}`} onClose={close}>
          <TransferForm
            admissionId={admissionId}
            currentBed={bedCode}
            onDone={(admission) => finished(`Moved to ${admission.bed_code}.`)}
            onCancel={close}
          />
        </Modal>
      )}
      {form === "discharge" && (
        <Modal title={`Discharge · ${patientName}`} onClose={close}>
          <DischargeForm admissionId={admissionId} patientName={patientName} onDone={() => finished("Patient discharged.")} onCancel={close} />
        </Modal>
      )}
    </div>
  );
}

/** Buttons for an empty bed: admit someone (free bed) or mark it clean (cleaning bed). */
export function EmptyBedActions({
  bed,
  onChanged,
}: {
  bed: { id: number; code: string; status: string; is_active: boolean };
  onChanged?: () => void;
}) {
  const { hasRole } = useAuth();
  const [form, setForm] = useState<Form>(null);
  const [flash, setFlash] = useFlash();
  const [error, setError] = useState("");

  async function markClean() {
    setError("");
    try {
      await api(`/api/hospital/beds/${bed.id}/clean/`, { method: "POST" });
      setFlash("Bed is ready for the next patient.");
      onChanged?.();
    } catch (err) {
      setError(errorText(err));
    }
  }

  if (!bed.is_active) return null;
  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-2">
        {bed.status === "FREE" && hasRole(...CAN.admit) && (
          <button className={primaryClass} onClick={() => setForm("admit")}>
            Admit a patient here
          </button>
        )}
        {bed.status === "CLEANING" && hasRole(...CAN.cleanBed) && (
          <button className={buttonClass} onClick={markClean}>
            Mark as clean
          </button>
        )}
      </div>
      {error && <ErrorMessage message={error} />}
      <Flash message={flash} />

      {form === "admit" && (
        <Modal title={`Admit a patient · ${bed.code}`} onClose={() => setForm(null)}>
          <AdmitForm
            presetBed={{ id: bed.id, code: bed.code }}
            onDone={(admission) => {
              setForm(null);
              setFlash(`${admission.patient_name} admitted.`);
              onChanged?.();
            }}
            onCancel={() => setForm(null)}
          />
        </Modal>
      )}
    </div>
  );
}

/** "Register & admit" button for the Patients page, or "Admit" for a patient who isn't in a bed. */
export function AdmitButton({
  patient,
  label = "Register & admit patient",
  onDone,
}: {
  patient?: { id: number; name: string };
  label?: string;
  onDone?: () => void;
}) {
  const { hasRole } = useAuth();
  const [open, setOpen] = useState(false);
  const [flash, setFlash] = useFlash();

  if (!hasRole(...CAN.admit)) return null;
  return (
    <div className="flex items-center gap-3">
      <button className={primaryClass} onClick={() => setOpen(true)}>
        {label}
      </button>
      <Flash message={flash} />
      {open && (
        <Modal title={patient ? `Admit · ${patient.name}` : "Register & admit a patient"} onClose={() => setOpen(false)}>
          <AdmitForm
            presetPatient={patient}
            onDone={(admission) => {
              setOpen(false);
              setFlash(`${admission.patient_name} admitted to ${admission.bed_code}.`);
              onDone?.();
            }}
            onCancel={() => setOpen(false)}
          />
        </Modal>
      )}
    </div>
  );
}
