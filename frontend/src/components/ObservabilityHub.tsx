import React, { useEffect, useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Activity, Brain, Cpu, DollarSign, Zap, AlertTriangle, FileText } from 'lucide-react';
import WorldStateDashboard from './WorldStateDashboard';
import RLTrainingDashboard from './RLTrainingDashboard';
import { useSSE } from '@/hooks/useSSE';
import DAGExecutionViewer from './kernel-views/DAGExecutionViewer';
import EventStreamViewer from './kernel-views/EventStreamViewer';
import SimulationViewer from './kernel-views/SimulationViewer';
import SchedulerDashboard from './kernel-views/SchedulerDashboard';
import ReplayConsole from './kernel-views/ReplayConsole';
import CapabilityGraphExplorer from './kernel-views/CapabilityGraphExplorer';

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
  const [rateLimitHits, setRateLimitHits] = useState(47);
  const [recentLogs, setRecentLogs] = useState<RecentLog[]>([]);
  const [logRate, setLogRate] = useState(8.4);

  const { data: liveMetrics } = useSSE('/api/v1/observability/stream');

  useEffect(() => {
    const fetchRecentLogs = async () => {
      try {
        const res = await fetch('/api/v1/observability/recent-logs?limit=5');
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
      setAnomalies(liveMetrics.anomalies || anomalies);
      setLlmSpend(liveMetrics.llm_spend_usd || llmSpend);
      setRateLimitHits(liveMetrics.rate_limit_hits || rateLimitHits);
      setLogRate(liveMetrics.log_rate || logRate);
    }
  }, [liveMetrics]);

  const openCorrelatedLogs = (filter: string) => {
    const lokiUrl = `/grafana/explore?schemaVersion=1&panes=%7B%22logs%22:%7B%22datasource%22:%22loki%22,%22queries%22:[%7B%22refId%22:%22A%22,%22expr%22:%22${encodeURIComponent(filter)}%22%7D]%7D%7D`;
    window.open(lokiUrl, '_blank');
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <div className="w-64 border-r p-4 flex flex-col gap-6">
        <div className="flex items-center gap-2">
          <Zap className="h-6 w-6 text-primary" />
          <h1 className="text-2xl font-bold">SimHPC Observatory</h1>
        </div>

        <Card className="p-4">
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
        </Card>

        <nav className="flex flex-col gap-2">
          <Button variant="ghost" className="justify-start" asChild><a href="#dag-execution">⚙️ DAG Execution</a></Button>
          <Button variant="ghost" className="justify-start" asChild><a href="#event-stream">📡 Event Stream</a></Button>
          <Button variant="ghost" className="justify-start" asChild><a href="#simulation">🌿 Simulation</a></Button>
          <Button variant="ghost" className="justify-start" asChild><a href="#scheduler">📊 Scheduler</a></Button>
          <Button variant="ghost" className="justify-start" asChild><a href="#replay">↩️ Replay Console</a></Button>
          <Button variant="ghost" className="justify-start" asChild><a href="#capabilities">🧩 Capability Graph</a></Button>
          <Button variant="ghost" className="justify-start" asChild><a href="#world-state">🌍 World State</a></Button>
          <Button variant="ghost" className="justify-start" asChild><a href="#rl-training">🧠 RL Training</a></Button>
          <Button variant="ghost" className="justify-start" asChild><a href="#hardware">🖥️ GPU/MIG</a></Button>
          <Button variant="ghost" className="justify-start" asChild><a href="#otel">📈 OTel Metrics</a></Button>
          <Button variant="ghost" className="justify-start" asChild>
            <a href="http://localhost:16686" target="_blank" rel="noopener noreferrer">🔍 Jaeger Tracing</a>
          </Button>
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-6">
        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-11">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="dag">DAG</TabsTrigger>
            <TabsTrigger value="events">Events</TabsTrigger>
            <TabsTrigger value="simulation">Simulation</TabsTrigger>
            <TabsTrigger value="scheduler">Scheduler</TabsTrigger>
            <TabsTrigger value="replay">Replay</TabsTrigger>
            <TabsTrigger value="capabilities">Capabilities</TabsTrigger>
            <TabsTrigger value="world-state">World State</TabsTrigger>
            <TabsTrigger value="rl">RL</TabsTrigger>
            <TabsTrigger value="grafana">Grafana</TabsTrigger>
            <TabsTrigger value="otel">OTel</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-5 gap-6">
              <Card>
                <CardHeader><CardTitle className="flex items-center gap-2"><Activity className="h-4 w-4" /> Kernel Health</CardTitle></CardHeader>
                <CardContent className="flex justify-between items-end">
                  <div className="text-4xl font-bold text-green-500">Healthy</div>
                  <Button variant="outline" size="sm" onClick={() => openCorrelatedLogs('{service_name="simhpc-core"} | trace_id%3D*')}>
                    View Logs
                  </Button>
                </CardContent>
              </Card>

              <Card className="col-span-2">
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
                          {log.trace_id && (
                            <Button
                              variant="link"
                              size="sm"
                              className="h-auto p-0 text-xs text-blue-500"
                              onClick={() => openCorrelatedLogs(`{trace_id="${log.trace_id}"}`)}
                            >
                              Trace {log.trace_id.slice(0, 8)}…
                            </Button>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader><CardTitle className="flex items-center gap-2"><AlertTriangle className="h-4 w-4" /> Anomalies</CardTitle></CardHeader>
                <CardContent>
                  <div className="text-4xl font-bold text-orange-500">{anomalies}</div>
                  <Button variant="outline" size="sm" className="mt-4 w-full" onClick={() => openCorrelatedLogs('{level="ERROR"} | anomalies')}>
                    View Correlated Logs
                  </Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader><CardTitle className="flex items-center gap-2"><DollarSign className="h-4 w-4" /> LLM Spend (24h)</CardTitle></CardHeader>
                <CardContent>
                  <div className="text-4xl font-bold">${llmSpend}</div>
                  <Button variant="outline" size="sm" className="mt-4 w-full" onClick={() => openCorrelatedLogs('{service_name="simhpc-core"} | llm')}>
                    LLM Logs
                  </Button>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="dag"><DAGExecutionViewer /></TabsContent>
          <TabsContent value="events"><EventStreamViewer /></TabsContent>
          <TabsContent value="simulation"><SimulationViewer /></TabsContent>
          <TabsContent value="scheduler"><SchedulerDashboard /></TabsContent>
          <TabsContent value="replay"><ReplayConsole /></TabsContent>
          <TabsContent value="capabilities"><CapabilityGraphExplorer /></TabsContent>
          <TabsContent value="world-state"><WorldStateDashboard /></TabsContent>
          <TabsContent value="rl"><RLTrainingDashboard /></TabsContent>

          <TabsContent value="grafana">
            <div className="text-center py-12">
              <h2 className="text-2xl font-semibold mb-4">Full Grafana + Thanos Instance</h2>
              <Button asChild size="lg">
                <a href="/grafana" target="_blank" rel="noopener noreferrer">Open Grafana → All Dashboards</a>
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="otel">
            <div className="space-y-6">
              <h2 className="text-2xl font-bold">OpenTelemetry Metrics</h2>
              <iframe
                src="/grafana/d/otel-metrics?orgId=1&refresh=10s"
                className="w-full h-[800px] border rounded-xl"
                title="OTel Metrics Dashboard"
              />
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
};

export default ObservabilityHub;
