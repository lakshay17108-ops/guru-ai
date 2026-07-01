/**
 * LearningPathContext
 *
 * Manages the application's core state via useReducer + Context:
 *   - learningPath: the generated curriculum (or null)
 *   - isLoading: whether an API call is in flight
 *   - error: error message string (or null)
 *
 * Why useReducer over useState?
 *   State transitions are interdependent (e.g., setting loading must clear
 *   error, setting path must clear loading). A reducer makes these transitions
 *   explicit and prevents impossible states.
 */

import { createContext, useContext, useReducer, useCallback } from 'react';
import { generateLearningPath } from '../services/api';

// --- Action Types ---
const ACTIONS = {
  SET_LOADING: 'SET_LOADING',
  SET_PATH: 'SET_PATH',
  SET_ERROR: 'SET_ERROR',
  CLEAR_PATH: 'CLEAR_PATH',
  CLEAR_ERROR: 'CLEAR_ERROR',
};

// --- Initial State ---
const initialState = {
  learningPath: null,
  isLoading: false,
  error: null,
};

// --- Reducer ---
function learningPathReducer(state, action) {
  switch (action.type) {
    case ACTIONS.SET_LOADING:
      return { ...state, isLoading: true, error: null };
    case ACTIONS.SET_PATH:
      return { ...state, learningPath: action.payload, isLoading: false, error: null };
    case ACTIONS.SET_ERROR:
      return { ...state, error: action.payload, isLoading: false };
    case ACTIONS.CLEAR_PATH:
      return { ...state, learningPath: null };
    case ACTIONS.CLEAR_ERROR:
      return { ...state, error: null };
    default:
      return state;
  }
}

// --- Context ---
const LearningPathContext = createContext(null);

/**
 * Provider component — wrap the app with this.
 */
export function LearningPathProvider({ children }) {
  const [state, dispatch] = useReducer(learningPathReducer, initialState);

  const generatePath = useCallback(async (topic, difficulty) => {
    dispatch({ type: ACTIONS.SET_LOADING });

    try {
      const data = await generateLearningPath(topic, difficulty);
      dispatch({ type: ACTIONS.SET_PATH, payload: data });
    } catch (err) {
      dispatch({ type: ACTIONS.SET_ERROR, payload: err.message });
    }
  }, []);

  const clearPath = useCallback(() => {
    dispatch({ type: ACTIONS.CLEAR_PATH });
  }, []);

  const clearError = useCallback(() => {
    dispatch({ type: ACTIONS.CLEAR_ERROR });
  }, []);

  const value = {
    ...state,
    generatePath,
    clearPath,
    clearError,
  };

  return (
    <LearningPathContext.Provider value={value}>
      {children}
    </LearningPathContext.Provider>
  );
}

/**
 * Custom hook — use this in any component that needs learning path state.
 * Throws if used outside of LearningPathProvider.
 */
export function useLearningPath() {
  const context = useContext(LearningPathContext);
  if (!context) {
    throw new Error('useLearningPath must be used within a LearningPathProvider');
  }
  return context;
}
