import React from 'react';
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { PageLayout } from '@/components/PageLayout';

export function Docs() {
  return (
    <PageLayout>
      <div className="pt-32 pb-20 px-6 max-w-4xl mx-auto">
        <header className="mb-12">
          <h1 className="text-4xl font-bold tracking-tight mb-4">Technical Documentation</h1>
          <p className="text-slate-500 italic">Last Updated: March 2026</p>
          <div className="flex gap-4 mt-6 text-sm font-medium text-slate-600">
            <a href="#sundials" className="hover:text-slate-900 transition-colors">SUNDIALS</a> • <a href="#mfem" className="hover:text-slate-900 transition-colors">MFEM</a> • <a href="#glvis" className="hover:text-slate-900 transition-colors">GLVis</a> • <a href="#ai-report" className="hover:text-slate-900 transition-colors">AI Report Generator</a>
          </div>
        </header>

        <ScrollArea className="h-[70vh] rounded-md border border-slate-200 bg-white/50 p-8 shadow-sm">
          <div className="space-y-10">
            
            {/* SUNDIALS */}
            <section id="sundials">
              <h2 className="text-2xl font-semibold mb-4 border-b pb-2 border-slate-200">SUNDIALS Integration in SimHPC</h2>
              <p className="text-lg font-medium mb-2">High-Performance Time Integration for Stiff and Nonlinear Systems</p>
              <p className="leading-relaxed mb-4">
                SimHPC integrates the SUNDIALS suite to provide robust, scalable time integration for stiff 
                ordinary differential equations (ODEs), differential-algebraic equations (DAEs), and nonlinear 
                systems. This integration enables production-grade transient simulations with adaptive stepping, 
                sensitivity analysis, and distributed memory support. The result is stable time evolution 
                under extreme parameter variation — without manual solver tuning.
              </p>
              
              <h3 className="text-xl font-semibold mt-6 mb-2">Background</h3>
              <p className="leading-relaxed mb-4">
                SUNDIALS (Suite of Nonlinear and Differential/Algebraic Equation Solvers) is a widely adopted 
                open-source numerical library designed for solving stiff and non-stiff ODE systems, DAEs, 
                large-scale nonlinear systems, and sensitivity and adjoint problems.
              </p>
              <ul className="list-disc pl-6 space-y-2 text-slate-700 mb-4">
                <li>CVODE</li>
                <li>CVODES</li>
                <li>IDA</li>
                <li>IDAS</li>
                <li>KINSOL</li>
              </ul>

              <h3 className="text-xl font-semibold mt-6 mb-2">Architectural Integration</h3>
              <p className="leading-relaxed mb-4">
                Within SimHPC, MFEM assembles spatial discretizations while SUNDIALS handles temporal integration. 
                GPU acceleration supports linear algebra kernels, and adaptive timestep control is managed dynamically. 
                The solver layer is abstracted through a unified execution interface, allowing parameter sweeps, 
                robustness analysis, and AI-driven stability detection without manual intervention.
              </p>

              <h3 className="text-xl font-semibold mt-6 mb-2">Numerical Capabilities</h3>
              <ul className="list-disc pl-6 space-y-2 text-slate-700 mb-4">
                <li>Adaptive BDF methods for stiff systems</li>
                <li>Variable-order time stepping</li>
                <li>Nonlinear Newton-Krylov solvers</li>
                <li>Jacobian-free methods</li>
                <li>Sensitivity analysis (forward and adjoint)</li>
                <li>Parallel MPI execution</li>
              </ul>

              <h3 className="text-xl font-semibold mt-6 mb-2">Use Cases</h3>
              <ul className="list-disc pl-6 space-y-2 text-slate-700">
                <li>Structural transient analysis</li>
                <li>Thermal diffusion with nonlinear materials</li>
                <li>Fluid-structure interaction</li>
                <li>Reaction-diffusion systems</li>
                <li>Parameterized dynamic systems</li>
              </ul>
            </section>

            <Separator className="bg-slate-200" />

            {/* MFEM */}
            <section id="mfem">
              <h2 className="text-2xl font-semibold mb-4 border-b pb-2 border-slate-200">MFEM Integration in SimHPC</h2>
              <p className="text-lg font-medium mb-2">High-Order Finite Element Infrastructure at Scale</p>
              <p className="leading-relaxed mb-4">
                SimHPC integrates MFEM as its finite element backbone, enabling high-order discretization, 
                adaptive refinement, and scalable parallel computation. This provides numerical accuracy and 
                performance typically reserved for national laboratory computing environments.
              </p>

              <h3 className="text-xl font-semibold mt-6 mb-2">High-Order Discretization</h3>
              <p className="leading-relaxed mb-4">
                SimHPC leverages MFEM's support for Continuous Galerkin methods, Discontinuous Galerkin 
                formulations, Mixed finite element spaces, and Curvilinear elements. High-order elements 
                enable reduced mesh size for equivalent accuracy, improved convergence rates, and better 
                resolution of complex geometries.
              </p>

              <h3 className="text-xl font-semibold mt-6 mb-2">Parallel Performance</h3>
              <p className="leading-relaxed mb-4">
                Through MFEM, domain decomposition is MPI-native, linear systems are integrated with scalable 
                solvers, and GPU backends accelerate matrix assembly. SimHPC automatically allocates compute 
                resources according to problem size and robustness parameters.
              </p>

              <h3 className="text-xl font-semibold mt-6 mb-2">Mesh Handling</h3>
              <ul className="list-disc pl-6 space-y-2 text-slate-700 mb-4">
                <li>STEP / STL import</li>
                <li>Adaptive refinement</li>
                <li>Up to multi-million element meshes (tier dependent)</li>
                <li>On-the-fly mesh validation</li>
              </ul>

              <h3 className="text-xl font-semibold mt-6 mb-2">Engineering Benefits</h3>
              <p className="leading-relaxed">
                By integrating MFEM, engineers gain high-order accuracy without HPC cluster management. 
                Mesh scaling is predictable and solver performance is benchmarkable. SimHPC removes 
                infrastructure friction while preserving numerical rigor.
              </p>
            </section>

            <Separator className="bg-slate-200" />

            {/* GLVis */}
            <section id="glvis">
              <h2 className="text-2xl font-semibold mb-4 border-b pb-2 border-slate-200">GLVis Visualization Pipeline</h2>
              <p className="text-lg font-medium mb-2">Interactive Finite Element Visualization in the Browser</p>
              <p className="leading-relaxed mb-4">
                SimHPC integrates GLVis to provide interactive visualization of finite element solutions 
                directly within a WebGL-enabled browser. This eliminates traditional post-processing 
                dependencies while preserving scientific visualization fidelity.
              </p>

              <h3 className="text-xl font-semibold mt-6 mb-2">Visualization Capabilities</h3>
              <p className="leading-relaxed mb-4">Users can:</p>
              <ul className="list-disc pl-6 space-y-2 text-slate-700 mb-4">
                <li>Inspect scalar and vector fields</li>
                <li>Rotate 3D domains interactively</li>
                <li>Animate time-dependent simulations</li>
                <li>Apply contour and deformation scaling</li>
                <li>Compare parametric variations</li>
              </ul>
              <p className="leading-relaxed mb-4">No local installation required.</p>

              <h3 className="text-xl font-semibold mt-6 mb-2">Engineering Advantages</h3>
              <p className="leading-relaxed mb-4">
                Traditional workflows require exporting data, opening desktop visualization software, 
                and manual post-processing. SimHPC eliminates these steps. Visualization becomes 
                immediate, shareable, and integrated into reporting.
              </p>

              <h3 className="text-xl font-semibold mt-6 mb-2">Robustness Overlay</h3>
              <p className="leading-relaxed">
                GLVis output is integrated with robustness analysis: stability scoring overlays, 
                variation heatmaps, and parameter sensitivity surfaces. Visualization becomes 
                diagnostic — not decorative.
              </p>
            </section>

            <Separator className="bg-slate-200" />

            {/* AI Report Generator */}
            <section id="ai-report">
              <h2 className="text-2xl font-semibold mb-4 border-b pb-2 border-slate-200">AI Report Generator</h2>
              <p className="text-lg font-medium mb-2">Automated Robustness and Engineering Insight Synthesis</p>
              <p className="leading-relaxed mb-4">
                The SimHPC AI Report Generator transforms raw simulation output into structured engineering 
                reports. It analyzes parameter sweeps, stability behavior, solver convergence, and sensitivity 
                patterns to produce concise, decision-ready documentation.
              </p>

              <h3 className="text-xl font-semibold mt-6 mb-2">System Architecture</h3>
              <p className="leading-relaxed mb-4">The AI Report Generator:</p>
              <ol className="list-decimal pl-6 space-y-2 text-slate-700 mb-4">
                <li>Ingests solver metadata</li>
                <li>Analyzes robustness sweeps</li>
                <li>Detects convergence irregularities</li>
                <li>Scores stability regimes</li>
                <li>Synthesizes structured PDF output</li>
              </ol>
              <p className="leading-relaxed mb-4">Reports include executive summary, parameter sensitivity tables, 
              stability heatmaps, solver performance metrics, and recommended parameter ranges.</p>

              <h3 className="text-xl font-semibold mt-6 mb-2">Deterministic Engineering Focus</h3>
              <p className="leading-relaxed mb-4">
                Unlike generic language models, the system operates on structured numerical metadata, 
                uses bounded engineering templates, avoids speculative language, and flags uncertainty 
                explicitly. Reports are technical — not narrative.
              </p>

              <h3 className="text-xl font-semibold mt-6 mb-2">Workflow Impact</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <div className="border border-slate-100 p-4 rounded bg-white">
                  <h4 className="font-bold text-sm uppercase mb-2">Reduces</h4>
                  <p className="text-sm text-slate-600">Manual result summarization, repetitive reporting tasks, inconsistent documentation quality</p>
                </div>
                <div className="border border-slate-100 p-4 rounded bg-white">
                  <h4 className="font-bold text-sm uppercase mb-2">Increases</h4>
                  <p className="text-sm text-slate-600">Auditability, reproducibility, decision velocity</p>
                </div>
              </div>

              <h3 className="text-xl font-semibold mt-6 mb-2">Tier Integration</h3>
              <ul className="list-disc pl-6 space-y-2 text-slate-700">
                <li>Starter Tier 1: Standard PDF synthesis</li>
                <li>Starter Tier 2: Custom branding + expanded robustness analytics</li>
                <li>Enterprise: Integrated compliance documentation support</li>
              </ul>
            </section>

          </div>
        </ScrollArea>

        <footer className="mt-12 pt-8 border-t border-slate-200 text-sm text-slate-500">
          <p>SimHPC reserves the right to update these technical specifications. All simulation outputs remain the sole property of the user.</p>
        </footer>
      </div>
    </PageLayout>
  );
}
