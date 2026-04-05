import { useState, useEffect } from 'react';
import { Network, Search, GitBranch, History } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/hooks/useAuth';
import { supabase } from '@/lib/supabase';
import { format } from 'date-fns';

interface LineageNode {
  id: string;
  scenario_name: string;
  status: string;
  created_at: string;
  parent_id?: string;
}

export function SimulationLineage() {
  const { user, getToken } = useAuth();
  const [lineage, setLineage] = useState<LineageNode[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchLineage = async () => {
    if (!user || !supabase) return;
    try {
      setLoading(true);
      await getToken(); // Ensure auth is ready
      const { data, error } = await supabase
        .from('simulations')
        .select('id, scenario_name, status, created_at')
        .eq('user_id', user.id)
        .order('created_at', { ascending: false })
        .limit(20);

      if (data) setLineage(data as LineageNode[]);
    } catch (error) {
      console.error('Failed to fetch lineage:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLineage();
    // Real-time updates for lineage
    if (!user || !supabase) return;
    const client = supabase;
    const channel = client.channel('lineage_updates')
      .on('postgres_changes', { event: '*', schema: 'public', table: 'simulations', filter: `user_id=eq.${user.id}` }, () => {
        fetchLineage();
      })
      .subscribe();
      
    return () => {
      client.removeChannel(channel);
    };
  }, [user?.id]);

  return (
    <Card className="bg-slate-900 border-slate-800 shadow-2xl h-full flex flex-col">
      <CardHeader className="py-4 border-b border-slate-800 flex flex-row items-center justify-between">
        <div className="flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-cyan-400" />
          <CardTitle className="text-xs uppercase font-bold text-slate-400">Design Ancestry Graph</CardTitle>
        </div>
        <History className="w-4 h-4 text-slate-700 hover:text-cyan-400 cursor-pointer transition-colors" onClick={fetchLineage} />
      </CardHeader>
      <CardContent className="flex-1 p-0 overflow-y-auto">
        {loading && lineage.length === 0 ? (
          <div className="p-8 text-center text-slate-600 animate-pulse text-[10px] uppercase font-bold">Mapping Structural Nodes...</div>
        ) : lineage.length === 0 ? (
          <div className="p-12 text-center text-slate-700 italic text-[10px] uppercase">No Historical Design Ancestry Detected</div>
        ) : (
          <div className="p-4 space-y-6">
             <div className="relative">
                <div className="absolute left-2 top-2 bottom-0 w-px bg-slate-800" />
                <div className="space-y-6">
                   {lineage.map((node, i) => (
                     <div key={node.id} className="relative pl-8 group">
                        <div className={`absolute left-0 top-1.5 w-4 h-4 rounded-full border-2 border-slate-900 transition-all ${
                          node.status === 'completed' ? 'bg-cyan-500 scale-100 group-hover:scale-125 shadow-[0_0_10px_rgba(34,211,238,0.5)]' : 
                          node.status === 'running' ? 'bg-amber-400 animate-pulse' : 'bg-slate-700'
                        }`} />
                        <div className="bg-slate-950/50 p-3 rounded-lg border border-slate-800 group-hover:border-slate-700 transition-all">
                           <div className="flex items-center justify-between mb-1">
                              <span className="text-[10px] font-mono text-slate-500 uppercase">T+{format(new Date(node.created_at), 'HH:mm:ss')}</span>
                              <Badge variant="outline" className={`text-[8px] border-none px-1 h-3.5 uppercase font-bold ${
                                node.status === 'completed' ? 'text-cyan-400 bg-cyan-400/5' : 'text-slate-500 bg-slate-500/5'
                              }`}>
                                {node.status}
                              </Badge>
                           </div>
                           <p className="text-xs font-bold text-white mb-1 truncate">{node.scenario_name}</p>
                           <p className="text-[10px] font-mono text-slate-600 truncate">{node.id}</p>
                        </div>
                     </div>
                   ))}
                </div>
             </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
