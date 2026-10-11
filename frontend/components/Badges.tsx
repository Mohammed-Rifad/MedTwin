import {
  EQUIPMENT_STATUS_LABELS,
  TRIAGE_LABELS,
  type AlertSeverity,
  type AlertStatus,
  type EquipmentStatus,
} from "@/lib/types";

// Triage colours follow the usual emergency-department convention: 1 = red (most urgent) … 5 = blue.
const TRIAGE_STYLE: Record<number, string> = {
  1: "bg-red-600 text-white",
  2: "bg-orange-500 text-white",
  3: "bg-amber-300 text-amber-950",
  4: "bg-emerald-500 text-white",
  5: "bg-sky-500 text-white",
};

export function TriageBadge({ level }: { level: number }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold ${TRIAGE_STYLE[level]}`}>
      {level} · {TRIAGE_LABELS[level]}
    </span>
  );
}

const SEVERITY_STYLE: Record<AlertSeverity, string> = {
  CRITICAL: "bg-red-600 text-white",
  WARNING: "bg-amber-400 text-amber-950",
  INFO: "bg-sky-100 text-sky-800",
};

export function SeverityBadge({ severity }: { severity: AlertSeverity }) {
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${SEVERITY_STYLE[severity]}`}>
      {severity.charAt(0) + severity.slice(1).toLowerCase()}
    </span>
  );
}

const STATUS_STYLE: Record<AlertStatus, string> = {
  OPEN: "border-red-200 text-red-700",
  ACKNOWLEDGED: "border-amber-200 text-amber-700",
  RESOLVED: "border-emerald-200 text-emerald-700",
};

export function AlertStatusBadge({ status }: { status: AlertStatus }) {
  return (
    <span className={`rounded-full border px-2 py-0.5 text-xs font-medium ${STATUS_STYLE[status]}`}>
      {status.charAt(0) + status.slice(1).toLowerCase()}
    </span>
  );
}

const EQUIPMENT_STYLE: Record<EquipmentStatus, string> = {
  OK: "bg-emerald-100 text-emerald-800",
  WARNING: "bg-amber-100 text-amber-800",
  FAULT: "bg-red-600 text-white",
  MAINTENANCE: "bg-slate-200 text-slate-700",
};

export function EquipmentStatusBadge({ status }: { status: EquipmentStatus }) {
  return <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${EQUIPMENT_STYLE[status]}`}>{EQUIPMENT_STATUS_LABELS[status]}</span>;
}
