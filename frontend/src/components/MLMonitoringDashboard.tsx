"use client";

import { useState, useEffect, useCallback } from "react";
import { simhpcFetch } from "@/lib/simhpc-client";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";

interface ModelVersion {
  version_id: string;
  semver: string;
  created_at: string;
  trained_on_runs: number;
  overall_score: number;
  mean_accuracy: number;
  status: string;
}

interface ModelStatus {
  latest_model?: {
    version: string;
    trained_on_runs: number;
    mean_accuracy: number;
    overall_score: number;
  };
  moat_strength: string;
  performance_trend: Array<{
    version: string;
    date: string;
    trained_on_runs: number;
    mean_accuracy: number;
    overall_score: number;
  }>;
}

interface DatasetStats {
  total_qualified_runs: number;
  estimated_training_examples: number;
  certified_runs: number;
  ready_for_training: boolean;
  training_milestone: string;
}

export default function MLMonitoringDashboard() {
  const [modelStatus, setModelStatus] = useState<ModelStatus | null>(null);
  const [datasetStats, setDatasetStats] = useState<DatasetStats | null>(null);
  const [versions, setVersions] = useState<ModelVersion[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<string>("latest");
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [training, setTraining] = useState(false);

  const fetchAllData = useCallback(async () => {
    try {
      const [statusRes, datasetRes, versionsRes] = await Promise.all([
        simhpcFetch("/ml/model/status"),
        simhpcFetch("/ml/dataset/stats"),
        simhpcFetch("/ml/models"),
      ]);
      setModelStatus(statusRes);
      setDatasetStats(datasetRes.data);
      setVersions(versionsRes.versions || []);
    } catch {
      toast.error("Failed to load ML dashboard");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 30000);
    return () => clearInterval(interval);
  }, [fetchAllData]);

  const triggerExport = async () => {
    setExporting(true);
    try {
      await simhpcFetch("/ml/export", {
        method: "POST",
        body: JSON.stringify({ quality_level: "production" }),
      });
      toast.success("Training data export started in background");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Export failed");
    } finally {
      setExporting(false);
    }
  };

  const triggerTraining = async () => {
    setTraining(true);
    try {
      await simhpcFetch("/ml/train", {
        method: "POST",
        body: JSON.stringify({}),
      });
      toast.success("Model training started in background");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Training failed");
    } finally {
      setTraining(false);
    }
  };

  const activateVersion = async (versionId: string) => {
    try {
      await simhpcFetch(`/ml/models/${versionId}/activate`, { method: "POST" });
      toast.success(`Activated model version ${versionId}`);
      fetchAllData();
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Failed to activate version");
    }
  };

  if (loading) {
    return <div className="p-8 text-center">Loading ML Intelligence...</div>;
  }

  const moatColor =
    modelStatus?.moat_strength?.includes("STRONG")
      ? "text-emerald-400"
      : modelStatus?.moat_strength?.includes("GROWING")
        ? "text-amber-400"
        : "text-slate-400";

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">ML Intelligence Dashboard</h1>
          <p className="text-slate-400">
            Physics model performance &amp; version control
          </p>
        </div>

        <div className="flex gap-3">
          <Select value={selectedVersion} onValueChange={setSelectedVersion}>
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Select model version" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="latest">Latest Active Model</SelectItem>
              {versions.map((v) => (
                <SelectItem key={v.version_id} value={v.version_id}>
                  {v.version_id} — {v.overall_score.toFixed(2)} • {v.trained_on_runs.toLocaleString()} runs
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button onClick={triggerExport} disabled={exporting} variant="outline">
            {exporting ? "Exporting..." : "Export Data"}
          </Button>
          <Button onClick={triggerTraining} disabled={training}>
            {training ? "Training..." : "Train New Model"}
          </Button>
        </div>
      </div>

      {selectedVersion !== "latest" && (
        <div className="bg-blue-950/30 border border-blue-700 rounded-lg p-4 flex items-center justify-between">
          <div>
            Currently viewing:{" "}
            <span className="font-mono font-semibold">{selectedVersion}</span>
          </div>
          <Button size="sm" onClick={() => activateVersion(selectedVersion)}>
            Activate This Version
          </Button>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Qualified Runs</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">
              {datasetStats?.total_qualified_runs?.toLocaleString() ?? 0}
            </div>
            <p className="text-xs text-slate-500 mt-1">Ready for training</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Latest Model Score</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold text-emerald-400">
              {modelStatus?.latest_model?.overall_score?.toFixed(2) ?? "—"}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              {modelStatus?.latest_model?.version ?? "No model yet"}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Moat Strength</CardTitle>
          </CardHeader>
          <CardContent>
            <div className={`text-3xl font-bold ${moatColor}`}>
              {modelStatus?.moat_strength ?? "BUILDING"}
            </div>
            <p className="text-xs text-slate-500 mt-1">Continuous improvement</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Estimated Examples</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-4xl font-bold">
              {(datasetStats?.estimated_training_examples ?? 0).toLocaleString()}
            </div>
            <p className="text-xs text-slate-500 mt-1">Across all tasks</p>
          </CardContent>
        </Card>
      </div>

      {modelStatus?.performance_trend && modelStatus.performance_trend.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Model Performance Trend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {modelStatus.performance_trend.slice(-6).map((m, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between border-b border-slate-800 pb-3 last:border-0 last:pb-0"
                >
                  <div>
                    <div className="font-mono text-sm">{m.version}</div>
                    <div className="text-xs text-slate-500">
                      {new Date(m.date).toLocaleDateString()}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">{m.mean_accuracy.toFixed(3)}</div>
                    <div className="text-xs text-emerald-400">accuracy</div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold text-emerald-400">
                      {m.overall_score.toFixed(2)}
                    </div>
                    <div className="text-xs text-slate-500">overall score</div>
                  </div>
                  <div className="text-right text-sm font-mono">
                    {m.trained_on_runs.toLocaleString()} runs
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Training Data Status</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-8">
            <div>
              <div className="text-5xl font-bold text-emerald-400">
                {datasetStats?.certified_runs ?? 0}
              </div>
              <div className="text-sm text-slate-400">Certified Runs</div>
            </div>

            <div className="flex-1">
              <div className="flex justify-between text-xs mb-1">
                <span>Progress toward next training milestone</span>
                <span>{datasetStats?.ready_for_training ? "READY" : "Building..."}</span>
              </div>
              <Progress
                value={Math.min(100, ((datasetStats?.total_qualified_runs ?? 0) / 5000) * 100)}
                className="h-2"
              />
            </div>
          </div>
          <p className="text-xs text-slate-500 mt-4">
            {datasetStats?.training_milestone}
          </p>
        </CardContent>
      </Card>

      <div className="text-xs text-slate-500 text-center">
        Real-time updates every 30 seconds — Data from Flywheel + Certificates
      </div>
    </div>
  );
}
