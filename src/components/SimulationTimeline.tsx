import React from 'react';
import { useControlRoomStore } from '../store/controlRoomStore';
import { Play, ShieldAlert, GitBranch, FileCheck, Activity } from 'lucide-react';

const icons = {
  START: <Play size={14} />,
  AUDIT: <ShieldAlert size={14} className="text-amber-400" />,
  CLONE: <GitBranch size={14} className="text-blue-400" />,
  CERTIFY: <FileCheck size={14} className="text-emerald-400" />,
  DEFAULT: <Activity size={14} />
};

const getEventType = (type: string, label?: string) => {
  if (label?.toUpperCase().includes('CLONE')) return 'CLONE';
  if (type === 'AUDIT_EVENT' || type === 'DETECTION') return 'AUDIT';
  if (type === 'CERTIFICATION_EVENT' || type === 'VERIFIED') return 'CERTIFY';
  if (label?.toUpperCase().includes('START') || label?.toUpperCase().includes('DISPATCH')) return 'START';
  return 'DEFAULT';
};

export const SimulationTimeline: React.FC = () => {
  const events = useControlRoomStore((state) => state.timeline);
  const { updateSelectedEvent } = useControlRoomStore((state) => state);

  const handleMarkerClick = (event: TimelineEvent) => {
    // When a marker is clicked, update the OperatorConsole with the system state at that timestamp
    updateSelectedEvent(event);
  };

  return (
    <div className="flex items-center w-full bg-[#0a0f1e] p-4 border-b border-slate-800 space-x-2 overflow-x-auto scrollbar-hide">
      {events.length === 0 ? (
        <div className="text-[10px] font-mono text-slate-700">WAITING FOR LIVE TELEMETRY DATA STRIP...</div>
      ) : (
        events.map((event, i) => {
          const eventType = getEventType(event.type, event.label);
          const isFirst = i === 0;
          const isLast = i === events.length - 1;
          
          return (
            <div key={event.id || i} className="flex items-center flex-shrink-0 group cursor-pointer hover:opacity-80 transition-opacity" onClick={() => handleMarkerClick(event)}>
              <div className="flex flex-col items-center">
                <div className={`p-2 rounded-lg border border-slate-700 bg-slate-900 group-hover:border-blue-500 transition-colors`}>
                  {icons[eventType as keyof typeof icons] || icons.DEFAULT}
                </div>
                <span className="mt-1 text-[9px] font-mono uppercase tracking-tighter text-slate-500">
                  {new Date(event.timestamp).toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit' })}
                </span>
                <span className="text-[10px] font-bold text-slate-300">
                  {event.label}
                </span>
              </div>
              {!isLast && (
                <div className="w-4 h-[1px] bg-slate-800 mx-2 mt-[-20px]" />
              )}
            </div>
          );
        })
      )}
    </div>
  );
};
