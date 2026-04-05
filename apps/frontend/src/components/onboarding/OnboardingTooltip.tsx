import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowRight, X } from 'lucide-react';

interface TooltipProps {
  target: string;
  content: string;
  onNext: () => void;
  onSkip: () => void;
  stepIndex: number;
  totalSteps: number;
}

export function OnboardingTooltip({ target, content, onNext, onSkip, stepIndex, totalSteps }: TooltipProps) {
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null);
  const [highlighted, setHighlighted] = useState(false);
  const targetRef = useRef<Element | null>(null);

  useEffect(() => {
    const el = document.querySelector(target);
    if (el) {
      targetRef.current = el;
      const rect = el.getBoundingClientRect();
      const tooltipWidth = 320;
      const tooltipHeight = 160;
      let left = rect.left;
      let top = rect.bottom + 12;

      if (left + tooltipWidth > window.innerWidth) {
        left = window.innerWidth - tooltipWidth - 16;
      }
      if (left < 16) left = 16;
      if (top + tooltipHeight > window.innerHeight) {
        top = rect.top - tooltipHeight - 12;
      }
      if (top < 16) top = 16;

      setPosition({ top, left });
      setHighlighted(true);
    }

    return () => setHighlighted(false);
  }, [target]);

  useEffect(() => {
    if (highlighted && targetRef.current && targetRef.current instanceof HTMLElement) {
      targetRef.current.style.outline = '2px solid rgba(6, 182, 212, 0.6)';
      targetRef.current.style.outlineOffset = '2px';
      targetRef.current.style.borderRadius = '8px';
      targetRef.current.style.transition = 'outline 0.3s ease';
    }
    return () => {
      if (targetRef.current && targetRef.current instanceof HTMLElement) {
        targetRef.current.style.outline = '';
        targetRef.current.style.outlineOffset = '';
        targetRef.current.style.borderRadius = '';
      }
    };
  }, [highlighted]);

  if (!position) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 8 }}
        className="fixed z-[9999]"
        style={{ top: position.top, left: position.left }}
      >
        <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl border border-slate-200 dark:border-slate-800 w-80 overflow-hidden">
          {/* Progress bar */}
          <div className="h-1 bg-slate-100 dark:bg-slate-800">
            <div
              className="h-full bg-cyan-500 transition-all duration-300"
              style={{ width: `${((stepIndex + 1) / totalSteps) * 100}%` }}
            />
          </div>

          <div className="p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-semibold text-cyan-600 dark:text-cyan-400 uppercase tracking-wider">
                Step {stepIndex + 1} of {totalSteps}
              </span>
              <button
                onClick={onSkip}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
            <p className="text-sm text-slate-700 dark:text-slate-300 leading-relaxed">{content}</p>
          </div>

          <div className="px-4 py-3 bg-slate-50 dark:bg-slate-800/50 border-t border-slate-100 dark:border-slate-800 flex items-center justify-between">
            <button
              onClick={onSkip}
              className="text-xs text-slate-500 hover:text-slate-700 dark:hover:text-slate-300 transition-colors"
            >
              Skip
            </button>
            <button
              onClick={onNext}
              className="flex items-center gap-1.5 px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-white font-medium rounded-lg transition-colors text-xs"
            >
              Next
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
