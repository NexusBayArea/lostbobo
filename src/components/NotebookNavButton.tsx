import { useNavigate, useLocation } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";

export function NotebookNavButton({ isSidebarOpen = true }: { isSidebarOpen?: boolean }) {
  const navigate = useNavigate();
  const location = useLocation();
  const isActive = location.pathname.startsWith("/dashboard/notebook");

  return (
    <button
      onClick={() => window.open("/dashboard/notebook", "_blank")}
      className={`
        group flex items-center gap-3 w-full px-3 py-2.5 rounded-xl text-sm font-medium
        transition-all duration-150
        ${isActive
          ? "bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
          : "text-slate-400 hover:text-white hover:bg-slate-800/60 border border-transparent"
        }
        ${!isSidebarOpen && "justify-center px-2"}
      `}
    >
      {/* Icon */}
      <span className={`shrink-0 transition-colors ${isActive ? "text-cyan-400" : "text-slate-500 group-hover:text-slate-300"}`}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
          <polyline points="14 2 14 8 20 8"/>
          <line x1="16" y1="13" x2="8" y2="13"/>
          <line x1="16" y1="17" x2="8" y2="17"/>
          <polyline points="10 9 9 9 8 9"/>
        </svg>
      </span>

      <AnimatePresence>
        {isSidebarOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex items-center flex-1"
          >
            <span>Experiment Notebook</span>

            {/* NEW badge — remove after first week of launch */}
            {!isActive && (
              <span className="ml-auto text-[9px] font-semibold uppercase tracking-widest px-1.5 py-0.5 rounded bg-cyan-500/15 text-cyan-400 border border-cyan-500/20">
                New
              </span>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </button>
  );
}
