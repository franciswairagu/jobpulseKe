import React, { createContext, useContext, useReducer, useCallback } from "react";

// This is the "shared application state" called for in the spec (section
// 16): one place holding user profile, CV analysis, saved jobs and global
// filters, so every page reads/writes the same source of truth instead of
// keeping its own local copies of fake data.

const AppStateContext = createContext(null);
const AppDispatchContext = createContext(null);

const initialState = {
  profile: { name: "Alvin", greeting: "Good morning" },
  cvAnalysis: null, // set once /api/cv/analyze resolves; personalizes the Dashboard
  savedJobIds: [],
  filters: { region: "All Africa", period: "Last 6 months" },
  notifications: [],
};

function reducer(state, action) {
  switch (action.type) {
    case "SET_CV_ANALYSIS":
      return { ...state, cvAnalysis: action.payload };
    case "CLEAR_CV_ANALYSIS":
      return { ...state, cvAnalysis: null };
    case "TOGGLE_SAVE_JOB": {
      const id = action.payload;
      const exists = state.savedJobIds.includes(id);
      return {
        ...state,
        savedJobIds: exists ? state.savedJobIds.filter((j) => j !== id) : [...state.savedJobIds, id],
      };
    }
    case "SET_FILTERS":
      return { ...state, filters: { ...state.filters, ...action.payload } };
    default:
      return state;
  }
}

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);
  return (
    <AppStateContext.Provider value={state}>
      <AppDispatchContext.Provider value={dispatch}>{children}</AppDispatchContext.Provider>
    </AppStateContext.Provider>
  );
}

export function useAppState() {
  const ctx = useContext(AppStateContext);
  if (!ctx) throw new Error("useAppState must be used within AppProvider");
  return ctx;
}

export function useAppDispatch() {
  const ctx = useContext(AppDispatchContext);
  if (!ctx) throw new Error("useAppDispatch must be used within AppProvider");
  return ctx;
}

// Convenience hooks built on top of the raw dispatch, so pages don't need to
// know action-type strings.
export function useCVAnalysisActions() {
  const dispatch = useAppDispatch();
  const setCVAnalysis = useCallback((analysis) => dispatch({ type: "SET_CV_ANALYSIS", payload: analysis }), [dispatch]);
  const clearCVAnalysis = useCallback(() => dispatch({ type: "CLEAR_CV_ANALYSIS" }), [dispatch]);
  return { setCVAnalysis, clearCVAnalysis };
}

export function useSavedJobs() {
  const { savedJobIds } = useAppState();
  const dispatch = useAppDispatch();
  const toggleSaveJob = useCallback((id) => dispatch({ type: "TOGGLE_SAVE_JOB", payload: id }), [dispatch]);
  return { savedJobIds, toggleSaveJob };
}

export function useFilters() {
  const { filters } = useAppState();
  const dispatch = useAppDispatch();
  const setFilters = useCallback((patch) => dispatch({ type: "SET_FILTERS", payload: patch }), [dispatch]);
  return { filters, setFilters };
}
