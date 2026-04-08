import { Cpu } from 'lucide-react';

export function AlphaControlRoom() {
  return (
    <div className="min-h-screen bg-slate-900 text-white p-8">
      <div className="flex items-center gap-3 mb-8">
        <Cpu className="w-8 h-8 text-cyan-500" />
        <h1 className="text-2xl font-bold">Alpha Control Room</h1>
      </div>
      <div className="bg-slate-800 rounded-xl p-6">
        <p className="text-slate-400">Alpha Control Room - Mission Control</p>
      </div>
    </div>
  );
}
