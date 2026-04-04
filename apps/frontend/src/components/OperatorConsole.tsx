import { useState } from 'react';
import { ShieldAlert, RefreshCw, Zap, CheckCircle2, Loader2, Terminal, AlertCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { toast } from 'sonner';

export function OperatorConsole() {
  const { getToken } = useAuth();
  const [loading, setLoading] = useState<string | null>(null);

  const handleCommand = async (command: string) => {
    setLoading(command);
    try {
      const token = await getToken();
      // Placeholder for command execution until backend is fully verified
      await new Promise(resolve => setTimeout(resolve, 800));
      toast.success(`SYSTEM COMMAND ACCEPTED: [${command.toUpperCase()}] broadcasted to GPU fleet.`);
    } catch (error: any) {
      toast.error(error.message || `Failed to execute ${command}`);
    } finally {
      setLoading(null);
    }
  };

  return (
    <Card className="bg-slate-900 border-slate-800 shadow-2xl h-full flex flex-col">
       <CardHeader className="py-4 border-b border-slate-800">
          <CardTitle className="text-xs uppercase font-bold text-slate-400 flex items-center gap-2">
             <Terminal className="w-3 h-3 text-red-500" /> [4] Operator Commands
          </CardTitle>
       </CardHeader>
       <CardContent className="flex-1 p-4 grid grid-cols-2 gap-3">
          <button 
            onClick={() => handleCommand('intercept')}
            disabled={!!loading}
            className="h-full border border-red-500/30 bg-red-500/5 rounded-lg flex flex-col items-center justify-center gap-2 group hover:bg-red-500/10 transition-all active:scale-95 disabled:opacity-50"
          >
             {loading === 'intercept' ? <Loader2 className="w-4 h-4 text-red-500 animate-spin" /> : <ShieldAlert className="w-4 h-4 text-red-500 group-hover:scale-110 transition-transform" />}
             <span className="text-[10px] font-black uppercase text-red-500/70 group-hover:text-red-500 transition-colors tracking-[0.2em]">Intercept</span>
          </button>
          
          <button 
            onClick={() => handleCommand('clone')}
            disabled={!!loading}
            className="h-full border border-cyan-500/30 bg-cyan-500/5 rounded-lg flex flex-col items-center justify-center gap-2 group hover:bg-cyan-500/10 transition-all active:scale-95 disabled:opacity-50"
          >
             {loading === 'clone' ? <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" /> : <RefreshCw className="w-4 h-4 text-cyan-400 group-hover:rotate-180 transition-transform duration-500" />}
             <span className="text-[10px] font-black uppercase text-cyan-500/70 group-hover:text-cyan-400 transition-colors tracking-[0.2em]">Clone</span>
          </button>
          
          <button 
            onClick={() => handleCommand('boost')}
            disabled={!!loading}
            className="h-full border border-amber-500/30 bg-amber-500/5 rounded-lg flex flex-col items-center justify-center gap-2 group hover:bg-amber-500/10 transition-all active:scale-95 disabled:opacity-50"
          >
             {loading === 'boost' ? <Loader2 className="w-4 h-4 text-amber-500 animate-spin" /> : <Zap className="w-4 h-4 text-amber-500 group-hover:scale-110 transition-transform" />}
             <span className="text-[10px] font-black uppercase text-amber-500/70 group-hover:text-amber-500 transition-colors tracking-[0.2em]">Boost</span>
          </button>
          
          <button 
            onClick={() => handleCommand('certify')}
            disabled={!!loading}
            className="h-full border border-green-500/30 bg-green-500/5 rounded-lg flex flex-col items-center justify-center gap-2 group hover:bg-green-500/10 transition-all active:scale-95 disabled:opacity-50"
          >
             {loading === 'certify' ? <Loader2 className="w-4 h-4 text-green-500 animate-spin" /> : <CheckCircle2 className="w-4 h-4 text-green-500 group-hover:scale-110 transition-transform" />}
             <span className="text-[10px] font-black uppercase text-green-500/70 group-hover:text-green-500 transition-colors tracking-[0.2em]">Certify</span>
          </button>
       </CardContent>
       <CardFooter className="px-6 py-2 border-t border-slate-800/50 bg-slate-950/20 text-[8px] text-slate-700 italic flex justify-center">
          HIGH STAKES INTERVENTIONS REQUIRE OPERATOR CLEARANCE
       </CardFooter>
    </Card>
  );
}
