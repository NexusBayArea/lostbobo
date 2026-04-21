import React, { useEffect } from 'react';
import ReactFlow, { 
  useNodesState, 
  useEdgesState, 
  Background, 
  Controls 
} from 'reactflow';
import 'reactflow/dist/style.css';
import { supabase } from '@/lib/supabase';

const LineageGraph = ({ runId }: { runId: string }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    const fetchLineage = async () => {
      const { data: traces, error } = await supabase
        .from('node_traces')
        .select('*')
        .eq('run_id', runId);

      if (error || !traces) return;

      const newNodes = traces.map((trace: any) => ({
        id: trace.id,
        data: { label: `${trace.node_id}` },
        position: { x: Math.random() * 400, y: Math.random() * 400 },
        style: { 
          background: '#3b82f6',
          color: '#fff',
          borderRadius: '8px'
        },
      }));

      const newEdges = traces.flatMap((trace: any) => 
        (trace.deps || []).map((depId: string) => ({
          id: `e-${depId}-${trace.id}`,
          source: depId,
          target: trace.id,
        }))
      );

      setNodes(newNodes);
      setEdges(newEdges);
    };

    fetchLineage();
  }, [runId, setNodes, setEdges]);

  return (
    <div className="h-[500px] w-full border rounded-xl bg-slate-50">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
};

export default LineageGraph;
