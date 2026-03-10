import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { 
  Mail, 
  Lock, 
  User, 
  ArrowRight, 
  Check, 
  Cpu, 
  BarChart3, 
  FileText, 
  Shield,
  Loader2
} from 'lucide-react';
import { SimHPCLogo } from '@/components/SimHPCLogo';
import { ThemeToggle } from '@/components/ThemeToggle';
import { AnimatedMesh } from '@/components/AnimatedMesh';
import { supabase } from '@/lib/supabase';
import { toast } from 'sonner';

const freeFeatures = [
  { icon: Cpu, text: 'Limited GPU Simulation Access' },
  { icon: BarChart3, text: 'Basic Robustness Analysis' },
  { icon: FileText, text: 'AI-Generated Technical Summary' },
  { icon: Shield, text: 'Secure Cloud Execution' },
];

const notIncluded = [
  'Custom large-scale models',
  'Extended GPU runtime',
  'Batch job execution',
  'Priority support',
  'Exportable advanced reports',
  'API access',
];

export function SignUp() {
  const navigate = useNavigate();
  console.log('SignUp: Component rendering');
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('SignUp: handleSubmit triggered', formData);
    setIsLoading(true);

    try {
      if (!formData.password || formData.password.length < 6) {
        console.warn('SignUp: Password too short');
        throw new Error('Password must be at least 6 characters long');
      }

      console.log('SignUp: Calling supabase.auth.signUp...');
      const { data, error } = await supabase.auth.signUp({
        email: formData.email,
        password: formData.password,
        options: {
          emailRedirectTo: `${window.location.origin}/dashboard`,
          data: {
            full_name: formData.name,
            name: formData.name,
          }
        },
      });

      if (error) {
        console.error('SignUp: Supabase error:', error);
        toast.error(error.message);
      } else {
        console.log('SignUp: Registration successful response:', data);
        if (data.session) {
          toast.success('Registration successful! Welcome to SimHPC.');
          navigate('/dashboard');
        } else {
          toast.success('Registration successful! Please check your email to verify your account.');
          navigate('/signin');
        }
      }
    } catch (err: any) {
      console.error('SignUp: Unexpected error catch:', err);
      toast.error(err.message || 'An unexpected error occurred');
    } finally {
      console.log('SignUp: handleSubmit finished');
      setIsLoading(false);
    }
  };

  const handleGoogleSignUp = async () => {
    console.log('SignUp: handleGoogleSignUp triggered');
    setIsLoading(true);
    try {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/dashboard`,
        },
      });
      if (error) {
        console.error('SignUp: Google OAuth error:', error);
        toast.error(error.message);
      }
    } catch (err) {
      console.error('SignUp: Google OAuth unexpected error:', err);
    } finally {
      setIsLoading(false);
    }
  };
  return (
    <div className="min-h-screen bg-background dark:bg-slate-900 relative overflow-hidden">
      {/* Background */}
      <div className="absolute inset-0 opacity-30 pointer-events-none select-none z-0">
        <AnimatedMesh />
      </div>

      {/* Header */}
      <header className="relative z-10 px-4 sm:px-6 lg:px-8 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <Link to="/">
            <SimHPCLogo size="md" />
          </Link>
          <ThemeToggle />
        </div>
      </header>

      {/* Content */}
      <div className="relative z-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 lg:py-12">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-start">
          {/* Left Column - Form */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-xl p-8">
              <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white mb-4">
                Start With a Controlled Simulation Environment — Free.
              </h1>
              <p className="text-slate-600 dark:text-slate-400 mb-8">
                Experience GPU-accelerated finite element simulation with built-in 
                robustness analysis and AI-generated technical summaries — at no cost.
              </p>

              {/* Google Sign Up */}
              <button
                onClick={handleGoogleSignUp}
                disabled={isLoading}
                className="w-full flex items-center justify-center gap-3 px-6 py-3 border border-slate-300 dark:border-slate-600 rounded-xl text-slate-700 dark:text-slate-300 font-medium hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors mb-6"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path
                    fill="currentColor"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="currentColor"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="currentColor"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
                Continue with Google
              </button>

              {/* Divider */}
              <div className="relative mb-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-slate-200 dark:border-slate-700" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-white dark:bg-slate-800 text-slate-500 dark:text-slate-400">
                    Or with email
                  </span>
                </div>
              </div>

              {/* Email Form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label htmlFor="full_name" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Full Name
                  </label>
                  <div className="relative">
                    <User className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <input
                      id="full_name"
                      name="full_name"
                      type="text"
                      autoComplete="name"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      className="w-full pl-12 pr-4 py-3 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="John Doe"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Email Address
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <input
                      id="email"
                      name="email"
                      type="email"
                      autoComplete="email"
                      value={formData.email}
                      onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                      className="w-full pl-12 pr-4 py-3 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="you@company.com"
                      required
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
                    Password
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                    <input
                      id="password"
                      name="password"
                      type="password"
                      autoComplete="new-password"
                      value={formData.password}
                      onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                      className="w-full pl-12 pr-4 py-3 bg-slate-50 dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      placeholder="••••••••"
                      required
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full flex items-center justify-center gap-2 px-6 py-4 bg-slate-900 dark:bg-white text-white dark:text-slate-900 font-medium rounded-xl hover:bg-slate-800 dark:hover:bg-slate-100 transition-colors disabled:opacity-50"
                >
                  {isLoading ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <>
                      Create Free Account
                      <ArrowRight className="w-5 h-5" />
                    </>
                  )}
                </button>
              </form>

              <p className="mt-6 text-center text-sm text-slate-500 dark:text-slate-400">
                Already have an account?{' '}
                <Link to="/signin" className="text-blue-600 dark:text-blue-400 hover:underline font-medium">
                  Sign In
                </Link>
              </p>
            </div>
          </motion.div>

          {/* Right Column - Features */}
          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.1, ease: [0.22, 1, 0.36, 1] }}
            className="space-y-8"
          >
            {/* What's Included */}
            <div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-6">
                What Free Access Includes
              </h2>
              <div className="grid sm:grid-cols-2 gap-4">
                {freeFeatures.map((feature) => (
                  <div
                    key={feature.text}
                    className="flex items-start gap-3 p-4 bg-green-50 dark:bg-green-900/20 rounded-xl border border-green-100 dark:border-green-800"
                  >
                    <div className="w-8 h-8 rounded-lg bg-green-500 flex items-center justify-center flex-shrink-0">
                      <feature.icon className="w-4 h-4 text-white" />
                    </div>
                    <span className="text-sm text-slate-700 dark:text-slate-300">{feature.text}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* What's Not Included */}
            <div>
              <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-6">
                What Free Access Does Not Include
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400 mb-4">
                Transparency builds trust.
              </p>
              <ul className="space-y-3">
                {notIncluded.map((item) => (
                  <li
                    key={item}
                    className="flex items-center gap-3 text-slate-500 dark:text-slate-400"
                  >
                    <div className="w-5 h-5 rounded-full bg-slate-200 dark:bg-slate-700 flex items-center justify-center">
                      <span className="text-xs">×</span>
                    </div>
                    {item}
                  </li>
                ))}
              </ul>
              <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">
                Upgrade required for production use.
              </p>
            </div>

            {/* Ideal For */}
            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-2xl p-6 border border-blue-100 dark:border-blue-800">
              <h2 className="text-lg font-semibold text-slate-900 dark:text-white mb-4">
                Ideal For
              </h2>
              <ul className="space-y-2">
                {[
                  'Engineering teams evaluating simulation infrastructure',
                  'Consultants testing cloud solver performance',
                  'Startups validating early-stage prototypes',
                  'Researchers exploring robustness workflows',
                ].map((item) => (
                  <li
                    key={item}
                    className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400"
                  >
                    <Check className="w-4 h-4 text-blue-500" />
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
