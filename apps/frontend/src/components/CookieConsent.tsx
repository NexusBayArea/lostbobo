import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Cookie, X } from 'lucide-react';
import { Link } from 'react-router-dom';

export function CookieConsent() {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        const consent = localStorage.getItem('cookie-consent');
        if (!consent) {
            const timer = setTimeout(() => setIsVisible(true), 1500);
            return () => clearTimeout(timer);
        }
    }, []);

    const handleAccept = () => {
        localStorage.setItem('cookie-consent', 'accepted');
        setIsVisible(false);
    };

    const handleOptOut = () => {
        localStorage.setItem('cookie-consent', 'opt-out-ca');
        setIsVisible(false);
    };

    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    initial={{ y: 100, opacity: 0 }}
                    animate={{ y: 0, opacity: 1 }}
                    exit={{ y: 100, opacity: 0 }}
                    className="fixed bottom-0 left-0 right-0 z-[100] p-4 md:p-6"
                >
                    <div className="max-w-4xl mx-auto bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-3xl shadow-2xl p-6 md:p-8 flex flex-col md:flex-row items-center gap-6">
                        <div className="w-16 h-16 rounded-2xl bg-amber-500/10 flex items-center justify-center text-amber-500 flex-shrink-0">
                            <Cookie className="w-8 h-8" />
                        </div>
                        <div className="flex-grow text-center md:text-left">
                            <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-2">Respecting Your Privacy</h3>
                            <p className="text-slate-600 dark:text-slate-400 text-sm mb-4">
                                We use cookies to operate SimHPC. See our <Link to="/cookies" className="text-blue-500 hover:underline">Cookie Policy</Link>.
                            </p>
                            <div className="flex items-center justify-center md:justify-start gap-4">
                                <button onClick={handleAccept} className="px-6 py-2.5 bg-blue-600 text-white rounded-xl font-bold hover:bg-blue-700">Accept All</button>
                                <button onClick={handleOptOut} className="px-6 py-2.5 bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-white rounded-xl hover:bg-slate-200">Opt-out</button>
                            </div>
                        </div>
                        <button onClick={() => setIsVisible(false)} className="absolute top-4 right-4 text-slate-400">
                            <X className="w-6 h-6" />
                        </button>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
