import React, { useEffect, useState, useCallback } from 'react';
import ReactFlow, { Node, Edge, Controls, Background, MiniMap } from 'reactflow';
import 'reactflow/dist/style.css';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Play, Zap, RefreshCw, Target, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { useTheme } from '@/hooks/useTheme';
import { ThemeToggle } from '@/components/ThemeToggle';
import { api } from '@/lib/api';

const DAGNode = ({ data }: any) => {
  const statusColors: Record<string, string> = {
    idle: 'border-slate-400 bg-slate-100 dark:bg-slate-800 dark:border-slate-600',
    pending: 'border-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 dark:border-yellow-600',
    running: 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-500 animate-pulse',
    success: 'border-green-500 bg-green-50 dark:bg-green-900/20 dark:border-green-500',
    failed: 'border-red-500 bg-red-50 dark:bg-red-900/20 dark:border-red-500',
  };

  return (
    <div
      className={`px-5 py-3 shadow-lg rounded-xl border-2 transition-all duration-200 ${
        statusColors[data.status] || statusColors.idle
      }`}
    >
      <div className="font-semibold text-sm text-slate-900 dark:text-white">{data.label}</div>
      {data.gpu && (
        <Badge variant="outline" className="text-[10px] mt-1 dark:text-slate-300">
          GPU
        </Badge>
      )}
      {data.duration && (
        <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-1">{data.duration}ms</div>
      )}
    </div>
  );
};

interface DAGResponse {
  nodes: Array<{
    id: string;
    label: string;
    status: string;
    gpu?: boolean;
    duration?: number;
  }>;
  edges: Array<{ source: string; target: string }>;
}

