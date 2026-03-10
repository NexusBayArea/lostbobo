import { cn } from '@/lib/utils';

interface SimHPCLogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  showText?: boolean;
}

export function SimHPCLogo({ className, size = 'md', showText = true }: SimHPCLogoProps) {
  const sizeClasses = {
    sm: { icon: 'w-8 h-8', text: 'text-lg' },
    md: { icon: 'w-10 h-10', text: 'text-xl' },
    lg: { icon: 'w-12 h-12', text: 'text-2xl' },
    xl: { icon: 'w-16 h-16', text: 'text-3xl' },
  };

  return (
    <div className={cn('flex items-center gap-3', className)}>
      {/* Logo Icon - Hexagonal mesh representing FEM/grid */}
      <div className={cn(
        'relative flex items-center justify-center',
        sizeClasses[size].icon
      )}>
        <svg
          viewBox="0 0 48 48"
          fill="none"
          xmlns="http://www.w3.org/2000/svg"
          className="w-full h-full"
        >
          {/* Outer hexagon */}
          <path
            d="M24 2L44 13.5V36.5L24 48L4 36.5V13.5L24 2Z"
            className="stroke-current"
            strokeWidth="2"
            fill="none"
          />
          {/* Inner mesh lines */}
          <path
            d="M24 2V48M4 13.5L44 36.5M44 13.5L4 36.5"
            className="stroke-current"
            strokeWidth="1.5"
            strokeOpacity="0.6"
          />
          {/* Center node */}
          <circle
            cx="24"
            cy="25"
            r="4"
            className="fill-current"
          />
          {/* Corner nodes */}
          <circle cx="24" cy="2" r="2.5" className="fill-current" />
          <circle cx="44" cy="13.5" r="2.5" className="fill-current" />
          <circle cx="44" cy="36.5" r="2.5" className="fill-current" />
          <circle cx="24" cy="48" r="2.5" className="fill-current" />
          <circle cx="4" cy="36.5" r="2.5" className="fill-current" />
          <circle cx="4" cy="13.5" r="2.5" className="fill-current" />
        </svg>
      </div>

      {/* Logo Text */}
      {showText && (
        <span className={cn(
          'font-bold tracking-tight',
          sizeClasses[size].text
        )}>
          <span className="text-inherit">Sim</span>
          <span className="text-blue-500">HPC</span>
        </span>
      )}
    </div>
  );
}

export function SimHPCLogoIcon({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={cn('w-10 h-10', className)}
    >
      <path
        d="M24 2L44 13.5V36.5L24 48L4 36.5V13.5L24 2Z"
        className="stroke-foreground"
        strokeWidth="2"
        fill="none"
      />
      <path
        d="M24 2V48M4 13.5L44 36.5M44 13.5L4 36.5"
        className="stroke-foreground"
        strokeWidth="1.5"
        strokeOpacity="0.6"
      />
      <circle cx="24" cy="25" r="4" className="fill-blue-500" />
      <circle cx="24" cy="2" r="2.5" className="fill-foreground" />
      <circle cx="44" cy="13.5" r="2.5" className="fill-foreground" />
      <circle cx="44" cy="36.5" r="2.5" className="fill-foreground" />
      <circle cx="24" cy="48" r="2.5" className="fill-foreground" />
      <circle cx="4" cy="36.5" r="2.5" className="fill-foreground" />
      <circle cx="4" cy="13.5" r="2.5" className="fill-foreground" />
    </svg>
  );
}
