import React from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, Legend } from 'recharts';

export default function TelemetryChart({ data }) {
  return (
    <div className="h-64 w-full bg-slate-900/50 p-3 rounded-lg border border-slate-800">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="timestamp" stroke="#94a3b8" style={{ fontSize: '10px' }} />
          <YAxis stroke="#94a3b8" style={{ fontSize: '10px' }} domain={['auto', 'auto']} />
          <Tooltip 
            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#475569', color: '#f8fafc', fontSize: '12px' }}
          />
          <Legend wrapperStyle={{ fontSize: '12px' }} />
          <Line type="monotone" dataKey="raw_temperature" stroke="#ef4444" name="Raw Sensor Temp (°C)" dot={true} strokeWidth={2} />
          <Line type="monotone" dataKey="repaired_temperature" stroke="#22c55e" name="AI Self-Healed (°C)" dot={false} strokeWidth={2} strokeDasharray="5 5" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}