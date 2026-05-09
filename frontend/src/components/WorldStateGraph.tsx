import { useEffect, useState, useCallback, useRef } from 'react';

interface EntityNode {
  entity_id: string;
  entity_type: string;
  name: string;
  state_key: string;
  uncertainty: number;
  value: number;
}

interface GraphEvent {
  event_id: string;
  event_type: string;
  timestamp: number;
  causal_id: string;
  source_plugin: string;
  priority: string;
}

interface WorldState {
  state_id: string;
  timestamp: number;
  causal_id: string;
  regime: string;
  entities: Record<string, EntityNode>;
  uncertainty: Record<string, unknown>;
}

interface GraphSnapshot {
  nodes: EntityNode[];
  edges: { source_id: string; target_id: string; relation: string; weight: number }[];
  total_nodes: number;
  total_edges: number;
}

const REGIME_COLORS: Record<string, string> = {
  normal: '#22c55e',
  panic: '#f97316',
  disruption: '#ef4444',
};

const PRIORITY_COLORS: Record<string, string> = {
  critical: '#ef4444',
  high: '#f97316',
  normal: '#3b82f6',
};

export default function WorldStateGraph() {
  const [worldState, setWorldState] = useState<WorldState | null>(null);
  const [graph, setGraph] = useState<GraphSnapshot | null>(null);
  const [events, setEvents] = useState<GraphEvent[]>([]);
  const [entropy, setEntropy] = useState(0);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [refreshInterval, setRefreshInterval] = useState(15);
  const [replayTs, setReplayTs] = useState<number | null>(null);
  const esRef = useRef<EventSource | null>(null);

  const fetchState = useCallback(async () => {
    try {
      const ts = replayTs ? `?at_ts=${replayTs}` : '';
      const res = await fetch(`/api/v1/world-state/current${ts}`);
      if (res.ok) {
        const data = await res.json();
        setWorldState(data);
        setEntropy(computeEntropy(Object.values(data.entities || {})));
      }
    } catch {}
  }, [replayTs]);

  const fetchGraph = useCallback(async () => {
    try {
      const res = await fetch('/api/v1/world-state/graph?max_nodes=200');
      if (res.ok) setGraph(await res.json());
    } catch {}
  }, []);

  useEffect(() => {
    fetchState();
    fetchGraph();
    const iv = setInterval(() => { fetchState(); fetchGraph(); }, refreshInterval * 1000);
    return () => clearInterval(iv);
  }, [fetchState, fetchGraph, refreshInterval]);

  useEffect(() => {
    esRef.current?.close();
    const es = new EventSource('/api/v1/world-state/stream');
    esRef.current = es;
    es.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data.type !== 'keepalive' && data.state_id) setWorldState(data);
      } catch {}
    };
    return () => es.close();
  }, []);

  const computeEntropy = (entities: EntityNode[]): number => {
    if (!entities.length) return 0;
    return entities.reduce((s, e) => s + e.uncertainty, 0) / entities.length;
  };

  const regime = worldState?.regime || 'normal';
  const regimeColor = REGIME_COLORS[regime] || REGIME_COLORS.normal;
  const nodes = graph?.nodes || [];
  const topUncertain = [...nodes].sort((a, b) => b.uncertainty - a.uncertainty).slice(0, 8);

  return (
    <div className="flex flex-col h-full">
      <div className="grid grid-cols-4 gap-3 mb-4">
        <div className="bg-white rounded border p-3">
          <div className="text-xs text-gray-500 mb-1">Regime</div>
          <div className="text-xl font-bold" style={{ color: regimeColor }}>
            {regime.toUpperCase()}
          </div>
        </div>
        <div className="bg-white rounded border p-3">
          <div className="text-xs text-gray-500 mb-1">State Entropy</div>
          <div className="text-xl font-bold">{entropy.toFixed(3)}</div>
        </div>
        <div className="bg-white rounded border p-3">
          <div className="text-xs text-gray-500 mb-1">Graph Nodes</div>
          <div className="text-xl font-bold">{graph?.total_nodes ?? 0}</div>
        </div>
        <div className="bg-white rounded border p-3">
          <div className="text-xs text-gray-500 mb-1">Entities</div>
          <div className="text-xl font-bold">{Object.keys(worldState?.entities || {}).length}</div>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 flex-1">
        <div className="col-span-2 bg-white rounded border overflow-hidden">
          <div className="border-b px-3 py-2 text-sm font-medium flex justify-between items-center">
            <span>Entity Graph</span>
            <span className="text-xs text-gray-400">{nodes.length} nodes</span>
          </div>
          <div className="p-3 overflow-auto" style={{ maxHeight: '360px' }}>
            {nodes.length === 0 ? (
              <div className="text-gray-400 text-sm text-center py-8">No graph data available</div>
            ) : (
              <div className="flex flex-wrap gap-2">
                {nodes.map((node) => {
                  const opacity = Math.max(0.3, 1 - node.uncertainty);
                  return (
                    <button
                      key={node.entity_id}
                      onClick={() => setSelectedNode(selectedNode === node.entity_id ? null : node.entity_id)}
                      className={`rounded-full border px-3 py-1 text-xs transition-opacity ${selectedNode === node.entity_id ? 'ring-2 ring-blue-500' : ''}`}
                      style={{ opacity, borderColor: regimeColor }}
                      title={`${node.name} (${node.entity_type})`}
                    >
                      {node.name || node.entity_type}
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-3">
          <div className="bg-white rounded border overflow-hidden">
            <div className="border-b px-3 py-2 text-sm font-medium">Top Uncertainty</div>
            <div className="divide-y">
              {topUncertain.map((n) => (
                <div key={n.entity_id} className="px-3 py-1.5 flex justify-between text-xs">
                  <span className="truncate max-w-[120px]">{n.name}</span>
                  <span className="text-red-500 font-mono">{n.uncertainty.toFixed(3)}</span>
                </div>
              ))}
              {topUncertain.length === 0 && <div className="px-3 py-2 text-gray-400 text-xs">No entities</div>}
            </div>
          </div>

          <div className="bg-white rounded border overflow-hidden">
            <div className="border-b px-3 py-2 text-sm font-medium">Causal Event Stream</div>
            <div className="divide-y max-h-48 overflow-y-auto">
              {events.slice(-20).reverse().map((ev) => (
                <div key={ev.event_id} className="px-3 py-1.5 text-xs">
                  <div className="flex justify-between">
                    <span className="font-mono truncate max-w-[100px]">{ev.event_type}</span>
                    <span style={{ color: PRIORITY_COLORS[ev.priority] || '#999' }}>{ev.priority}</span>
                  </div>
                  <div className="text-gray-400">{new Date(ev.timestamp * 1000).toLocaleTimeString()}</div>
                </div>
              ))}
              {events.length === 0 && <div className="px-3 py-2 text-gray-400 text-xs">No events yet</div>}
            </div>
          </div>
        </div>
      </div>

      <div className="mt-3 flex gap-3 items-center">
        <label className="text-xs text-gray-500">
          Refresh: {refreshInterval}s
          <input
            type="range"
            min={5}
            max={60}
            value={refreshInterval}
            onChange={(e) => setRefreshInterval(Number(e.target.value))}
            className="ml-2"
          />
        </label>
        <label className="text-xs text-gray-500">
          Replay:
          <input
            type="datetime-local"
            onChange={(e) => setReplayTs(e.target.value ? new Date(e.target.value).getTime() / 1000 : null)}
            className="ml-2 border rounded px-1 text-xs"
          />
        </label>
        <button onClick={fetchState} className="text-xs bg-blue-500 text-white px-3 py-1 rounded">
          Refresh
        </button>
      </div>
    </div>
  );
}
