import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { GitBranch, Clock, ChevronRight } from 'lucide-react';

export function SimulationLineage() {
  const lineage = [
    { id: 1, name: 'baseline_v2.1', time: '14:32:01', status: 'completed' },
    { id: 2, name: 'baseline_v2.1_perturbed', time: '14:35:22', status: 'completed' },
    { id: 3, name: 'baseline_v2.2', time: '14:42:18', status: 'completed' },
  ];

  return (
    <Card className="h-full bg-slate-900/80 border-slate-800">
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-black text-slate-500 uppercase tracking-[0.2em] flex items-center gap-2">
          <GitBranch className="w-3 h-3 text-cyan-400" />
          Simulation Lineage
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          {lineage.map((item, i) => (
            <div key={item.id} className="flex items-center gap-2">
              <div className="flex flex-col items-center">
                <div className="w-2 h-2 rounded-full bg-cyan-400" />
                {i < lineage.length - 1 && <div className="w-0.5 h-8 bg-slate-700" />}
              </div>
              <div className="flex-1 bg-slate-800/50 rounded-lg p-2 border border-slate-700/50 flex items-center justify-between">
                <div>
                  <span className="text-xs font-mono text-white">{item.name}</span>
                  <div className="flex items-center gap-1 text-[8px] text-slate-500 mt-0.5">
                    <Clock className="w-2 h-2" />
                    {item.time}
                  </div>
                </div>
                <Badge variant="outline" className="text-[8px] h-5 text-green-400 border-green-500/30">
                  {item.status}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
