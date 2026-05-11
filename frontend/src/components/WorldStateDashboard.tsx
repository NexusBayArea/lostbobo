import React, { useEffect, useState } from 'react';
import ReactFlow, {
  Node,
  Edge,
  Controls,
  MiniMap,
  Background,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';

interface WorldState {
  timestamp: number;
  causal_id: string;
  regime: string;
  entropy: number;
  entities: any[];
  graph: {
    nodes: any[];
    edges: any[];
  };
  event_stream: any[];
}

interface CausalAnomaly {
  anomaly_id: string;
  anomaly_type: string;
  severity: string;
  description: string;
  affected_entity_keys: string[];
  confidence: number;
  timestamp: number;
}

const WorldStateDashboard: React.FC = () => {
  const [worldState, setWorldState] = useState<WorldState | null>(null);
  const [anomalies, setAnomalies] = useState<CausalAnomaly[]>([]);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch('/api/v1/core/world-state-graph');
        const data = await response.json();
        setWorldState(data);

        if (data.graph?.nodes) {
          setNodes(
            data.graph.nodes.map((n: any) => ({
              id: n.id || n.entity_id,
              position: n.position || { x: Math.random() * 800, y: Math.random() * 600 },
              data: { label: `${n.type || 'entity'}:${n.name || n.id}` },
              type: 'default',
            }))
          );
          setEdges(data.graph.edges || []);
        }
      } catch (error) {
        console.error('Failed to fetch world state:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const fetchAnomalies = async () => {
      try {
        const response = await fetch('/api/v1/core/anomalies');
        const data = await response.json();
        setAnomalies(data);
      } catch (error) {
        console.error('Failed to fetch anomalies:', error);
      }
    };

    fetchAnomalies();
    const interval = setInterval(fetchAnomalies, 10000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const eventSource = new EventSource('/api/v1/core/world-state/stream');
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setWorldState((prev) => ({ ...prev, ...data }));
      if (data.graph?.nodes) {
        setNodes(
          data.graph.nodes.map((n: any) => ({
            id: n.id || n.entity_id,
            position: n.position || { x: Math.random() * 800, y: Math.random() * 600 },
            data: { label: `${n.type || 'entity'}:${n.name || n.id}` },
            type: 'default',
          }))
        );
        setEdges(data.graph.edges || []);
      }
    };
    return () => eventSource.close();
  }, []);

  const regimeColor =
    worldState?.regime === 'normal' ? 'text-emerald-400' :
    worldState?.regime === 'panic' ? 'text-red-400' : 'text-amber-400';

  const severityClass = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'text-red-400';
      case 'high':
        return 'text-orange-400';
      case 'medium':
        return 'text-yellow-400';
      default:
        return 'text-gray-400';
    }
  };

  return (
    <div className="h-screen flex flex-col bg-gray-950 text-white p-4 gap-4">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">SimHPC WorldState Live</h1>
        <div className="flex gap-6">
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
            <div className="text-gray-400 text-sm">Regime</div>
            <div className={`text-2xl font-bold ${regimeColor}`}>
              {worldState?.regime?.toUpperCase() || 'NORMAL'}
            </div>
          </div>
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
            <div className="text-gray-400 text-sm">Entropy</div>
            <div className="text-2xl font-bold">{worldState?.entropy?.toFixed(3) || '0.000'}</div>
          </div>
          <div className="bg-gray-900 rounded-lg p-4 border border-gray-700">
            <div className="text-gray-400 text-sm">Causal ID</div>
            <div className="font-mono text-sm text-gray-300">
              {worldState?.causal_id?.slice(0, 12)}...
            </div>
          </div>
        </div>
      </div>

      <div className="flex-1 border border-gray-700 rounded-xl overflow-hidden">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          fitView
        >
          <Controls />
          <MiniMap />
          <Background variant="dots" gap={12} size={1} />
        </ReactFlow>
      </div>

      <div className="flex gap-4">
        <button
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium transition-colors"
          onClick={() => console.log('Temporal replay')}
        >
          Temporal Replay
        </button>
        <button
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium transition-colors"
          onClick={() => console.log('zk-SNARK proof')}
        >
          Prove with zk-SNARK
        </button>
        <button
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium transition-colors"
          onClick={() => console.log('Bulletproof')}
        >
          Prove with Bulletproof
        </button>
        <button
          className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg font-medium transition-colors"
          onClick={() => console.log('STARK')}
        >
          Prove with STARK
        </button>
      </div>

      <div className="flex gap-4 h-48">
        <div className="flex-1 border border-gray-700 rounded-xl p-4 overflow-auto">
          <h2 className="text-lg font-semibold mb-2">Causal Event Stream</h2>
          <div className="font-mono text-xs space-y-1">
            {worldState?.event_stream?.map((e: any) => (
              <div key={e.id} className="py-1 border-b border-gray-800">
                [{new Date(e.timestamp * 1000).toISOString()}] {e.event_type} — {JSON.stringify(e.payload || {}).slice(0, 80)}
              </div>
            )) || <div className="text-gray-500">No events</div>}
          </div>
        </div>

        <div className="w-1/4 border border-red-500/30 rounded-xl p-4 overflow-auto">
          <h2 className="text-red-400 text-lg font-semibold mb-2">Causal Anomalies (Live)</h2>
          <div className="space-y-2">
            {anomalies.map((a) => (
              <div key={a.anomaly_id} className="flex justify-between text-sm border-b border-gray-800 py-2">
                <span className="font-mono">{a.anomaly_type}</span>
                <span className={severityClass(a.severity)}>{a.severity.toUpperCase()}</span>
                <span className="text-gray-400 text-xs">{a.affected_entity_keys?.slice(0, 2).join(', ') || 'global'}</span>
              </div>
            )) || <div className="text-gray-500 text-sm">No anomalies detected</div>}
          </div>
        </div>

        <div className="w-1/4 border border-violet-500/30 rounded-xl p-4">
          <h2 className="text-violet-400 text-lg font-semibold mb-2">RL Adaptation Engine</h2>
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>Last Action: <span className="font-mono">{worldState?.last_rl_action?.isolation_mode || 'none'}</span></div>
            <div>Policy Reward: <span className="font-semibold text-violet-400">{worldState?.rl_reward?.toFixed(3) || '0.000'}</span></div>
            <div>Detection Threshold: <span className="font-mono">{worldState?.last_rl_action?.detection_threshold?.toFixed(2) || '0.50'}</span></div>
            <div>Resource Scale: <span className="font-mono">{worldState?.last_rl_action?.resource_scale?.toFixed(2) || '1.00'}</span></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WorldStateDashboard;
