import { Sun, Moon } from 'lucide-react';
import { useTheme } from '@/hooks/useTheme';
import { cn } from '@/lib/utils';

interface ThemeToggleProps {
  className?: string;
  variant?: 'default' | 'ghost';
}

export function ThemeToggle({ className, variant = 'ghost' }: ThemeToggleProps) {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className={cn(
        'relative flex items-center justify-center w-10 h-10 rounded-xl transition-all duration-300',
        variant === 'ghost' && 'hover:bg-slate-100 dark:hover:bg-slate-800',
        variant === 'default' && 'bg-slate-100 dark:bg-slate-800 hover:bg-slate-200 dark:hover:bg-slate-700',
        className
      )}
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
    >
      <div className="relative w-5 h-5">
        <Sun
          className={cn(
            'absolute inset-0 w-5 h-5 transition-all duration-300',
            theme === 'dark' 
              ? 'opacity-0 rotate-90 scale-0' 
              : 'opacity-100 rotate-0 scale-100 text-slate-700'
          )}
        />
        <Moon
          className={cn(
            'absolute inset-0 w-5 h-5 transition-all duration-300',
            theme === 'light' 
              ? 'opacity-0 -rotate-90 scale-0' 
              : 'opacity-100 rotate-0 scale-100 text-slate-300'
          )}
        />
      </div>
    </button>
  );
}