export default function DAGDashboard() {
  const { theme } = useTheme();
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);
  const [status, setStatus] = useState<'idle' | 'pending' | 'running' | 'success' | 'failed'>('idle');
  const [error, setError] = useState<string | null>(null);
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [execTime, setExecTime] = useState<number | null>(null);
  const [currentRunId, setCurrentRunId] = useState<string | null>(null);

  const fetchGraph = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await api.get<DAGResponse>('/api/v1/dag/graph', false);

      const transformedNodes = response.nodes.map((node, index) => ({
        id: node.id,
        data: {
          label: node.label,
          status: node.status,
          gpu: node.gpu,
          duration: node.duration,
        },
        position: {
          x: (index % 3) * 300,
          y: Math.floor(index / 3) * 150,
        },
        type: 'default',
      }));

      const transformedEdges = response.edges.map((edge) => ({
        id: `edge-${edge.source}-${edge.target}`,
        source: edge.source,
        target: edge.target,
      }));

      setNodes(transformedNodes);
      setEdges(transformedEdges);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to fetch DAG graph';
      setError(errorMsg);
      console.error('Error fetching graph:', err);
      toast.error(errorMsg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const runFullDAG = useCallback(async () => {
    try {
      setStatus('pending');
      setError(null);
      const startTime = Date.now();

      const response = await api.post<{ run_id: string }>('/api/v1/dag/run', { full: true });

      setCurrentRunId(response.run_id);
      setStatus('running');
      toast.success('Full DAG execution started');

      setExecTime(Date.now() - startTime);
      setStatus('success');
      toast.success('DAG execution completed');
      fetchGraph();
    } catch (err) {
      setStatus('failed');
      const errorMsg = err instanceof Error ? err.message : 'Failed to start DAG execution';
      setError(errorMsg);
      toast.error(errorMsg);
    }
  }, [fetchGraph]);

  const runNode = useCallback(
    async (nodeId: string) => {
      try {
        setError(null);
        await api.post<{ run_id: string }>(`/api/v1/dag/run/${nodeId}`, {});
        toast.info(`Running node: ${nodeId}`);
        setTimeout(() => fetchGraph(), 1000);
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : `Failed to run node: ${nodeId}`;
        setError(errorMsg);
        toast.error(errorMsg);
      }
    },
    [fetchGraph]
  );

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/dag/ws`;

    try {
      const socket = new WebSocket(wsUrl);

      socket.onopen = () => {
        toast.success('Connected to live updates');
      };

      socket.onmessage = () => {
        fetchGraph();
      };

      socket.onerror = () => {
        toast.error('Live update connection failed');
      };

      socket.onclose = () => {
        setTimeout(() => {
          const newSocket = new WebSocket(wsUrl);
          setWs(newSocket);
        }, 5000);
      };

      setWs(socket);

      return () => {
        socket.close();
      };
    } catch (err) {
      console.error('Failed to establish WebSocket:', err);
    }
  }, [fetchGraph]);

  useEffect(() => {
    fetchGraph();
    const interval = setInterval(fetchGraph, 3000);
    return () => clearInterval(interval);
  }, [fetchGraph]);

  return (
    <div className={`h-screen flex ${theme === 'dark' ? 'bg-slate-950 text-white' : 'bg-slate-50 text-slate-900'}`}>
      <div
        className={`w-80 border-r ${
          theme === 'dark' ? 'border-slate-800 bg-slate-900' : 'border-slate-200 bg-white'
        } p-6 overflow-auto flex flex-col`}
      >
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center gap-3">
            <Zap
              className={`w-8 h-8 ${
                theme === 'dark' ? 'text-cyan-400' : 'text-cyan-600'
              }`}
            />
            <h1 className="text-2xl font-bold">SimHPC DAG</h1>
          </div>
          <ThemeToggle />
        </div>

        {error && (
          <div
            className={`mb-4 p-4 rounded-lg border flex gap-2 ${
              theme === 'dark'
                ? 'bg-red-900/20 border-red-600 text-red-400'
                : 'bg-red-50 border-red-300 text-red-700'
            }`}
          >
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <div className="text-sm">{error}</div>
          </div>
        )}

        <Button
          onClick={runFullDAG}
          className="w-full mb-4"
          size="lg"
          disabled={status === 'running' || isLoading}
        >
          {status === 'running' ? (
            <>
              <RefreshCw className="mr-2 w-4 h-4 animate-spin" />
              Running...
            </>
          ) : (
            <>
              <Play className="mr-2" /> Run Full Pipeline
            </>
          )}
        </Button>

        <div className="mb-6">
          <Badge variant="secondary" className={`w-full justify-center py-2 text-sm font-semibold`}>
            Status: {status.toUpperCase()}
          </Badge>
          {execTime && (
            <p
              className={`text-xs text-center mt-2 ${
                theme === 'dark' ? 'text-slate-400' : 'text-slate-600'
              }`}
            >
              Execution time: {(execTime / 1000).toFixed(2)}s
            </p>
          )}
        </div>

        <div className="flex-1">
          <Card
            className={
              theme === 'dark'
                ? 'bg-slate-950 border-slate-700'
                : 'bg-slate-100 border-slate-300'
            }
          >
            <CardHeader className="pb-3">
              <CardTitle className="text-sm flex items-center gap-2">
                <Target className="w-4 h-4" />
                Available Nodes ({nodes.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 max-h-96 overflow-y-auto">
              {isLoading ? (
                <div
                  className={`text-sm text-center py-4 ${
                    theme === 'dark' ? 'text-slate-400' : 'text-slate-600'
                  }`}
                >
                  Loading nodes...
                </div>
              ) : nodes.length === 0 ? (
                <div
                  className={`text-sm text-center py-4 ${
                    theme === 'dark' ? 'text-slate-400' : 'text-slate-600'
                  }`}
                >
                  No nodes available
                </div>
              ) : (
                nodes.map((node) => (
                  <Button
                    key={node.id}
                    variant="outline"
                    size="sm"
                    className="w-full justify-start text-left truncate"
                    onClick={() => runNode(node.id)}
                    disabled={status === 'running'}
                    title={node.data.label}
                  >
                    <Target className="mr-2 h-4 w-4 flex-shrink-0" />
                    <span className="truncate">{node.data.label}</span>
                  </Button>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {currentRunId && (
          <div
            className={`mt-6 p-3 rounded-lg text-xs ${
              theme === 'dark'
                ? 'bg-slate-800 text-slate-300'
                : 'bg-slate-200 text-slate-700'
            }`}
          >
            <p className="font-semibold mb-1">Current Run ID:</p>
            <p className="font-mono break-all">{currentRunId}</p>
          </div>
        )}
      </div>

      <div className="flex-1 relative overflow-hidden">
        {isLoading && nodes.length === 0 ? (
          <div
            className={`w-full h-full flex items-center justify-center ${
              theme === 'dark' ? 'bg-slate-950' : 'bg-slate-50'
            }`}
          >
            <div className="text-center">
              <RefreshCw className="w-12 h-12 animate-spin mx-auto mb-4 opacity-50" />
              <p className={theme === 'dark' ? 'text-slate-400' : 'text-slate-600'}>
                Loading DAG...
              </p>
            </div>
          </div>
        ) : (
          <ReactFlow
            nodes={nodes}
            edges={edges}
            nodeTypes={{ default: DAGNode }}
            fitView
            className={theme === 'dark' ? 'bg-slate-950' : 'bg-slate-50'}
          >
            <Background
              color={theme === 'dark' ? '#334155' : '#cbd5e1'}
              gap={16}
            />
            <Controls />
            <MiniMap
              className={theme === 'dark' ? 'dark' : 'light'}
              maskColor={theme === 'dark' ? '#1e293b' : '#f1f5f9'}
            />
          </ReactFlow>
        )}

        <div className="absolute top-6 right-6 flex flex-col gap-2 pointer-events-none">
          <Badge
            variant="secondary"
            className={`px-4 py-1.5 text-sm font-semibold`}
          >
            {status.toUpperCase()}
          </Badge>
          {ws && <Badge variant="outline">Live Connected</Badge>}
        </div>
      </div>
    </div>
  );
}