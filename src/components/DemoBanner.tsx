import { useState, useEffect } from 'react';

export function DemoBanner() {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(false), 10000);
    return () => clearTimeout(timer);
  }, []);

  if (!visible) return null;

  return (
    <div className="bg-cyan-500/10 border border-cyan-500/20 rounded-xl px-4 py-3 text-center text-sm text-cyan-400">
      Demo mode — Sign in for full access
      <button onClick={() => setVisible(false)} className="ml-2 text-cyan-300 hover:text-cyan-200">✕</button>
    </div>
  );
}
