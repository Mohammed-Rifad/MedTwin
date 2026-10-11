"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";

import { api, getTokens } from "./api";
import type { HospitalClock } from "./types";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://127.0.0.1:8000";

export type LiveStatus = "connecting" | "live" | "reconnecting";
type Listener = (data: unknown) => void;

type LiveContextValue = {
  status: LiveStatus;
  subscribe: (type: string, listener: Listener) => () => void;
};

const LiveContext = createContext<LiveContextValue | null>(null);
// The clock ticks every second, so it has its own context: only the clock display re-renders, not the map.
const ClockContext = createContext<HospitalClock | null>(null);

/**
 * One live connection for the whole app. Screens subscribe to the message types they care about
 * (e.g. "bed_update"). If the connection drops, it reconnects by itself, waiting a little longer each time.
 */
export function LiveProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<LiveStatus>("connecting");
  const [clock, setClock] = useState<HospitalClock | null>(null);
  const listeners = useRef(new Map<string, Set<Listener>>());

  useEffect(() => {
    let socket: WebSocket | null = null;
    let retryTimer: ReturnType<typeof setTimeout> | undefined;
    let attempt = 0;
    let stopped = false;

    async function connect() {
      // Make sure the login token is fresh: this call quietly renews it if it has expired.
      // If the whole session has expired, the auth provider takes the user to the login page.
      await api("/api/auth/me/").catch(() => undefined);
      const tokens = getTokens();
      if (stopped || !tokens) return;

      socket = new WebSocket(`${WS_URL}/ws/hospital/?token=${encodeURIComponent(tokens.access)}`);
      socket.onopen = () => {
        attempt = 0;
        setStatus("live");
      };
      socket.onmessage = (event) => {
        const message = JSON.parse(event.data) as { type: string; data: unknown };
        if (message.type === "clock") setClock(message.data as HospitalClock);
        listeners.current.get(message.type)?.forEach((listener) => listener(message.data));
      };
      socket.onclose = () => {
        if (stopped) return;
        setStatus("reconnecting");
        const delay = Math.min(15_000, 1_000 * 2 ** attempt); // 1 s, 2 s, 4 s … up to 15 s
        attempt += 1;
        retryTimer = setTimeout(connect, delay);
      };
    }

    connect();
    return () => {
      stopped = true;
      clearTimeout(retryTimer);
      socket?.close();
    };
  }, []);

  const subscribe = useCallback((type: string, listener: Listener) => {
    const set = listeners.current.get(type) ?? new Set<Listener>();
    set.add(listener);
    listeners.current.set(type, set);
    return () => {
      set.delete(listener);
    };
  }, []);

  const value = useMemo(() => ({ status, subscribe }), [status, subscribe]);

  return (
    <LiveContext.Provider value={value}>
      <ClockContext.Provider value={clock}>{children}</ClockContext.Provider>
    </LiveContext.Provider>
  );
}

export function useLiveStatus(): LiveStatus {
  const value = useContext(LiveContext);
  if (!value) throw new Error("useLiveStatus must be used inside <LiveProvider>");
  return value.status;
}

export function useHospitalClock(): HospitalClock | null {
  return useContext(ClockContext);
}

/** Run `handler` every time a live message of this type arrives, e.g. useLiveEvent("bed_update", ...). */
export function useLiveEvent<T>(type: string, handler: (data: T) => void) {
  const value = useContext(LiveContext);
  if (!value) throw new Error("useLiveEvent must be used inside <LiveProvider>");
  const { subscribe } = value;
  const handlerRef = useRef(handler);

  useEffect(() => {
    handlerRef.current = handler;
  });

  useEffect(() => subscribe(type, (data) => handlerRef.current(data as T)), [type, subscribe]);
}
