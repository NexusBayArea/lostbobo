import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Loader2, ShieldCheck, AlertTriangle, Zap } from 'lucide-react';
import { PageLayout } from '@/components/PageLayout';

type DemoState = 'validating' | 'success' | 'expired' | 'invalid' | 'limit_reached';

export function DemoAccess() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const [state, setState] = useState<DemoState>('validating');
  const [message, setMessage] = useState('Validating your demo access...');
  const [demoInfo, setDemoInfo] = useState<{ remaining: number; limit: number; email?: string } | null>(null);

  useEffect(() => {
    if (!token) {
      setState('invalid');
      setMessage('No demo token provided.');
      return;
    }

    const validateToken = async () => {
      try {
        const API_BASE = import.meta.env.VITE_API_URL || 'https://40n3yh92ugakps-8000.proxy.runpod.net/api/v1';
        const response = await fetch(`${API_BASE}/demo/magic-link`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token }),
        });

        const data = await response.json();

        if (data.valid) {
          setState('success');
          setMessage('Access granted! Redirecting to your dashboard...');
          setDemoInfo({
            remaining: data.remaining,
            limit: data.usage_limit,
            email: data.email,
          });

          // Store demo token for session tracking
          localStorage.setItem('demo_token', token);
          localStorage.setItem('demo_remaining', String(data.remaining));
          localStorage.setItem('demo_limit', String(data.usage_limit));
          localStorage.setItem('demo_active', 'true');

          // Redirect after animation
          setTimeout(() => {
            navigate('/dashboard');
          }, 2500);
        } else {
          if (data.reason === 'limit_reached') {
            setState('limit_reached');
            setMessage('You have used all available demo simulations.');
          } else if (data.reason === 'expired') {
            setState('expired');
            setMessage('This demo link has expired.');
          } else {
            setState('invalid');
            setMessage(data.message || 'Invalid or unrecognized demo link.');
          }
        }
      } catch (error) {
        console.error('Demo validation error:', error);
        setState('invalid');
        setMessage('Unable to validate demo link. Please try again.');
      }
    };

    validateToken();
  }, [token, navigate]);

  return (
    <PageLayout>
      <div className="min-h-[80vh] flex items-center justify-center px-4">
        <motion.div
          initial={{ opacity: 0, y: 30, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.5, ease: [0.22, 1, 0.36, 1] }}
          className="w-full max-w-md"
        >
          {/* Card Container */}
          <div className="relative bg-white dark:bg-slate-800 rounded-3xl border border-slate-200 dark:border-slate-700 shadow-2xl shadow-blue-500/5 overflow-hidden">
            {/* Gradient Top Bar */}
            <div className={`h-1.5 w-full ${
              state === 'success' ? 'bg-gradient-to-r from-emerald-400 via-green-500 to-teal-500' :
              state === 'validating' ? 'bg-gradient-to-r from-blue-400 via-indigo-500 to-purple-500' :
              'bg-gradient-to-r from-orange-400 via-red-500 to-pink-500'
            }`} />

            <div className="px-8 py-10 text-center">
              {/* Status Icon */}
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
                className="mb-6"
              >
                {state === 'validating' && (
                  <div className="w-20 h-20 mx-auto rounded-full bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center">
                    <Loader2 className="w-10 h-10 text-blue-500 animate-spin" />
                  </div>
                )}
                {state === 'success' && (
                  <div className="w-20 h-20 mx-auto rounded-full bg-emerald-50 dark:bg-emerald-900/30 flex items-center justify-center">
                    <motion.div
                      initial={{ scale: 0 }}
                      animate={{ scale: 1 }}
                      transition={{ delay: 0.3, type: 'spring', stiffness: 300, damping: 15 }}
                    >
                      <ShieldCheck className="w-10 h-10 text-emerald-500" />
                    </motion.div>
                  </div>
                )}
                {(state === 'expired' || state === 'limit_reached') && (
                  <div className="w-20 h-20 mx-auto rounded-full bg-amber-50 dark:bg-amber-900/30 flex items-center justify-center">
                    <AlertTriangle className="w-10 h-10 text-amber-500" />
                  </div>
                )}
                {state === 'invalid' && (
                  <div className="w-20 h-20 mx-auto rounded-full bg-red-50 dark:bg-red-900/30 flex items-center justify-center">
                    <AlertTriangle className="w-10 h-10 text-red-500" />
                  </div>
                )}
              </motion.div>

              {/* Title */}
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white mb-2">
                {state === 'validating' && 'Verifying Access'}
                {state === 'success' && 'Welcome to SimHPC'}
                {state === 'expired' && 'Demo Expired'}
                {state === 'limit_reached' && 'Demo Complete'}
                {state === 'invalid' && 'Invalid Link'}
              </h1>

              {/* Message */}
              <p className="text-slate-500 dark:text-slate-400 text-sm leading-relaxed mb-6">
                {message}
              </p>

              {/* Success Info */}
              {state === 'success' && demoInfo && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                  className="bg-emerald-50 dark:bg-emerald-900/20 border border-emerald-100 dark:border-emerald-800 rounded-xl p-4 mb-4"
                >
                  <div className="flex items-center justify-center gap-2 text-emerald-700 dark:text-emerald-300">
                    <Zap className="w-4 h-4" />
                    <span className="text-sm font-semibold">
                      {demoInfo.remaining} simulation runs available
                    </span>
                  </div>
                </motion.div>
              )}

              {/* Progress Bar for validating */}
              {state === 'validating' && (
                <div className="w-full h-1 bg-slate-100 dark:bg-slate-700 rounded-full overflow-hidden">
                  <motion.div
                    initial={{ width: '0%' }}
                    animate={{ width: '80%' }}
                    transition={{ duration: 2, ease: 'easeInOut' }}
                    className="h-full bg-gradient-to-r from-blue-500 to-indigo-500 rounded-full"
                  />
                </div>
              )}

              {/* Expired / Limit Reached CTA */}
              {(state === 'expired' || state === 'limit_reached') && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                  className="space-y-3"
                >
                  <a
                    href="mailto:deploy@simhpc.com?subject=Request%20Extended%20Demo%20Access"
                    className="block w-full py-3 px-6 bg-slate-900 dark:bg-blue-600 text-white font-medium rounded-xl hover:bg-slate-800 dark:hover:bg-blue-700 transition-colors text-center"
                  >
                    Request More Access
                  </a>
                  <a
                    href="/pricing"
                    className="block w-full py-3 px-6 bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 font-medium rounded-xl hover:bg-slate-200 dark:hover:bg-slate-600 transition-colors text-center"
                  >
                    View Plans
                  </a>
                </motion.div>
              )}

              {/* Invalid CTA */}
              {state === 'invalid' && (
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.3 }}
                >
                  <a
                    href="/contact"
                    className="block w-full py-3 px-6 bg-slate-900 dark:bg-blue-600 text-white font-medium rounded-xl hover:bg-slate-800 dark:hover:bg-blue-700 transition-colors text-center"
                  >
                    Contact Support
                  </a>
                </motion.div>
              )}
            </div>

            {/* Footer */}
            <div className="px-8 py-4 bg-slate-50 dark:bg-slate-900/50 border-t border-slate-100 dark:border-slate-700">
              <p className="text-xs text-slate-400 dark:text-slate-500 text-center">
                SimHPC — GPU-Accelerated Finite Element Simulation
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </PageLayout>
  );
}
