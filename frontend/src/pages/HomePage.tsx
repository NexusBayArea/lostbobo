import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import { useEffect, useRef, Component, ErrorInfo, ReactNode } from 'react';
import {
  Shield,
  Zap,
  Cpu,
  Activity,
  Layers,
  GitBranch,
  BarChart3,
  ArrowRight,
  Box,
  Code2,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PageLayout } from '@/components/PageLayout';

/* ── Error Boundary ──────────────────────────────────── */
interface Props { children: ReactNode }
interface State { hasError: boolean }
class ErrorBoundary extends Component<Props, State> {
  public state: State = { hasError: false };
  public static getDerivedStateFromError(_: Error): State { return { hasError: true }; }
  public componentDidCatch(error: Error, errorInfo: ErrorInfo) { console.error('Uncaught error:', error, errorInfo); }
  public render() {
    if (this.state.hasError) return <div className="p-8 text-center text-red-500">Something went wrong. Please refresh the page.</div>;
    return this.props.children;
  }
}

/* ── Animated Particle Background ─────────────────────── */
function ParticleBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationId: number;
    let particles: Array<{
      x: number; y: number; vx: number; vy: number;
      radius: number; alpha: number;
    }> = [];

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const count = 120;
    for (let i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.5,
        vy: (Math.random() - 0.5) * 0.5,
        radius: Math.random() * 2.2 + 0.8,
        alpha: Math.random() * 0.45 + 0.15,
      });
    }

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      particles.forEach((p) => {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < 0) p.x = canvas.width;
        if (p.x > canvas.width) p.x = 0;
        if (p.y < 0) p.y = canvas.height;
        if (p.y > canvas.height) p.y = 0;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(34, 211, 238, ${p.alpha})`;
        ctx.fill();
      });

      for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
          const dx = particles[i].x - particles[j].x;
          const dy = particles[i].y - particles[j].y;
          const dist = Math.sqrt(dx * dx + dy * dy);
          if (dist < 150) {
            ctx.beginPath();
            ctx.moveTo(particles[i].x, particles[i].y);
            ctx.lineTo(particles[j].x, particles[j].y);
            // Increased opacity from 0.20 to 0.30
            ctx.strokeStyle = `rgba(34, 211, 238, ${0.30 * (1 - dist / 150)})`;
            ctx.stroke();
          }
        }
      }

      animationId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      cancelAnimationFrame(animationId);
      window.removeEventListener('resize', resize);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none"
      style={{ zIndex: 0, opacity: 1 }}
    />
  );
}

/* ── Main Page Component ──────────────────────────────── */
export default function HomePage() {
  return (
    <ErrorBoundary>
      <PageLayout>
        <div className="min-h-screen bg-background text-foreground selection:bg-cyan-500/30 relative">
          <ParticleBackground />

          {/* ── Hero ─────────────────────────────────────────── */}
          <section className="relative overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-br from-cyan-900/20 via-background to-purple-900/10 pointer-events-none" />
            <div className="relative max-w-6xl mx-auto px-6 pt-28 pb-20 text-center" style={{ zIndex: 1 }}>
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
              >
                <Badge className="mb-6 text-xs font-mono tracking-widest border-cyan-500/30 text-cyan-400 bg-cyan-500/10">
                  KERNEL · DISTRIBUTED COMPUTE OS
                </Badge>
                <h1 className="text-4xl md:text-6xl font-bold tracking-tight leading-tight">
                  The Engineering<br />
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-600">
                    Simulation Operating System
                  </span>
                </h1>
                <p className="mt-6 text-lg text-muted-foreground max-w-2xl mx-auto">
                  Not a SaaS. Not a notebook. A deterministic, replayable, GPU‑accelerated
                  execution platform for scientific computing — with a trust fabric that
                  verifies every plugin, every simulation, and every agent interaction.
                </p>
              </motion.div>

              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="mt-10 flex flex-wrap justify-center gap-4"
              >
                <Button size="lg" asChild>
                  <Link to="/dashboard">
                    <Cpu className="mr-2 h-4 w-4" /> Launch Dashboard
                  </Link>
                </Button>
                <Button variant="outline" size="lg" asChild>
                  <a href="https://simhpc.vercel.app/signup">
                    <Activity className="mr-2 h-4 w-4" /> Get Started — Free
                  </a>
                </Button>
              </motion.div>
            </div>
          </section>

          {/* ── Three Pillars ────────────────────────────────── */}
          <section className="max-w-6xl mx-auto px-6 pb-24" style={{ zIndex: 1, position: 'relative' }}>
            <div className="grid md:grid-cols-3 gap-8">
              {[
                { icon: Cpu, title: 'Control Plane', desc: 'Deterministic scheduler, protocol bus, memory fabric, event store, and RAG engine running on CPU nodes. Lightweight models handle routing, compression, and reasoning — so the GPU never wastes cycles on orchestration.' },
                { icon: Zap, title: 'GPU Simulation Plane', desc: 'MFEM + SUNDIALS compiled directly into immutable A40 containers. Stateless workers pull jobs from the kernel queue, run physics, stream telemetry, and return results. No REST. No blocking. No domain logic in the core.' },
                { icon: Shield, title: 'Trust Fabric', desc: 'Clawpassport identity, A2A handshake protocol, runtime behavioural scoring, and Agentwall policy enforcement. Every plugin and agent is verified before it can talk to anything else — cryptographic trust plus live telemetry.' },
              ].map((p) => (
                <div key={p.title} className="rounded-2xl border border-border bg-card/60 p-6 hover:border-cyan-800/40 transition-colors">
                  <p.icon className="h-8 w-8 text-cyan-400 mb-4" />
                  <h3 className="text-xl font-semibold mb-2">{p.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">{p.desc}</p>
                </div>
              ))}
            </div>
          </section>

          {/* ── What's New ───────────────────────────────────── */}
          <section className="border-t border-border bg-muted/30" style={{ zIndex: 1, position: 'relative' }}>
            <div className="max-w-6xl mx-auto px-6 py-20">
              <h2 className="text-2xl font-bold mb-10 flex items-center gap-3">
                <Box className="h-6 w-6 text-cyan-400" />
                From Alpha to Kernel
              </h2>
              <div className="grid md:grid-cols-2 gap-6 text-sm">
                {[
                  'Frozen Plugin ABI with capability registry & skill registry',
                  'Canonical DAG IR – portable, serialisable, orchestrator‑agnostic',
                  'Kernel Scheduler with fairness, budgets, preemption, GPU isolation',
                  'World State Fabric with causal ordering & probabilistic merge',
                  'Memory Fabric (episodic, semantic, execution, causal) with RAG built‑in',
                  'Internal Protocol Bus – no REST between kernel services',
                  'Deterministic Execution Layer with replay manifests & audit certificates',
                  'Clawpassport OSS – plugin identity, handshake, & behavioural trust engine',
                  'WebSocket + SSE telemetry with full tenant isolation',
                  'MFEM & SUNDIALS compiled into immutable A40 Docker images',
                  'Robustness analysis plugin (LHS, Sobol, percentage) with async execution queue',
                  'PDF Report & Certificate generation with SHA‑256 proof stamp',
                ].map((item) => (
                  <div key={item} className="flex items-start gap-3">
                    <GitBranch className="h-4 w-4 text-cyan-500 mt-0.5 shrink-0" />
                    <span className="text-foreground/80">{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* ── For Engineers & AI Builders ──────────────────── */}
          <section className="max-w-6xl mx-auto px-6 pb-24 grid md:grid-cols-2 gap-12" style={{ zIndex: 1, position: 'relative' }}>
            <div>
              <BarChart3 className="h-8 w-8 text-blue-400 mb-4" />
              <h3 className="text-xl font-semibold mb-3">Built for R&D Teams</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Run GPU‑accelerated parameter sweeps with Latin Hypercube, Monte Carlo,
                and Sobol GSA. Receive AI‑generated engineering interpretation reports
                and download tamper‑proof PDF certificates that prove your
                simulation results haven't been altered.
              </p>
            </div>
            <div>
              <Code2 className="h-8 w-8 text-purple-400 mb-4" />
              <h3 className="text-xl font-semibold mb-3">Plugin Ecosystem</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Build domain‑specific plugins (battery chemistry, weather, EV power‑train)
                that run on the SimHPC kernel. Your plugins carry a Clawpassport,
                register capabilities, and communicate securely via the A2A protocol.
                Zero‑trust by default. Open‑source core.
              </p>
            </div>
          </section>

          {/* ── CTA ──────────────────────────────────────────── */}
          <section className="border-t border-border" style={{ zIndex: 1, position: 'relative' }}>
            <div className="max-w-4xl mx-auto px-6 py-20 text-center">
              <Layers className="h-10 w-10 text-cyan-400 mx-auto mb-6" />
              <h2 className="text-2xl font-bold mb-4">
                Ready to run on distributed cloud GPUs?
              </h2>
              <p className="text-muted-foreground mb-8 max-w-xl mx-auto">
                SimHPC deploys as immutable Docker containers — local, RunPod, or future
                Kubernetes clusters. Every run is deterministic, replayable, and verified.
              </p>
              <Button size="lg" asChild>
                <Link to="/dashboard">
                  <ArrowRight className="mr-2 h-4 w-4" /> Try It Now
                </Link>
              </Button>
            </div>
          </section>
        </div>
      </PageLayout>
    </ErrorBoundary>
  );
}
