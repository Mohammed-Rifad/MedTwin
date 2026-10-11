import type { Role } from "./types";

/**
 * Who may do what. These mirror the backend's rules (hospital/views.py `action_roles`).
 * The backend still checks every request; the frontend uses this only to hide buttons people can't use.
 */
export const CAN: Record<string, Role[]> = {
  admit: ["NURSE", "ADMIN"],
  recordVitals: ["NURSE"],
  transfer: ["DOCTOR", "NURSE"],
  discharge: ["DOCTOR"],
  cleanBed: ["ADMIN", "DOCTOR", "NURSE"],
};
