import { useEffect, useRef } from 'react';
import { useTheme } from '@/hooks/useTheme';

export function ConfidenceGraph() {
  const svgRef = useRef<SVGSVGElement>(null);
  const { theme } = useTheme();

  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;

    const paths = svg.querySelectorAll('.animate-draw');
    paths.forEach((path) => {
      const length = (path as SVGPathElement).getTotalLength?.() || 1000;
      (path as SVGPathElement).style.strokeDasharray = `${length}`;
      (path as SVGPathElement).style.strokeDashoffset = `${length}`;
      
      // Trigger animation
      setTimeout(() => {
        (path as SVGPathElement).style.transition = 'stroke-dashoffset 2s ease-out';
        (path as SVGPathElement).style.strokeDashoffset = '0';
      }, 500);
    });
  }, []);

  const isDark = theme === 'dark';
  const primaryColor = isDark ? '#60A5FA' : '#3B82F6';
  const secondaryColor = isDark ? '#34D399' : '#10B981';
  const bandColor = isDark ? 'rgba(96, 165, 250, 0.15)' : 'rgba(59, 130, 246, 0.12)';
  const textColor = isDark ? '#94A3B8' : '#64748B';

  return (
    <svg
      ref={svgRef}
      viewBox="0 0 400 200"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className="w-full h-auto"
    >
      {/* Grid lines */}
      <g className="opacity-30">
        {[0, 50, 100, 150, 200].map((y) => (
          <line
            key={`h-${y}`}
            x1="0"
            y1={y}
            x2="400"
            y2={y}
            stroke={textColor}
            strokeWidth="0.5"
            strokeDasharray="4 4"
          />
        ))}
        {[0, 100, 200, 300, 400].map((x) => (
          <line
            key={`v-${x}`}
            x1={x}
            y1="0"
            x2={x}
            y2="200"
            stroke={textColor}
            strokeWidth="0.5"
            strokeDasharray="4 4"
          />
        ))}
      </g>

      {/* Confidence band area */}
      <path
        d="M0 120 Q50 110 100 100 T200 80 T300 70 T400 60 L400 140 Q350 130 300 120 T200 110 T100 100 T0 120Z"
        fill={bandColor}
        className="animate-fade-in"
        style={{ animationDelay: '0.5s', animationDuration: '1s' }}
      />

      {/* Upper confidence bound */}
      <path
        className="animate-draw"
        d="M0 100 Q50 90 100 80 T200 60 T300 50 T400 40"
        stroke={primaryColor}
        strokeWidth="2"
        strokeLinecap="round"
        fill="none"
        strokeOpacity="0.5"
      />

      {/* Lower confidence bound */}
      <path
        className="animate-draw"
        d="M0 140 Q50 130 100 120 T200 100 T300 90 T400 80"
        stroke={primaryColor}
        strokeWidth="2"
        strokeLinecap="round"
        fill="none"
        strokeOpacity="0.5"
      />

      {/* Main simulation curve */}
      <path
        className="animate-draw"
        d="M0 120 Q50 110 100 100 T200 80 T300 70 T400 60"
        stroke={secondaryColor}
        strokeWidth="3"
        strokeLinecap="round"
        fill="none"
      />

      {/* Data points */}
      {[
        { x: 100, y: 100 },
        { x: 200, y: 80 },
        { x: 300, y: 70 },
        { x: 400, y: 60 },
      ].map((point, i) => (
        <circle
          key={i}
          cx={point.x}
          cy={point.y}
          r="5"
          fill={secondaryColor}
          className="animate-fade-in"
          style={{ animationDelay: `${1.5 + i * 0.2}s` }}
        />
      ))}

      {/* Labels */}
      <text
        x="380"
        y="30"
        fill={textColor}
        fontSize="10"
        fontFamily="system-ui"
      >
        +σ
      </text>
      <text
        x="380"
        y="75"
        fill={secondaryColor}
        fontSize="10"
        fontFamily="system-ui"
        fontWeight="500"
      >
        μ
      </text>
      <text
        x="380"
        y="105"
        fill={textColor}
        fontSize="10"
        fontFamily="system-ui"
      >
        -σ
      </text>

      {/* Confidence interval label */}
      <text
        x="200"
        y="185"
        fill={textColor}
        fontSize="11"
        fontFamily="system-ui"
        textAnchor="middle"
      >
        Confidence Interval: ±95%
      </text>
    </svg>
  );
}
