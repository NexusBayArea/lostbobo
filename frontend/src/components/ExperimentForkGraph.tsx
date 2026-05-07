import React from "react";
import ForceGraph2D from "react-force-graph-2d";

interface ExperimentNode {
  experiment_id: string;
  name: string;
  score: number;
  visibility: string;
}

interface ForkLink {
  parent: string;
  child: string;
}

interface ExperimentForkGraphProps {
  experiments: ExperimentNode[];
  forks: ForkLink[];
}

export default function ExperimentForkGraph({ experiments, forks }: ExperimentForkGraphProps) {
  const graphData = {
    nodes: experiments.map((exp) => ({
      id: exp.experiment_id,
      label: exp.name,
      val: Math.sqrt(exp.score || 1) * 6,
      color: exp.visibility === "public" ? "#22c55e" : "#64748b",
    })),
    links: forks.map((fork) => ({
      source: fork.parent,
      target: fork.child,
      label: "forked →",
    })),
  };

  return (
    <div className="w-full h-[500px] bg-slate-950 rounded-xl border border-slate-700">
      <ForceGraph2D
        graphData={graphData}
        nodeLabel="label"
        linkLabel="label"
        nodeRelSize={6}
        linkDirectionalArrowLength={4}
      />
    </div>
  );
}