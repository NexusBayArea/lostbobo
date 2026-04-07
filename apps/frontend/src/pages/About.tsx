import { motion } from 'framer-motion';
import { PageLayout } from '@/components/PageLayout';
import { Users, Cpu, Shield, Globe } from 'lucide-react';

export function About() {
    return (
        <PageLayout>
            <div className="pt-32 pb-20 px-6 max-w-6xl mx-auto">
                <h1 className="text-4xl font-bold mb-6 text-slate-900 dark:text-white">About SimHPC</h1>
                <div className="space-y-4 text-lg text-slate-600 dark:text-slate-400">
                    <p>Engineering is increasingly simulated before it is built.</p>
                    <p>But simulation tools haven't evolved at the same pace as the systems they model.</p>
                    <p>SimHPC turns high-performance simulation into programmable infrastructure; combining high-order finite elements, adaptive time integration, GPU-backed compute, and automated robustness analysis into a single cloud-native platform.</p>
                    <p>No cluster management.</p>
                    <p>No solver tuning rituals.</p>
                    <p>No manual report writing.</p>
                    <p>Just reproducible results and measurable stability.</p>
                    <p>We believe robustness should be standard, not an afterthought.</p>
                    <p>We believe simulation should integrate like software, not operate like legacy desktop tooling.</p>
                    <p>SimHPC is built for teams that ship hardware, design complex systems, and need signal; not guesswork.</p>
                    <p className="font-semibold text-slate-900 dark:text-white">Run simulations.</p>
                    <p className="font-semibold text-slate-900 dark:text-white">Measure robustness.</p>
                    <p className="font-semibold text-slate-900 dark:text-white">Deploy with confidence.</p>
                </div>
            </div>
        </PageLayout>
    );
}
