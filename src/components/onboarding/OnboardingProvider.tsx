import { createContext, useContext, useState, useEffect, type ReactNode } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { supabase } from '@/lib/supabase';

interface OnboardingContextType {
  step: number;
  completed: boolean;
  nextStep: () => void;
  prevStep: () => void;
  markComplete: () => void;
}

const OnboardingContext = createContext<OnboardingContextType>({
  step: 0,
  completed: false,
  nextStep: () => {},
  prevStep: () => {},
  markComplete: () => {},
});

export function OnboardingProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const [step, setStep] = useState(0);
  const [completed, setCompleted] = useState(false);

  useEffect(() => {
    if (!user) return;
    const saved = localStorage.getItem(`onboarding-${user.id}`);
    if (saved) {
      const data = JSON.parse(saved);
      setStep(data.step || 0);
      setCompleted(data.completed || false);
    }
  }, [user]);

  const saveState = (newStep: number, newCompleted: boolean) => {
    if (user) {
      localStorage.setItem(`onboarding-${user.id}`, JSON.stringify({ step: newStep, completed: newCompleted }));
    }
  };

  const nextStep = () => {
    const next = step + 1;
    setStep(next);
    saveState(next, completed);
  };

  const prevStep = () => {
    const prev = Math.max(0, step - 1);
    setStep(prev);
    saveState(prev, completed);
  };

  const markComplete = () => {
    setCompleted(true);
    saveState(step, true);
  };

  return (
    <OnboardingContext.Provider value={{ step, completed, nextStep, prevStep, markComplete }}>
      {children}
    </OnboardingContext.Provider>
  );
}

export const useOnboarding = () => useContext(OnboardingContext);
