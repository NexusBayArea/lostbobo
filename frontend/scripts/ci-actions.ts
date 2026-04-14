export type CIAction = "FAST" | "BALANCED" | "FULL";

export const Actions: CIAction[] = ["FAST", "BALANCED", "FULL"];

export const ActionConfig: Record<CIAction, { cacheDag: boolean; typecheck: boolean; fullBuild: boolean }> = {
  FAST: { cacheDag: true, typecheck: false, fullBuild: false },
  BALANCED: { cacheDag: true, typecheck: true, fullBuild: false },
  FULL: { cacheDag: false, typecheck: true, fullBuild: true },
};