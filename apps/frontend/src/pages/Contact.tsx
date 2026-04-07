import { PageLayout } from '@/components/PageLayout';
import { Mail, Cpu, Info, HelpCircle } from 'lucide-react';

export function Contact() {
    return (
        <PageLayout>
            <div className="pt-32 pb-20 px-6 max-w-4xl mx-auto">
                <h1 className="text-4xl font-bold mb-6 text-slate-900 dark:text-white">Contact Us</h1>
                <p className="text-lg text-slate-600 dark:text-slate-400 mb-12">
                    Get in touch with the SimHPC team for sales, information, or support.
                </p>
                
                <div className="grid gap-6">
                    <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-6">
                        <div className="flex items-center gap-4 mb-4">
                            <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded-lg">
                                <Cpu className="w-6 h-6 text-slate-600 dark:text-slate-400" />
                            </div>
                            <div>
                                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Sales</h2>
                                <p className="text-slate-600 dark:text-slate-400">For pricing inquiries and enterprise solutions</p>
                            </div>
                        </div>
                        <a href="mailto:deploy@simhpc.com" className="text-blue-600 dark:text-blue-400 font-semibold hover:underline">
                            deploy@simhpc.com
                        </a>
                    </div>

                    <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-6">
                        <div className="flex items-center gap-4 mb-4">
                            <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded-lg">
                                <Info className="w-6 h-6 text-slate-600 dark:text-slate-400" />
                            </div>
                            <div>
                                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Information</h2>
                                <p className="text-slate-600 dark:text-slate-400">For general inquiries and questions</p>
                            </div>
                        </div>
                        <a href="mailto:info@simhpc.com" className="text-blue-600 dark:text-blue-400 font-semibold hover:underline">
                            info@simhpc.com
                        </a>
                    </div>

                    <div className="border border-slate-200 dark:border-slate-700 rounded-lg p-6">
                        <div className="flex items-center gap-4 mb-4">
                            <div className="p-3 bg-slate-100 dark:bg-slate-800 rounded-lg">
                                <HelpCircle className="w-6 h-6 text-slate-600 dark:text-slate-400" />
                            </div>
                            <div>
                                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">Support</h2>
                                <p className="text-slate-600 dark:text-slate-400">For technical support and troubleshooting</p>
                            </div>
                        </div>
                        <a href="mailto:support@simhpc.com" className="text-blue-600 dark:text-blue-400 font-semibold hover:underline">
                            support@simhpc.com
                        </a>
                    </div>
                </div>
            </div>
        </PageLayout>
    );
}
