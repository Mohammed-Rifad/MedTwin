export type Role = "ADMIN" | "DOCTOR" | "NURSE";

export type User = {
  id: number;
  username: string;
  first_name: string;
  last_name: string;
  email: string;
  role: Role;
};

export type Paginated<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};

export type Unit = {
  id: number;
  name: string;
  code: string;
  unit_type: "ICU" | "WARD" | "ED";
  floor: number;
  map_x: number;
  map_y: number;
  map_width: number;
  map_height: number;
  capacity: number;
  occupied: number;
};

export type RiskLevel = "LOW" | "MEDIUM" | "HIGH" | "";

export type CurrentAdmission = {
  id: number;
  patient_id: number;
  patient_name: string;
  bed: string;
  admitted_at: string;
  risk_score: number | null;
  risk_level: RiskLevel;
};

export type Bed = {
  id: number;
  unit: number;
  unit_code: string;
  code: string;
  status: "FREE" | "OCCUPIED" | "CLEANING";
  is_active: boolean;
  map_x: number;
  map_y: number;
  current_admission: CurrentAdmission | null;
};

export type HospitalClock = {
  hospital_time: string;
  running: boolean;
  speed: number;
};

export const ROLE_LABELS: Record<Role, string> = {
  ADMIN: "Admin",
  DOCTOR: "Doctor",
  NURSE: "Nurse",
};
