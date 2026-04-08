import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Activity, Cpu, Zap, Gauge, Thermometer } from 'lucide-react';

export function TelemetryPanel() {
  return (
    <Card className="h-full bg-slate-900/80 border-slate-800">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xs font-black text-slate-500 uppercase tracking-[0.2em] flex items-center gap-2">
            <Activity className="w-3 h-3 text-cyan-400" />
            Live Telemetry
          </CardTitle>
          <Badge variant="outline" className="text-[8px] border-green-500/30 text-green-400 bg-green-400/5">
            LIVE
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          {[
            { label: 'GPU UTIL', value: '87%', icon: Gauge, color: 'text-cyan-400' },
            { label: 'MEMORY', value: '42GB', icon: Cpu, color: 'text-purple-400' },
            { label: 'TEMP', value: '67°C', icon: Thermometer, color: 'text-amber-400' },
            { label: 'POWER', value: '350W', icon: Zap, color: 'text-green-400' },
          ].map((metric) => (
            <div key={metric.label} className="bg-slate-800/50 rounded-lg p-3 border border-slate-700/50">
              <div className="flex items-center justify-between mb-1">
                <span className="text-[8px] text-slate-500 uppercase tracking-wider">{metric.label}</span>
                <metric.icon className={`w-3 h-3 ${metric.color}`} />
              </div>
              <span className="text-lg font-mono text-white">{metric.value}</span>
            </div>
          ))}
        </div>
        <div className="h-32 bg-slate-800/30 rounded-lg border border-slate-700/50 p-2 flex items-end gap-0.5">
          {[65, 78, 45, 89, 72, 91, 68, 84, 76, 88, 95, 82].map((h, i) => (
            <div key={i} className="flex-1 bg-cyan-500/60 rounded-t-sm" style={{ height: `${h}%` }} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
