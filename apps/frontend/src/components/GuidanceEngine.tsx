import { useState } from 'react';
import { MessageSquare, Sparkles, AlertCircle, TrendingUp, ShieldCheck, Loader2, ArrowRight } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent, CardDescription, CardFooter } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';
import { useAuth } from '@/hooks/useAuth';
import { toast } from 'sonner';

export function GuidanceEngine() {
  const { getToken } = useAuth();
  const [loading, setLoading] = useState(false);
  const [insight, setInsight] = useState<any>(null);

  const fetchGuidance = async () => {
    setLoading(true);
    try {
      const token = await getToken();
      // This would normally call api.generateReport for a specific run
      // For now, providing a high-quality mock response
      await new Promise(resolve => setTimeout(resolve, 1500));
      setInsight({
        recommendation: "Increase solver relative tolerance to 1e-6 to bypass stiff convergence drift in Thermal-Channel-01.",
        confidence: 0.94,
        threat_level: "low",
        impact: "Reduces compute cost by 14% with <1.2% loss in accuracy."
      });
      toast.success('MERCURY AI guidance updated.');
    } catch (error) {
      toast.error('Failed to update guidance.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="bg-slate-900 border-slate-800 shadow-2xl h-full flex flex-col group">
      <CardHeader className="py-4 border-b border-slate-800 flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-cyan-400 group-hover:scale-110 transition-transform" />
          <CardTitle className="text-xs uppercase font-bold text-slate-400 font-mono">Mercury Guidance Engine</CardTitle>
        </div>
        {!insight && !loading && (
           <Badge variant="outline" className="border-red-500/30 text-red-500 bg-red-500/5 px-1.5 font-mono text-[10px]">
             ANALYSIS OFFLINE
           </Badge>
        )}
      </CardHeader>
      <CardContent className="flex-1 p-6 flex flex-col items-center justify-center text-center">
        {loading ? (
          <div className="space-y-4 flex flex-col items-center">
             <Loader2 className="w-8 h-8 text-cyan-400 animate-spin" />
             <p className="text-[10px] text-slate-500 uppercase font-black tracking-widest animate-pulse">Running Neural Inference...</p>
          </div>
        ) : insight ? (
          <div className="space-y-6 text-left">
             <div className="flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
                <p className="text-sm font-medium text-white leading-relaxed">{insight.recommendation}</p>
             </div>
             
             <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-slate-950/50 rounded-xl border border-slate-800">
                   <p className="text-[8px] uppercase font-bold text-slate-500 mb-1">Confidence</p>
                   <p className="text-lg font-mono text-cyan-400">{(insight.confidence * 100).toFixed(0)}%</p>
                </div>
                <div className="p-3 bg-slate-950/50 rounded-xl border border-slate-800">
                   <p className="text-[8px] uppercase font-bold text-slate-500 mb-1">Impact</p>
                   <TrendingUp className="w-4 h-4 text-green-400" />
                </div>
             </div>
             
             <div className="p-4 bg-cyan-500/5 rounded-xl border border-cyan-500/20">
                <p className="text-[10px] font-bold text-cyan-400 uppercase mb-2">AI Reasoning</p>
                <p className="text-xs text-slate-400 italic">{insight.impact}</p>
             </div>
          </div>
        ) : (
          <div className="space-y-6 py-8">
             <div className="w-16 h-16 bg-slate-800/30 rounded-full flex items-center justify-center mx-auto opacity-50 group-hover:opacity-100 transition-opacity">
                <ShieldCheck className="w-8 h-8 text-slate-600 group-hover:text-cyan-500 transition-colors" />
             </div>
             <div>
                <p className="text-xs text-slate-500 font-bold uppercase mb-2">Mercury AI Standby</p>
                <p className="text-[10px] text-slate-600 px-6 italic">Select and analyze a live design to generate corrective engineering guidance.</p>
             </div>
          </div>
        )}
      </CardContent>
      <CardFooter className="p-4 border-t border-slate-800/50 flex gap-2">
         <Button 
            className="flex-1 h-8 text-[10px] font-bold uppercase tracking-widest bg-cyan-600 hover:bg-cyan-500 text-slate-950" 
            onClick={fetchGuidance}
            disabled={loading}
          >
            {loading ? 'INFERRING...' : insight ? 'REFRESH INSIGHTS' : 'RUN NVIDIA INFERENCE'}
         </Button>
         <Button variant="outline" className="h-8 border-slate-800 bg-slate-950 text-slate-500 hover:text-white" disabled={!insight}>
            <ArrowRight className="w-3 h-3" />
         </Button>
      </CardFooter>
    </Card>
  );
}
