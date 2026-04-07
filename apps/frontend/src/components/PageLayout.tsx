import React, { useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Navigation } from './Navigation';
import { Footer } from '@/sections/Footer';

interface PageLayoutProps {
    children: React.ReactNode;
}

export function PageLayout({ children }: PageLayoutProps) {
    const { pathname } = useLocation();

    useEffect(() => {
        window.scrollTo(0, 0);
    }, [pathname]);

    return (
        <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-slate-950 transition-colors duration-300">
            <Navigation />
            <main className="flex-grow">
                {children}
            </main>
            <Footer />
        </div>
    );
}
