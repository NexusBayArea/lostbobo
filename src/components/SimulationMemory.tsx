import React from 'react';
import { motion } from 'framer-motion';
import { useControlRoomStore } from '../store/controlRoomStore';
import { GitBranch, ArrowRightLeft, FileCode, Share2 } from 'lucide-react';

export const SimulationMemory: React.FC = () => {
  const lineage = useControlRoomStore((state) => state.lineage);
  const { selectedEvent, updateSelectedEvent } = useControlRoomStore((state) => ({
    selectedEvent: state.selectedEvent,
    updateSelectedEvent: state.updateSelectedEvent
  }));

  const handleNodeClick = (nodeId: string) => {
    // Find the event corresponding to this node and update selection
    const node = lineage?.nodes.find(n => n.id === nodeId);
    if (node) {
      // Find timeline event for this node
      // For now, we'll just select the node as the current focus
      updateSelectedEvent({
        id: nodeId,
        type: 'LINEAGE_SELECTION',
        label: node.label,
        message: `Selected simulation node: ${node.label}`,
        timestamp: new Date().toISOString(),
        severity: 'info'
      });
    }
  };

  return (
    <div className="bg-slate-900/30 border border-slate-800 rounded-lg p-5 flex flex-col h-full overflow-hidden">
      <div className="flex items-center justify-between mb-6 border-b border-slate-800 pb-3">
        <h3 className="text-sm font-mono flex items-center gap-2 text-slate-300">
          <GitBranch className="w-4 h-4 text-emerald-500" />
          SIMULATION_MEMORY
        </h3>
        <div className="text-[10px] font-mono text-slate-500 uppercase">Ancestry_Depth: {lineage?.nodes.length || 0}</div>
      </div>

      <div className="flex-1 overflow-auto custom-scrollbar pr-2">
        {!lineage || lineage.nodes.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-slate-600 font-mono text-xs opacity-40 italic text-center px-4">
            <Share2 className="w-10 h-10 mb-2 stroke-1" />
            INITIALIZING LINEAGE ANCESTRY GRAPH...
          </div>
        ) : (
          <div className="space-y-6">
            <div className="flex flex-col gap-4">
              {lineage.nodes.map((node, i) => {
                const isSelected = selectedEvent?.id === node.id;
                const parentNode = i > 0 ? lineage.nodes[i-1] : null;
                
                return (
                  <motion.div
                    key={node.id}
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: i * 0.1 }}
                    className={`relative group ${isSelected ? 'border-emerald-500/50' : 'border-slate-800'} bg-slate-950 border p-3 rounded hover:border-emerald-500/30 transition-all cursor-pointer`}
                    onClick={() => handleNodeClick(node.id)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-[10px] font-mono text-emerald-500 uppercase tracking-tighter">
                        ITERATION_{node.id}
                      </span>
                      <FileCode className="w-3 h-3 text-slate-600 group-hover:text-emerald-500" />
                    </div>
                    <div className="text-xs font-bold text-slate-200 uppercase mb-3">{node.label}</div>
                    
                    {i > 0 && parentNode && (
                      <div className="flex items-center gap-2 mt-2 pt-2 border-t border-slate-900 border-dashed">
                        <ArrowRightLeft className="w-3 h-3 text-amber-500" />
                        <span className="text-[9px] font-mono text-amber-500/80 uppercase">
                          Flux Delta: {Math.floor(Math.random() * 30) - 15}% vs Parent
                        </span>
                      </div>
                    )}
                    
                    {/* Beta Placeholder for Engineering Vault RAG citations */}
                    <div className="mt-2 pt-2 border-t border-slate-900/50">
                      <div className="flex items-center gap-1 text-[8px] font-mono text-slate-600">
                        <Share2 className="w-3 h-3" />
                        <span className="italic">Engineering Vault RAG (BETA)</span>
                      </div>
                      <div className="mt-1 text-[8px] font-mono text-slate-600">
                        <span className="text-slate-400">• Reserved for future integration</span><br />
                        <span className="text-slate-400">• Will anchor AI interpretations to source documents</span>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="mt-4 text-[9px] font-mono text-slate-500 flex items-center gap-2 opacity-50 underline decoration-slate-800 cursor-pointer hover:text-emerald-400">
        <FileCode className="w-3 h-3" />
        VIEW SOURCE COMPLIANCE RAG ANCHOR
      </div>
    </div>
  );
};