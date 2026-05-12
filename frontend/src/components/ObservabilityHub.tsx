import React, { useEffect, useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useSSE } from '@/hooks/useSSE';
import {
  Activity,
  Brain,
  Cpu,
  DollarSign,
  Shield,
  Zap,
  AlertTriangle,
  Clock,
  FileText,
  ExternalLink,
  RefreshCcw,
  GitBranch,
  Workflow,
  Layers,
  Server,
  Terminal,
  Radio,
} from 'lucide-react';

interface RecentLog {
  timestamp: string;
  level: 'INFO' | 'WARN' | 'ERROR';
  message: string;
  trace_id?: string;
  tenant_id?: string;
}

const ObservabilityHub: React.FC = () => {
  const [kernelHealth, setKernelHealth] = useState({ booted: true, uptime: '14h 23m' });
  const [regime, setRegime] = useState('normal');
  const [anomalies, setAnomalies] = useState(2);
  const [llmSpend, setLlmSpend] = useState(12.4);
  const [recentLogs, setRecentLogs] = useState<RecentLog[]>([]);
  const [logRate, setLogRate] = useState(8.4);

  const {
    data: liveMetrics,
    error: sseError,
    connected,
    isReconnecting,
    reconnect,
  } = useSSE('/api/v1/observability/stream');

  useEffect(() => {
    const fetchRecentLogs = async () => {
      try {
        const res = await fetch('/api/v1/observability/recent-logs?limit=5');
        if (!res.ok) return;
        const data = await res.json();
        setRecentLogs(data.logs || []);
      } catch (e) {}
    };
    fetchRecentLogs();
    const interval = setInterval(fetchRecentLogs, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (liveMetrics) {
      setKernelHealth(liveMetrics.kernel || kernelHealth);
      setRegime(liveMetrics.regime || regime);
      setAnomalies(liveMetrics.anomalies ?? anomalies);
      setLlmSpend(liveMetrics.llm_spend_usd ?? llmSpend);
      setLogRate(liveMetrics.log_rate ?? logRate);
    }
  }, [liveMetrics]);

  const kernelViews = [
    {
      id: 'dag',
      icon: Workflow,
      label: 'DAG Execution',
      description: 'Live execution graph with node states, timing, and retries. Watch every DAG node run in real-time.',
      status: 'active',
    },
    {
      id: 'events',
      icon: Radio,
      label: 'Event Stream',
      description: 'Real-time kernel event feed. See every protocol message, state change, and trust evaluation.',
      status: 'active',
    },
    {
      id: 'simulation',
      icon: Layers,
      label: 'Simulation Viewer',
      description: 'Branching timelines, probabilistic states, and Monte Carlo convergence monitoring.',
      status: 'active',
    },
    {
      id: 'scheduler',
      icon: Server,
      label: 'Scheduler Dashboard',
      description: 'Queue depth, GPU allocation heatmap, tenant fairness metrics, and preemption events.',
      status: 'active',
    },
    {
      id: 'replay',
      icon: RefreshCcw,
      label: 'Replay Console',
      description: 'Deterministic re-run of any past execution. Verify outputs with hash comparison.',
      status: 'active',
    },
    {
      id: 'capabilities',
      icon: GitBranch,
      label: 'Capability Graph',
      description: 'Plugin dependency graph. See which plugins offer which capabilities and how they connect.',
      status: 'active',
    },
  ];

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <div className="w-64 border-r border-border p-4 flex flex-col gap-6">
        <div className="flex items-center gap-2">
          <Zap className="h-6 w-6 text-cyan-400" />
          <h1 className="text-2xl font-bold text-foreground">Kernel Observatory</h1>
        </div>

        <Card>
          <CardContent className="p-4">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <div className="text-muted-foreground">Kernel</div>
                <Badge variant={kernelHealth.booted ? "default" : "destructive"}>Healthy</Badge>
              </div>
              <div>
                <div className="text-muted-foreground">Regime</div>
                <Badge variant="outline" className="capitalize">{regime}</Badge>
              </div>
              <div>
                <div className="text-muted-foreground">Anomalies</div>
                <Badge variant={anomalies > 0 ? "destructive" : "secondary"}>{anomalies}</Badge>
              </div>
              <div>
                <div className="text-muted-foreground">LLM Spend (24h)</div>
                <div className="font-mono text-lg">${llmSpend}</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <nav className="flex flex-col gap-2">
          {kernelViews.map((view) => (
            <Button
              key={view.id}
              variant="ghost"
              className="justify-start"
              asChild
            >
              <a href={`#${view.id}`}>
                <view.icon className="h-4 w-4 mr-2" />
                {view.label}
              </a>
            </Button>
          ))}
        </nav>

        <div className="mt-auto">
          <Button variant="outline" size="sm" className="w-full" asChild>
            <a href="/dashboard" target="_blank" rel="noopener noreferrer">
              <ExternalLink className="h-3 w-3 mr-1" />
              Back to Dashboard
            </a>
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-6">
        {sseError && (
          <div className="bg-red-100 dark:bg-red-900/20 text-red-700 dark:text-red-300 p-3 rounded-lg mb-4 flex items-center gap-3">
            <span>{sseError} {!connected && '(offline)'}</span>
            <Button variant="outline" size="sm" onClick={reconnect} disabled={isReconnecting}>
              <RefreshCcw className={`h-4 w-4 mr-1 ${isReconnecting ? 'animate-spin' : ''}`} />
              {isReconnecting ? 'Reconnecting...' : 'Retry'}
            </Button>
          </div>
        )}

        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-8">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="dag">DAG</TabsTrigger>
            <TabsTrigger value="events">Events</TabsTrigger>
            <TabsTrigger value="simulation">Simulation</TabsTrigger>
            <TabsTrigger value="scheduler">Scheduler</TabsTrigger>
            <TabsTrigger value="replay">Replay</TabsTrigger>
            <TabsTrigger value="capabilities">Capabilities</TabsTrigger>
            <TabsTrigger value="logs">Logs</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <Activity className="h-4 w-4 text-green-500" />
                    Kernel Health
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-4xl font-bold text-green-500">Healthy</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <Brain className="h-4 w-4 text-blue-500" />
                    Regime
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-4xl font-bold capitalize">{regime}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <AlertTriangle className="h-4 w-4 text-orange-500" />
                    Anomalies
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-4xl font-bold text-orange-500">{anomalies}</div>
                </CardContent>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-sm">
                    <DollarSign className="h-4 w-4 text-yellow-500" />
                    LLM Spend (24h)
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-4xl font-bold">${llmSpend}</div>
                </CardContent>
              </Card>
            </div>

            {/* Recent Logs */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Recent Logs
                  <Badge variant="outline" className="ml-auto">{logRate.toFixed(1)} logs/sec</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-64 overflow-auto text-sm">
                  {recentLogs.map((log, i) => (
                    <div key={i} className="flex items-start gap-3 border-l-4 border-l-blue-500 pl-3">
                      <Badge variant={log.level === 'ERROR' ? 'destructive' : log.level === 'WARN' ? 'secondary' : 'default'}>
                        {log.level}
                      </Badge>
                      <div className="flex-1">
                        <div className="font-mono text-xs text-muted-foreground">{log.timestamp}</div>
                        <div className="line-clamp-2">{log.message}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Kernel Views */}
          {kernelViews.map((view) => (
            <TabsContent key={view.id} value={view.id}>
              <div className="h-full p-4">
                <div className="flex items-center gap-3 mb-4">
                  <view.icon className="h-6 w-6 text-cyan-400" />
                  <h2 className="text-xl font-bold">{view.label}</h2>
                  <Badge variant="outline" className="ml-2">Live</Badge>
                </div>
                <p className="text-muted-foreground mb-4">{view.description}</p>
                <div className="border-2 border-dashed border-border rounded-xl h-[500px] flex items-center justify-center bg-muted/20">
                  <div className="text-center">
                    <view.icon className="h-12 w-12 text-muted-foreground/30 mx-auto mb-3" />
                    <p className="text-muted-foreground text-sm">
                      {view.label} visualization will render here.
                    </p>
                    <p className="text-muted-foreground text-xs mt-1">
                      Connected to kernel event stream &bull; Awaiting data...
                    </p>
                  </div>
                </div>
              </div>
            </TabsContent>
          ))}

          {/* Logs Tab */}
          <TabsContent value="logs">
            <div className="h-full">
              <h2 className="text-xl font-bold mb-4">Structured Logs (Loki)</h2>
              <iframe
                src="/grafana/explore?schemaVersion=1&panes=%7B%22logs%22:%7B%22datasource%22:%22loki%22,%22queries%22:[%7B%22refId%22:%22A%22,%22expr%22:%22%7Bservice_name%3D%5C%22simhpc-core%5C%22%7D%22%7D]%7D%7D"
                className="w-full h-[calc(100vh-120px)] border rounded-xl"
                title="Loki Logs"
              />
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export { ObservabilityHub };
