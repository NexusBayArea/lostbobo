import { useOnboarding } from './OnboardingProvider';
import { steps } from './steps';
import { OnboardingModal } from './OnboardingModal';
import { OnboardingTooltip } from './OnboardingTooltip';

export function StepRenderer() {
  const { state, nextStep, skipOnboarding, isOnboardingActive } = useOnboarding();

  if (!isOnboardingActive) return null;

  const step = steps.find(s => s.id === state.currentStep);
  if (!step) return null;

  const stepIndex = steps.indexOf(step);

  if (step.type === 'modal') {
    return (
      <OnboardingModal
        title={step.title || ''}
        content={step.content}
        onNext={nextStep}
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
