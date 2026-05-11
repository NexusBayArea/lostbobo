import React, { useEffect, useState } from 'react';
import ReactFlow, {
  Controls,
  MiniMap,
  Background,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

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
  last_rl_action?: any;
  rl_reward?: number;
}

interface RLPolicyData {
  timestamp: number;
  action_distribution: {
    sandbox: number;
    wasm: number;
    kata: number;
  };
  quarantine_probability: number;
  resource_scale_mean: number;
  exploration_rate: number;
  last_reward: number;
  recent_decisions: Array<{
    timestamp: number;
    action: string;
    reward: number;
  }>;
  reward_history: number[];
  last_chaos?: boolean;
}

const WorldStateDashboard: React.FC = () => {
  const [worldState, setWorldState] = useState<WorldState | null>(null);
  const [rlPolicy, setRlPolicy] = useState<RLPolicyData | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Existing SSE for WorldState
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
  }, [setNodes, setEdges]);

  // New polling for RL policy
  useEffect(() => {
    const fetchRLPolicy = async () => {
      try {
        const res = await fetch('/api/v1/core/rl-policy-inspection');
        const data = await res.json();
        setRlPolicy(data);
      } catch (err) {
        console.error('Failed to fetch RL policy:', err);
      }
    };

    fetchRLPolicy();
    const interval = setInterval(fetchRLPolicy, 3000);
    return () => clearInterval(interval);
  }, []);

  const regimeColor =
    worldState?.regime === 'normal' ? 'text-emerald-400' :
    worldState?.regime === 'panic' ? 'text-red-400' : 'text-amber-400';

  return (
    <div className="h-screen flex flex-col bg-gray-950 text-white p-6 gap-6 overflow-hidden">
      {/* Top metrics row */}
      <div className="grid grid-cols-12 gap-4 h-24">
        <Card className="col-span-3 bg-gray-900 border-gray-800">
          <CardHeader className="p-3">
            <CardTitle className="text-xs text-gray-400 font-medium">System Regime</CardTitle>
          </CardHeader>
          <CardContent className="px-3 pb-3">
            <div className={`text-2xl font-bold ${regimeColor}`}>
              {worldState?.regime?.toUpperCase() || 'NORMAL'}
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-2 bg-gray-900 border-gray-800">
          <CardHeader className="p-3">
            <CardTitle className="text-xs text-gray-400 font-medium">Entropy</CardTitle>
          </CardHeader>
          <CardContent className="px-3 pb-3">
            <div className="text-2xl font-bold text-blue-400">
              {worldState?.entropy?.toFixed(4) || '0.0000'}
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-4 bg-gray-900 border-gray-800">
          <CardHeader className="p-3">
            <CardTitle className="text-xs text-gray-400 font-medium">Causal ID</CardTitle>
          </CardHeader>
          <CardContent className="px-3 pb-3">
            <div className="font-mono text-sm text-gray-300 truncate">
              {worldState?.causal_id || 'ID_NOT_AVAILABLE'}
            </div>
          </CardContent>
        </Card>

        <Card className="col-span-3 bg-gray-900 border-gray-800 border-violet-500/30">
          <CardHeader className="p-3">
            <CardTitle className="text-xs text-violet-400 font-medium">RL Policy Health</CardTitle>
          </CardHeader>
          <CardContent className="px-3 pb-3 flex justify-between items-end">
            <div className="text-2xl font-bold text-violet-400">
              {rlPolicy?.last_reward?.toFixed(2) || '—'}
            </div>
            <div className="text-xs text-violet-400 mb-1">
              Exploration: {((rlPolicy?.exploration_rate || 0) * 100).toFixed(1)}%
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="flex-1 flex gap-6 overflow-hidden">
        {/* Left: Entity Graph */}
        <div className="flex-1 border border-gray-700 rounded-2xl overflow-hidden bg-gray-900/50">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            fitView
          >
            <Controls />
            <MiniMap />
            <Background variant="dots" gap={20} size={1} color="#334155" />
          </ReactFlow>
        </div>

        {/* Right: RL Policy Inspection Panel */}
        <div className="w-[400px] flex flex-col gap-4 overflow-y-auto pr-2">
          {/* 1. Action Distribution */}
          <Card className="bg-gray-900 border-gray-800">
            <CardHeader className="p-4 pb-0">
              <CardTitle className="text-sm font-semibold">Current Policy Distribution</CardTitle>
            </CardHeader>
            <CardContent className="p-4 h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={[
                    { name: 'Sandbox', value: rlPolicy?.action_distribution?.sandbox || 0 },
                    { name: 'WASM', value: rlPolicy?.action_distribution?.wasm || 0 },
                    { name: 'Kata', value: rlPolicy?.action_distribution?.kata || 0 },
                  ]}
                  layout="vertical"
                >
                  <XAxis type="number" hide />
                  <YAxis dataKey="name" type="category" width={80} stroke="#94a3b8" fontSize={12} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }}
                    itemStyle={{ color: '#fff' }}
                  />
                  <Bar dataKey="value" radius={[0, 4, 4, 0]} fill="#8b5cf6" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* 2. Reward History */}
          <Card className="bg-gray-900 border-gray-800">
            <CardHeader className="p-4 pb-0">
              <CardTitle className="text-sm font-semibold">Reward Trajectory (last steps)</CardTitle>
            </CardHeader>
            <CardContent className="p-4 h-40">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={rlPolicy?.reward_history?.map((r: number, i: number) => ({
                    step: i,
                    reward: r
                  })) || []}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                  <XAxis dataKey="step" hide />
                  <YAxis domain={['auto', 'auto']} stroke="#94a3b8" fontSize={10} />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', border: 'none', borderRadius: '8px' }}
                    labelStyle={{ display: 'none' }}
                  />
                  <Line type="monotone" dataKey="reward" stroke="#8b5cf6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* 3. Recent Decisions Table */}
          <Card className="bg-gray-900 border-gray-800 flex-1 min-h-0">
            <CardHeader className="p-4 pb-0">
              <CardTitle className="text-sm font-semibold">Recent RL Decisions</CardTitle>
            </CardHeader>
            <CardContent className="p-2">
              <Table>
                <TableHeader>
                  <TableRow className="border-gray-800 hover:bg-transparent">
                    <TableHead className="h-8 text-xs">Time</TableHead>
                    <TableHead className="h-8 text-xs">Action</TableHead>
                    <TableHead className="h-8 text-xs text-right">Reward</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {(rlPolicy?.recent_decisions || []).slice(0, 8).map((d, i) => (
                    <TableRow key={i} className="border-gray-800 hover:bg-gray-800/50">
                      <TableCell className="py-2 text-[10px] font-mono text-gray-400">
                        {new Date(d.timestamp * 1000).toLocaleTimeString()}
                      </TableCell>
                      <TableCell className="py-2 text-xs font-medium">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                          d.action === 'kata' ? 'bg-violet-500/20 text-violet-400' :
                          d.action === 'wasm' ? 'bg-amber-500/20 text-amber-400' :
                          'bg-emerald-500/20 text-emerald-400'
                        }`}>
                          {d.action.toUpperCase()}
                        </span>
                      </TableCell>
                      <TableCell className="py-2 text-xs text-right font-mono">
                        {d.reward.toFixed(3)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>

          {/* 4. Quarantine & Chaos Status */}
          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="p-4 grid grid-cols-2 gap-4">
              <div>
                <div className="text-[10px] text-gray-400 uppercase font-bold tracking-wider mb-1">Quarantine Prob.</div>
                <div className="text-xl font-bold">
                  {((rlPolicy?.quarantine_probability || 0) * 100).toFixed(0)}%
                </div>
              </div>
              <div>
                <div className="text-[10px] text-gray-400 uppercase font-bold tracking-wider mb-1">Chaos Injection</div>
                <div className={`text-xl font-bold ${rlPolicy?.last_chaos ? "text-red-500" : "text-emerald-500"}`}>
                  {rlPolicy?.last_chaos ? "ACTIVE" : "IDLE"}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default WorldStateDashboard;
