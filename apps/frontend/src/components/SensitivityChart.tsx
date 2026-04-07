import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { SensitivityEntry } from '@/types/simulation';

interface SensitivityChartProps {
  data: SensitivityEntry[];
  className?: string;
}

export function SensitivityChart({ data, className }: SensitivityChartProps) {
  // Sort by influence coefficient for better visualization
  const sortedData = [...data].sort((a, b) => b.influence_coefficient - a.influence_coefficient);

  return (
    <div className={className || "h-[300px] w-full pt-4"}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart layout="vertical" data={sortedData} margin={{ left: 40, right: 20 }}>
          <XAxis type="number" domain={[0, 1]} hide />
          <YAxis 
            dataKey="parameter_name" 
            type="category" 
            tick={{ fontSize: 12, fill: 'currentColor' }} 
            width={100} 
            axisLine={false}
            tickLine={false}
          />
          <Tooltip 
            cursor={{ fill: 'transparent' }}
            contentStyle={{ 
              borderRadius: '12px', 
              border: '1px solid #e2e8f0', 
              boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
              backgroundColor: 'rgba(255, 255, 255, 0.95)'
            }}
          />
          <Bar 
            dataKey="influence_coefficient" 
            radius={[0, 4, 4, 0]}
            barSize={24}
          >
            {sortedData.map((entry, index) => (
              <Cell 
                key={`cell-${index}`} 
                fill={entry.influence_coefficient > 0.7 ? '#3b82f6' : '#94a3b8'} 
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
