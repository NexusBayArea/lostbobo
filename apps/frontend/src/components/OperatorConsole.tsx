import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Terminal, Zap, ShieldAlert, RotateCcw } from 'lucide-react';

export function OperatorConsole() {
  return (
    <Card className="h-full bg-slate-900/80 border-slate-800">
      <CardHeader className="pb-2">
        <CardTitle className="text-xs font-black text-slate-500 uppercase tracking-[0.2em] flex items-center gap-2">
          <Terminal className="w-3 h-3 text-cyan-400" />
          Operator Console
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="bg-slate-950 rounded-lg p-3 font-mono text-[10px] text-cyan-400 border border-slate-800">
          <div>$ simhpc status --live</div>
          <div className="text-slate-500">&gt; All systems operational</div>
        </div>
        <div className="grid grid-cols-2 gap-2">
          <Button size="sm" className="text-[10px] h-8 bg-cyan-500/10 hover:bg-cyan-500/20 text-cyan-400 border border-cyan-500/20">
            <Zap className="w-3 h-3 mr-1" />
            Inject
          </Button>
          <Button size="sm" className="text-[10px] h-8 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 border border-amber-500/20">
            <ShieldAlert className="w-3 h-3 mr-1" />
            Abort
          </Button>
          <Button size="sm" className="text-[10px] h-8 col-span-2 bg-slate-800 hover:bg-slate-700 text-slate-400">
            <RotateCcw className="w-3 h-3 mr-1" />
            Reset State
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
