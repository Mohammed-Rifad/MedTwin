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
  status_since: string | null;
  is_active: boolean;
  map_x: number;
  map_y: number;
  current_admission: CurrentAdmission | null;
};

export type Admission = {
  id: number;
  patient: number;
  patient_name: string;
  bed: number;
  bed_code: string;
  unit: string;
  reason: string;
  admitted_at: string;
  expected_discharge_at: string | null;
  discharged_at: string | null;
  outcome: "" | "HOME" | "TRANSFERRED" | "DECEASED";
  risk_score: number | null;
  risk_level: RiskLevel;
  length_of_stay_hours: number;
};

export type Patient = {
  id: number;
  mrn: string;
  first_name: string;
  last_name: string;
  date_of_birth: string;
  sex: "M" | "F" | "O";
  age: number;
  current_admission: CurrentAdmission | null;
  created_at: string;
};

export type PatientDetail = Patient & { admissions: Admission[] };

export type VitalReading = {
  id: number;
  recorded_at: string;
  heart_rate: number | null;
  spo2: number | null;
  systolic_bp: number | null;
  diastolic_bp: number | null;
  respiratory_rate: number | null;
  temperature: number | null;
  source: "MONITOR" | "MANUAL";
};

export const SEX_LABELS: Record<Patient["sex"], string> = { M: "Male", F: "Female", O: "Other" };

export const OUTCOME_LABELS: Record<Admission["outcome"], string> = {
  "": "Current stay",
  HOME: "Discharged home",
  TRANSFERRED: "Transferred out",
  DECEASED: "Deceased",
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
