import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { FileText } from 'lucide-react';
import { toast } from 'sonner';

export default function ReportGenerator() {
  const [simulationId, setSimulationId] = useState("");
  const [reportType, setReportType] = useState<"thermal_analysis" | "robustness" | "compliance" | "executive">("thermal_analysis");
  const [isGenerating, setIsGenerating] = useState(false);

  const generateReport = async () => {
    if (!simulationId) {
      toast.error("Please enter a simulation ID");
      return;
    }
    setIsGenerating(true);
    try {
      const res = await fetch('/api/v1/reports/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ simulation_id: simulationId, report_type: reportType, dag_trigger: true })
      });

      const data = await res.json();
      toast.success(`Report queued! Job ID: ${data.job_id}`);
    } catch (e) {
      toast.error("Failed to queue report");
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <Card className="w-full max-w-2xl">
      <CardHeader>
        <CardTitle className="flex items-center gap-3">
          <FileText className="w-6 h-6" />
          AI Report Generator
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        <div>
          <label className="text-sm font-medium">Simulation ID</label>
          <input
            type="text"
            value={simulationId}
            onChange={(e) => setSimulationId(e.target.value)}
            className="w-full mt-1 p-3 border rounded-lg"
            placeholder="sim_2026_05_04_001"
          />
        </div>

        <div>
          <label className="text-sm font-medium">Report Type</label>
          <Select value={reportType} onValueChange={(v: any) => setReportType(v)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="thermal_analysis">Thermal Runaway Analysis</SelectItem>
              <SelectItem value="robustness">Robustness & Sensitivity</SelectItem>
              <SelectItem value="compliance">Compliance & Certification</SelectItem>
              <SelectItem value="executive">Executive Summary</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <Button onClick={generateReport} disabled={!simulationId || isGenerating} className="w-full" size="lg">
          {isGenerating ? "Generating via DAG..." : "Generate Report"}
        </Button>

        <div className="text-xs text-muted-foreground text-center">
          Powered by SimHPC DAG + AI Intelligence Engine
        </div>
      </CardContent>
    </Card>
  );
}