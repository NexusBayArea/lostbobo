import React from 'react';
import { Link } from 'react-router-dom';

const LegalLayout: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => {
  return (
    <div className="min-h-screen bg-background dark:bg-slate-950 py-12 px-4 sm:px-6 lg:px-8 font-sans">
      <div className="max-w-3xl mx-auto bg-white dark:bg-slate-900 p-8 border border-slate-200 dark:border-slate-800 rounded-xl shadow-sm">
        <Link to="/" className="text-cyan-600 dark:text-cyan-400 hover:text-cyan-800 dark:hover:text-cyan-300 text-sm font-medium mb-8 inline-block">
          &larr; Back to SimHPC
        </Link>
        <h1 className="text-3xl font-bold text-slate-900 dark:text-white mb-6">{title}</h1>
        <div className="prose prose-blue max-w-none text-slate-600 dark:text-slate-400 space-y-6">
          {children}
        </div>
        <footer className="mt-12 pt-6 border-t border-slate-100 dark:border-slate-800 text-sm text-slate-400">
          © 2026 SimHPC. All rights reserved. Managed via Infisical & Supabase.
        </footer>
      </div>
    </div>
  );
};

export default LegalLayout;
