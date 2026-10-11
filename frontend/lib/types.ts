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
  capacity: number;
  occupied: number;
};

export const ROLE_LABELS: Record<Role, string> = {
  ADMIN: "Admin",
  DOCTOR: "Doctor",
  NURSE: "Nurse",
};
