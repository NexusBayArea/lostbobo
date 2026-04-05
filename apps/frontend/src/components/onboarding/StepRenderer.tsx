import { useOnboarding } from './OnboardingProvider';
import { steps } from './steps';
import { OnboardingModal } from './OnboardingModal';
import { OnboardingTooltip } from './OnboardingTooltip';

export function StepRenderer() {
  const { state, nextStep, skipOnboarding, isOnboardingActive, dispatch } = useOnboarding();

  if (!isOnboardingActive) return null;

  const step = steps.find(s => s.id === state.currentStep);
  if (!step) return null;

  const stepIndex = steps.indexOf(step);

  const handleComplete = () => {
    dispatch({ type: 'SET_STEP', payload: 'complete' });
    dispatch({ type: 'SKIP' });
  };

  if (step.type === 'modal') {
    return (
      <OnboardingModal
        title={step.title || ''}
        content={step.content}
        onNext={step.id === 'complete' ? handleComplete : nextStep}
        onSkip={skipOnboarding}
        cta={step.cta}
      />
    );
  }

  if (step.type === 'tooltip') {
    return (
      <OnboardingTooltip
        target={step.target || ''}
        content={step.content}
        onNext={nextStep}
        onSkip={skipOnboarding}
        stepIndex={stepIndex}
        totalSteps={steps.length}
      />
    );
  }

  return null;
}
