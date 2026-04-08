import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Sparkles, ChevronRight, Lightbulb } from 'lucide-react';

export function GuidanceEngine() {
  const suggestions = [
    { text: 'GPU utilization at 87% - consider batch processing', type: 'optimization' },
    { text: '3 simulations completed successfully', type: 'status' },
    { text: 'Temperature stable at 67°C', type: 'status' },
  ];

  return (
    <Card className="h-full bg-slate-900/80 border-slate-800">
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-black text-slate-500 uppercase tracking-[0.2em] flex items-center gap-2">
          <Sparkles className="w-3 h-3 text-cyan-400" />
          Guidance Engine
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        {suggestions.map((s, i) => (
          <div key={i} className="bg-slate-800/30 rounded-lg p-2 border border-slate-700/30 flex items-start gap-2">
            <Lightbulb className="w-3 h-3 text-amber-400 mt-0.5 flex-shrink-0" />
            <span className="text-[10px] text-slate-300">{s.text}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}
