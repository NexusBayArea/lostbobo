import { createContext, useContext, useReducer, useEffect, useCallback, type ReactNode } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { supabase } from '@/lib/supabase';
import { onboardingReducer, initialState, type OnboardingState, type OnboardingAction } from './onboardingReducer';
import { steps } from './steps';

interface OnboardingContextType {
  state: OnboardingState;
  dispatch: React.Dispatch<OnboardingAction>;
  nextStep: () => void;
  prevStep: () => void;
  skipOnboarding: () => void;
  trackEvent: (event: string) => void;
  currentStepDef: typeof steps[0] | undefined;
  isOnboardingActive: boolean;
}

const OnboardingContext = createContext<OnboardingContextType>({
  state: initialState,
  dispatch: () => {},
  nextStep: () => {},
  prevStep: () => {},
  skipOnboarding: () => {},
  trackEvent: () => {},
  currentStepDef: undefined,
  isOnboardingActive: false,
});

const STORAGE_KEY = 'simhpc_onboarding_cache';

export function OnboardingProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [state, dispatch] = useReducer(onboardingReducer, initialState);

  // Load from localStorage instantly, then hydrate from Supabase
  useEffect(() => {
    if (!user) return;

    const cached = localStorage.getItem(STORAGE_KEY);
    if (cached) {
      try {
        const parsed = JSON.parse(cached);
        dispatch({ type: 'HYDRATE', payload: parsed });
      } catch { /* ignore */ }
    }

    if (!supabase) return;

    supabase
      .from('onboarding_state')
      .select('*')
      .eq('user_id', user.id)
      .single()
      .then(({ data, error }) => {
        if (data && !error) {
          dispatch({
            type: 'HYDRATE',
            payload: {
              currentStep: data.current_step || 'welcome',
              completedSteps: data.completed_steps || [],
              events: data.events || [],
              skipped: data.skipped || false,
              version: data.version || 1,
            },
          });
        }
      });
  }, [user?.id]);

  // Autosave to Supabase (debounced)
  useEffect(() => {
    if (!user?.id || !supabase || state.currentStep === initialState.currentStep && state.completedSteps.length === 0) return;

    const timeout = setTimeout(() => {
      const client = supabase;
      if (!client) return;
      client
        .from('onboarding_state')
        .upsert({
          user_id: user.id,
          current_step: state.currentStep,
          completed_steps: state.completedSteps,
          events: state.events,
          skipped: state.skipped,
          version: state.version,
          updated_at: new Date().toISOString(),
        }, { onConflict: 'user_id' })
        .then(({ error }) => {
          if (error) console.warn('Onboarding autosave failed:', error.message);
        });

      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    }, 800);

    return () => clearTimeout(timeout);
  }, [state, user?.id]);

  const nextStep = useCallback(() => {
    const currentIndex = steps.findIndex(s => s.id === state.currentStep);
    const currentDef = steps[currentIndex];
    const nextId = currentDef?.next;
    if (nextId) {
      dispatch({ type: 'SET_STEP', payload: nextId });
    }
  }, [state.currentStep]);

  const prevStep = useCallback(() => {
    const currentIndex = steps.findIndex(s => s.id === state.currentStep);
    if (currentIndex > 0) {
      dispatch({ type: 'SET_STEP', payload: steps[currentIndex - 1].id });
    }
  }, [state.currentStep]);

  const skipOnboarding = useCallback(() => {
    dispatch({ type: 'SKIP' });
  }, []);

  const trackEvent = useCallback((event: string) => {
    dispatch({ type: 'TRACK_EVENT', payload: event });
  }, []);

  const currentStepDef = steps.find(s => s.id === state.currentStep);
  const isOnboardingActive = !state.skipped && !state.completedSteps.includes('complete');

  return (
    <OnboardingContext.Provider value={{
      state,
      dispatch,
      nextStep,
      prevStep,
      skipOnboarding,
      trackEvent,
      currentStepDef,
      isOnboardingActive,
    }}>
      {children}
    </OnboardingContext.Provider>
  );
}

export const useOnboarding = () => useContext(OnboardingContext);
