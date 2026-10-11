"use client";

import { useCallback, useEffect, useState } from "react";

import { errorText, Field, FormFooter, inputClass } from "@/components/forms/fields";
import { Modal } from "@/components/Modal";
import { RequireRole } from "@/components/RequireRole";
import { ErrorMessage, Loading } from "@/components/States";
import { api } from "@/lib/api";
import { useLiveEvent } from "@/lib/live";
import type { Bed, Paginated, Unit } from "@/lib/types";

type Dialog = { kind: "rename-unit"; unit: Unit } | { kind: "rename-bed"; bed: Bed } | { kind: "add-bed"; unit: Unit } | null;

/** The next free bed code in a unit, e.g. ICU-13 after ICU-12. */
function nextBedCode(unit: Unit, beds: Bed[]): string {
  const numbers = beds.map((bed) => Number(bed.code.split("-").pop())).filter(Number.isFinite);
  return `${unit.code}-${String(Math.max(0, ...numbers) + 1).padStart(2, "0")}`;
}

const STATUS_TEXT: Record<Bed["status"], string> = { FREE: "Free", OCCUPIED: "Occupied", CLEANING: "Cleaning" };

function HospitalSetup() {
  const [units, setUnits] = useState<Unit[] | null>(null);
  const [beds, setBeds] = useState<Bed[]>([]);
  const [error, setError] = useState("");
  const [actionError, setActionError] = useState("");
  const [dialog, setDialog] = useState<Dialog>(null);

  const load = useCallback(() => {
    Promise.all([
      api<Paginated<Unit>>("/api/hospital/units/?page_size=100"),
      api<Paginated<Bed>>("/api/hospital/beds/?page_size=500"),
    ])
      .then(([unitPage, bedPage]) => {
        setUnits(unitPage.results);
        setBeds(bedPage.results);
        setError("");
      })
      .catch((err: Error) => setError(err.message));
  }, []);

  useEffect(load, [load]);
  useLiveEvent("reload", load); // sent after any setup change, by anyone
  useLiveEvent<Bed>("bed_update", (changed) => setBeds((current) => current.map((bed) => (bed.id === changed.id ? changed : bed))));

  async function setOpen(bed: Bed, open: boolean) {
    setActionError("");
    try {
      await api(`/api/hospital/beds/${bed.id}/`, { method: "PATCH", body: JSON.stringify({ is_active: open }) });
      load();
    } catch (err) {
      setActionError(errorText(err));
    }
  }

  const finished = () => {
    setDialog(null);
    load();
  };

  if (error) return <ErrorMessage message={error} />;
  if (!units) return <Loading message="Loading the hospital…" />;

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-800">Hospital setup</h1>
        <p className="text-slate-500">
          Add beds, rename them, or close a bed (for repairs or staff shortages). Closed beds stay on the map, greyed out, and don&apos;t count as capacity.
        </p>
      </div>

      {actionError && <ErrorMessage message={actionError} />}

      {units.map((unit) => {
        const unitBeds = beds.filter((bed) => bed.unit === unit.id).sort((a, b) => a.code.localeCompare(b.code));
        const closed = unitBeds.filter((bed) => !bed.is_active).length;
        return (
          <section key={unit.id} className="rounded-xl border border-slate-200 bg-white p-5">
            <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-slate-800">{unit.name}</h2>
                <p className="text-sm text-slate-500">
                  {unit.capacity} open beds{closed ? ` · ${closed} closed` : ""} · {unit.occupied} occupied
                </p>
              </div>
              <div className="flex gap-2">
                <button onClick={() => setDialog({ kind: "rename-unit", unit })} className="rounded-lg border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100">
                  Rename unit
                </button>
                <button onClick={() => setDialog({ kind: "add-bed", unit })} className="rounded-lg bg-sky-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-sky-700">
                  Add bed
                </button>
              </div>
            </div>

            <ul className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3 2xl:grid-cols-4">
              {unitBeds.map((bed) => (
                <li
                  key={bed.id}
                  className={`flex items-center justify-between gap-2 rounded-lg border px-3 py-2 text-sm ${
                    bed.is_active ? "border-slate-200" : "border-dashed border-slate-300 bg-slate-50 text-slate-400"
                  }`}
                >
                  <div>
                    <p className="font-medium">{bed.code}</p>
                    <p className="text-xs">{bed.is_active ? STATUS_TEXT[bed.status] : "Closed"}</p>
                  </div>
                  <div className="flex gap-1">
                    <button onClick={() => setDialog({ kind: "rename-bed", bed })} className="rounded-md px-2 py-1 text-xs text-slate-600 hover:bg-slate-100">
                      Rename
                    </button>
                    {bed.is_active ? (
                      <button
                        onClick={() => setOpen(bed, false)}
                        disabled={bed.status === "OCCUPIED"}
                        title={bed.status === "OCCUPIED" ? "Move or discharge the patient first" : "Close this bed"}
                        className="rounded-md px-2 py-1 text-xs text-red-600 hover:bg-red-50 disabled:cursor-not-allowed disabled:text-slate-300 disabled:hover:bg-transparent"
                      >
                        Close
                      </button>
                    ) : (
                      <button onClick={() => setOpen(bed, true)} className="rounded-md px-2 py-1 text-xs text-emerald-700 hover:bg-emerald-50">
                        Reopen
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </section>
        );
      })}

      {dialog?.kind === "add-bed" && (
        <Modal title={`Add a bed · ${dialog.unit.name}`} onClose={() => setDialog(null)}>
          <NameForm
            label="Bed code"
            initial={nextBedCode(dialog.unit, beds.filter((bed) => bed.unit === dialog.unit.id))}
            hint="The unit's beds are re-arranged on the map to make room."
            submitLabel="Add bed"
            onSave={(code) => api("/api/hospital/beds/", { method: "POST", body: JSON.stringify({ unit: dialog.unit.id, code }) })}
            onDone={finished}
            onCancel={() => setDialog(null)}
          />
        </Modal>
      )}
      {dialog?.kind === "rename-bed" && (
        <Modal title={`Rename bed ${dialog.bed.code}`} onClose={() => setDialog(null)}>
          <NameForm
            label="Bed code"
            initial={dialog.bed.code}
            submitLabel="Save"
            onSave={(code) => api(`/api/hospital/beds/${dialog.bed.id}/`, { method: "PATCH", body: JSON.stringify({ code }) })}
            onDone={finished}
            onCancel={() => setDialog(null)}
          />
        </Modal>
      )}
      {dialog?.kind === "rename-unit" && (
        <Modal title={`Rename ${dialog.unit.name}`} onClose={() => setDialog(null)}>
          <NameForm
            label="Unit name"
            initial={dialog.unit.name}
            submitLabel="Save"
            onSave={(name) => api(`/api/hospital/units/${dialog.unit.id}/`, { method: "PATCH", body: JSON.stringify({ name }) })}
            onDone={finished}
            onCancel={() => setDialog(null)}
          />
        </Modal>
      )}
    </div>
  );
}

/** A one-field form used for adding a bed and for renaming beds and units. */
function NameForm({
  label,
  initial,
  hint,
  submitLabel,
  onSave,
  onDone,
  onCancel,
}: {
  label: string;
  initial: string;
  hint?: string;
  submitLabel: string;
  onSave: (value: string) => Promise<unknown>;
  onDone: () => void;
  onCancel: () => void;
}) {
  const [value, setValue] = useState(initial);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    try {
      await onSave(value.trim());
      onDone();
    } catch (err) {
      setError(errorText(err));
      setBusy(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col gap-4">
      <Field label={label}>
        <input className={inputClass} value={value} onChange={(event) => setValue(event.target.value)} required autoFocus />
      </Field>
      {hint && <p className="text-xs text-slate-500">{hint}</p>}
      <FormFooter error={error} busy={busy} submitLabel={submitLabel} onCancel={onCancel} />
    </form>
  );
}

export default function HospitalSetupPage() {
  return (
    <RequireRole roles={["ADMIN"]}>
      <HospitalSetup />
    </RequireRole>
  );
}
