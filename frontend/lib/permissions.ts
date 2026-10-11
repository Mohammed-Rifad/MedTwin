import type { Role } from "./types";

/**
 * Who may do what. These mirror the backend's rules (`action_roles` in hospital/views.py,
 * IsAdminOrReadOnly on equipment). The backend still checks every request; the frontend uses
 * this only to hide buttons people can't use.
 */
export const CAN: Record<string, Role[]> = {
  admit: ["NURSE", "ADMIN"],
  recordVitals: ["NURSE"],
  transfer: ["DOCTOR", "NURSE"],
  discharge: ["DOCTOR"],
  cleanBed: ["ADMIN", "DOCTOR", "NURSE"],
  logArrival: ["NURSE", "ADMIN"],
  admitFromEmergency: ["NURSE", "ADMIN"],
  dischargeFromEmergency: ["DOCTOR", "NURSE"],
  handleAlerts: ["ADMIN", "DOCTOR", "NURSE"],
  manageEquipment: ["ADMIN"],
};
