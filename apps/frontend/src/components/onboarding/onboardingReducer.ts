export interface OnboardingState {
  currentStep: string;
  completedSteps: string[];
  events: string[];
  skipped: boolean;
  version: number;
}

export const initialState: OnboardingState = {
  currentStep: 'welcome',
  completedSteps: [],
  events: [],
  skipped: false,
  version: 1,
};

export type OnboardingAction =
  | { type: 'SET_STEP'; payload: string }
  | { type: 'TRACK_EVENT'; payload: string }
  | { type: 'SKIP' }
  | { type: 'HYDRATE'; payload: Partial<OnboardingState> }
  | { type: 'RESET' };

export function onboardingReducer(state: OnboardingState, action: OnboardingAction): OnboardingState {
  switch (action.type) {
    case 'SET_STEP': {
      const completed = state.currentStep && !state.completedSteps.includes(state.currentStep)
        ? [...state.completedSteps, state.currentStep]
        : state.completedSteps;
      return {
        ...state,
        currentStep: action.payload,
        completedSteps: completed,
        version: state.version + 1,
      };
    }
    case 'TRACK_EVENT':
      return {
        ...state,
        events: state.events.includes(action.payload)
          ? state.events
          : [...state.events, action.payload],
        version: state.version + 1,
      };
    case 'SKIP':
      return { ...state, skipped: true, version: state.version + 1 };
    case 'HYDRATE':
      return { ...state, ...action.payload };
    case 'RESET':
      return { ...initialState };
    default:
      return state;
  }
}
