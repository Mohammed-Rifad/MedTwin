"use client";

import type { VitalReading } from "@/lib/types";

import { MetricCharts, type Metric } from "./MetricCharts";

const VITALS: Metric<VitalReading>[] = [
  { key: "heart_rate", label: "Heart rate", unit: "/min", color: "#ef4444" },
  { key: "spo2", label: "SpO₂", unit: "%", color: "#0284c7" },
  { key: "respiratory_rate", label: "Breathing", unit: "/min", color: "#7c3aed" },
  { key: "systolic_bp", label: "Blood pressure", unit: "mmHg", color: "#d97706", second: { key: "diastolic_bp", color: "#f59e0b" } },
  { key: "temperature", label: "Temperature", unit: "°C", color: "#059669" },
];

/** A patient's vital signs: latest values plus a small chart each. */
export function VitalsChart({ readings }: { readings: VitalReading[] }) {
  return <MetricCharts readings={readings} metrics={VITALS} empty="No vital signs recorded yet." />;
}
