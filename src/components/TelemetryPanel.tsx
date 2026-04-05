import { useState, useEffect } from 'react';
import { Activity, Cpu, Database, Network } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

export function TelemetryPanel() {
  const [data, setData] = useState<any[]>([]);

  useEffect(() => {
    // Generate mock telemetry for the cockpit
    const interval = setInterval(() => {
      setData(prev => {
        const next = [...prev, {
          time: new Date().toLocaleTimeString(),
          gpu: 40 + Math.random() * 20,
          convergence: 0.1 + Math.random() * 0.5,
          error: 0.05 + Math.random() * 0.1
        }].slice(-20);
        return next;
      });
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Card className="bg-slate-900 border-slate-800 shadow-2xl h-full flex flex-col">
       <CardHeader className="py-4 border-b border-slate-800 flex flex-row items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            <CardTitle className="text-xs uppercase font-bold text-slate-400 font-mono">Live Simulation Telemetry</CardTitle>
          </div>
          <div className="flex items-center gap-4 text-[10px] font-mono">
             <div className="flex items-center gap-1">
                <div className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
                <span className="text-slate-500 uppercase">GPU Load</span>
             </div>
             <div className="flex items-center gap-1">
                <div className="w-1.5 h-1.5 rounded-full bg-amber-400" />
                <span className="text-slate-500 uppercase">Convergence</span>
             </div>
          </div>
       </CardHeader>
       <CardContent className="flex-1 p-0 overflow-hidden bg-slate-950/20">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 20, right: 30, left: -20, bottom: 20 }}>
               <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
               <XAxis 
                  dataKey="time" 
                  hide 
               />
               <YAxis 
                  domain={[0, 100]} 
                  axisLine={false} 
                  tickLine={false} 
                  tick={{ fontSize: 8, fill: '#64748b' }} 
               />
               <Tooltip 
                  contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', fontSize: '10px' }}
                  itemStyle={{ fontSize: '10px' }}
               />
               <Line 
                  type="monotone" 
                  dataKey="gpu" 
                  stroke="#22d3ee" 
                  strokeWidth={2} 
                  dot={false} 
                  isAnimationActive={false}
               />
               <Line 
                  type="monotone" 
                  dataKey="convergence" 
                  stroke="#fbbf24" 
                  strokeWidth={2} 
                  dot={false} 
                  isAnimationActive={false}
               />
            </LineChart>
          </ResponsiveContainer>
       </CardContent>
    </Card>
  );
}
