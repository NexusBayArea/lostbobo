// frontend/src/components/LineageDashboard.tsx
import React, { useEffect, useState } from "react";
import LineageVisualizer from "./LineageVisualizer";

interface ExecutionSummary {
  execution_id: string;
  total_events: number;
  last_event: string;
  source_types: string[];
}

export default function LineageDashboard() {
  const [executions, setExecutions] = useState<ExecutionSummary[]>([]);
  const [selectedExecutionId, setSelectedExecutionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadExecutions = async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/lineage/executions?limit=50");
      const data = await res.json();
      setExecutions(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadExecutions();
  }, []);

  if (selectedExecutionId) {
    return (
      <div className="flex flex-col h-screen">
        <div className="p-4 border-b flex items-center justify-between bg-white">
          <h1 className="text-xl font-semibold">
            Execution: {selectedExecutionId.slice(0, 8)}...
          </h1>
          <button
            onClick={() => setSelectedExecutionId(null)}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg text-sm"
          >
            ← Back to List
          </button>
        </div>
        <LineageVisualizer executionId={selectedExecutionId} />
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Execution Lineage Dashboard</h1>
        <button
          onClick={loadExecutions}
          className="px-5 py-2 bg-blue-600 text-white rounded-xl hover:bg-blue-700"
        >
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="text-center py-12">Loading executions...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {executions.map((exec) => (
            <div
              key={exec.execution_id}
              className="border border-gray-200 rounded-3xl p-6 hover:shadow-xl cursor-pointer transition-shadow"
              onClick={() => setSelectedExecutionId(exec.execution_id)}
            >
              <div className="font-mono text-sm text-gray-500 mb-1">
                {exec.execution_id.slice(0, 8)}...
              </div>
              <div className="text-2xl font-semibold mb-2">
                {exec.total_events} events
              </div>
              <div className="text-sm text-gray-600 mb-4">
                Last event: {new Date(exec.last_event).toLocaleString()}
              </div>
              <div className="flex flex-wrap gap-2">
                {exec.source_types.map((type) => (
                  <span
                    key={type}
                    className="px-3 py-1 bg-gray-100 text-xs font-medium rounded-2xl"
                  >
                    {type}
                  </span>
                ))}
              </div>
              <button className="mt-6 w-full py-3 bg-black text-white rounded-2xl text-sm font-medium">
                View Full Lineage Graph →
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
