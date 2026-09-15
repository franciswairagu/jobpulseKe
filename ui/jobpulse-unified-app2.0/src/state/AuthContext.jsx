import React, { createContext, useContext, useReducer, useCallback, useEffect } from "react";

const AuthContext = createContext(null);
const AuthDispatchContext = createContext(null);

const STORAGE_KEY = "jobpulse_auth";

function loadInitialAuth() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) return JSON.parse(raw);
  } catch {}
  return { token: null, refreshToken: null, user: null, startupId: null };
}

const initialState = loadInitialAuth();

function reducer(state, action) {
  switch (action.type) {
    case "LOGIN":
      // Clear previous user's CV analysis on login
      localStorage.removeItem("jobpulse_cv_analysis");
      return { ...state, ...action.payload };
    case "LOGOUT":
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem("jobpulse_cv_analysis");
      return { token: null, refreshToken: null, user: null, startupId: null };
    case "SET_USER":
      return { ...state, user: action.payload };
    case "SET_STARTUP_ID":
      return { ...state, startupId: action.payload };
    default:
      return state;
  }
}

export function AuthProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);

  useEffect(() => {
    if (state.token) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    }
  }, [state.token, state.user, state.startupId]);

  return (
    <AuthContext.Provider value={state}>
      <AuthDispatchContext.Provider value={dispatch}>{children}</AuthDispatchContext.Provider>
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}

export function useAuthDispatch() {
  const ctx = useContext(AuthDispatchContext);
  if (!ctx) throw new Error("useAuthDispatch must be used within AuthProvider");
  return ctx;
}

export function useAuthActions() {
  const dispatch = useAuthDispatch();
  const login = useCallback((payload) => dispatch({ type: "LOGIN", payload }), [dispatch]);
  const logout = useCallback(() => dispatch({ type: "LOGOUT" }), [dispatch]);
  const setUser = useCallback((user) => dispatch({ type: "SET_USER", payload: user }), [dispatch]);
  const setStartupId = useCallback((id) => dispatch({ type: "SET_STARTUP_ID", payload: id }), [dispatch]);
  return { login, logout, setUser, setStartupId };
}
