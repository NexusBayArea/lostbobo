import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Checks if a heartbeat timestamp is within the 'Healthy' threshold.
 * Matches the 15-minute logic in resource_reaper.py
 */
export const isPingRecent = (lastPing: string | null | undefined, thresholdMinutes = 15): boolean => {
  if (!lastPing) return false;

  const pingDate = new Date(lastPing);
  const now = new Date();
  
  // Calculate difference in minutes
  const diffInMs = now.getTime() - pingDate.getTime();
  const diffInMins = diffInMs / (1000 * 60);

  return diffInMins < thresholdMinutes;
};

/**
 * Formats the timestamp into a short, scannable string for the Admin UI.
 */
export const formatPing = (lastPing: string | null | undefined): string => {
  if (!lastPing) return 'NEVER';

  const pingDate = new Date(lastPing);
  const now = new Date();
  const diffInSecs = Math.floor((now.getTime() - pingDate.getTime()) / 1000);

  if (diffInSecs < 60) return 'JUST NOW';
  if (diffInSecs < 3600) return \\m ago\;
  if (diffInSecs < 86400) return \\h ago\;
  
  return pingDate.toLocaleDateString([], { month: 'short', day: 'numeric' });
};
