import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { supabase } from '@/lib/supabase';

const RiskDashboard = ({ strategyId }: { strategyId: string }) => {
  const [riskData, setRiskData] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    const fetchRiskState = async () => {
      const { data: state } = await supabase
        .from('risk_state')
        .select('*')
        .eq('run_id', strategyId)
        .order('updated_at', { ascending: true });

      const { data: events } = await supabase
        .from('risk_events')
        .select('*')
        .eq('run_id', strategyId)
        .limit(5);

      if (state) setRiskData(state);
      if (events) setAlerts(events);
    };

    fetchRiskState();
  }, [strategyId]);

  return (
    <div className="space-y-6 p-6 bg-white rounded-2xl shadow-sm border">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-red-50 rounded-lg border border-red-100">
          <p className="text-sm text-red-600 font-medium">Current Drawdown</p>
          <p className="text-2xl font-bold text-red-700">
            {riskData.length > 0 ? (riskData[riskData.length - 1]?.drawdown?.toFixed(2) || 0) : 0}%
          </p>
        </div>
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-100">
          <p className="text-sm text-blue-600 font-medium">Value at Risk (VaR)</p>
          <p className="text-2xl font-bold text-blue-700">
            {riskData.length > 0 ? (riskData[riskData.length - 1]?.var_95?.toFixed(2) || 0) : 0}
          </p>
        </div>
        <div className="p-4 bg-orange-50 rounded-lg border border-orange-100">
          <p className="text-sm text-orange-600 font-medium">Active Risk Events</p>
          <p className="text-2xl font-bold text-orange-700">{alerts.length}</p>
        </div>
      </div>

      <div className="h-64 w-full">
        <h4 className="text-sm font-semibold mb-4 text-slate-700">Drawdown Curve (Stateful Safety)</h4>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={riskData}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="updated_at" hide />
            <YAxis />
            <Tooltip />
            <Area type="monotone" dataKey="drawdown" stroke="#ef4444" fill="#fee2e2" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="mt-4">
        <h4 className="text-sm font-semibold mb-2 text-slate-700">Recent Risk Violations</h4>
        <div className="divide-y border rounded-lg">
          {alerts.map((alert) => (
            <div key={alert.id} className="p-3 text-sm flex justify-between items-center">
              <span className="font-mono text-xs text-slate-500">{new Date(alert.created_at).toLocaleTimeString()}</span>
              <span className="font-medium text-red-600">{alert.event_type}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default RiskDashboard;
