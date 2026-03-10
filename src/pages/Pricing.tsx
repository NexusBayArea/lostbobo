import { useState } from "react";
import { PageLayout } from "@/components/PageLayout";

interface Plan {
    name: string;
    tag: string;
    monthlyPrice: number;
    annualPrice: number;
    accent: string;
    accentLight: string;
    border: string;
    badge: string | null;
    credits: string;
    overage: string;
    lookupKey: string;
    features: string[];
    notIncluded: string[];
    cta: string;
    ctaStyle: "outline" | "filled";
}

interface CreditPack {
    amount: number;
    price: number;
    perCredit: string;
    popular?: boolean;
}

const plans: Plan[] = [
    {
        name: "Starter Tier 1",
        tag: "For individuals & small teams",
        monthlyPrice: 150,
        annualPrice: 100,
        accent: "#64748B",
        accentLight: "rgba(100,116,139,0.12)",
        border: "rgba(100,116,139,0.3)",
        badge: null,
        credits: "200 compute credits/mo",
        overage: "$0.55 / additional credit",
        lookupKey: "starter_tier_1",
        features: [
            "Up to 500K-element meshes",
            "5 concurrent simulation runs",
            "Robustness analysis (up to 20 runs)",
            "AI-generated PDF reports",
            "GLVis WebGL visualization",
            "Latin Hypercube & Monte Carlo sampling",
            "Email support",
            "1 user seat",
        ],
        notIncluded: [
            "Priority GPU queue",
            "Custom parameter presets",
            "API access",
            "SSO / team management",
        ],
        cta: "Start Free Trial",
        ctaStyle: "outline",
    },
    {
        name: "Starter Tier 2",
        tag: "For engineering teams",
        monthlyPrice: 500,
        annualPrice: 400,
        accent: "#3B82F6",
        accentLight: "rgba(59,130,246,0.12)",
        border: "rgba(59,130,246,0.5)",
        badge: "Most Popular",
        credits: "800 compute credits/mo",
        overage: "$0.42 / additional credit",
        lookupKey: "starter_tier_2",
        features: [
            "Up to 5M-element meshes",
            "20 concurrent simulation runs",
            "Robustness analysis (up to 50 runs)",
            "AI-generated PDF reports + custom branding",
            "Priority A40 GPU queue",
            "Full REST API access",
            "STEP / STL mesh import",
            "Custom parameter presets",
            "Slack + email support",
            "Up to 5 user seats",
        ],
        notIncluded: [
            "Dedicated GPU instance",
            "SOC 2 / ITAR compliance",
            "On-premise deployment",
        ],
        cta: "Start Free Trial",
        ctaStyle: "filled",
    },
    {
        name: "Enterprise Tier 1",
        tag: "For labs, consultancies & OEMs",
        monthlyPrice: 2000,
        annualPrice: 1500,
        accent: "#8B5CF6",
        accentLight: "rgba(139,92,246,0.12)",
        border: "rgba(139,92,246,0.4)",
        badge: null,
        credits: "Custom compute allocation",
        overage: "Volume discounts available",
        lookupKey: "enterprise_tier_1",
        features: [
            "Unlimited mesh size",
            "Unlimited concurrent runs",
            "Dedicated GPU instance (A40 / H100)",
            "SOC 2 Type II compliance",
            "ITAR/EAR export control support",
            "On-premise or VPC deployment",
            "SSO (SAML 2.0 / OIDC)",
            "SLA: 99.9% uptime guarantee",
            "Custom integrations (NASTRAN, Abaqus export)",
            "Dedicated solutions engineer",
            "Unlimited seats",
        ],
        notIncluded: [],
        cta: "Contact Sales",
        ctaStyle: "outline",
    },
];

const creditPacks: CreditPack[] = [
    { amount: 100, price: 50, perCredit: "$0.50" },
    { amount: 500, price: 220, perCredit: "$0.44", popular: true },
    { amount: 2000, price: 760, perCredit: "$0.38" },
];

const CheckIcon = ({ color }: { color: string }) => (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="7.5" stroke={color} strokeOpacity="0.3" />
        <path d="M5 8l2.2 2.2L11 6" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
);

const XIcon = () => (
    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <circle cx="8" cy="8" r="7.5" stroke="rgba(255,255,255,0.1)" />
        <path d="M6 6l4 4M10 6l-4 4" stroke="rgba(255,255,255,0.2)" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
);

export function Pricing() {
    const [annual, setAnnual] = useState(true);

    return (
        <PageLayout>
            <div className="py-32 px-6">
                {/* Header */}
                <div className="text-center max-w-[640px] mx-auto mb-14">
                    <div className="inline-flex items-center gap-2 bg-blue-500/10 border border-blue-500/30 rounded-full px-4 py-1.5 text-xs tracking-widest uppercase text-blue-400 mb-6">
                        GPU-Accelerated FEA · Cloud Native
                    </div>
                    <h1 className="text-[clamp(32px,5vw,52px)] font-bold leading-[1.1] tracking-tight mb-4 bg-gradient-to-br from-slate-50 to-slate-400 bg-clip-text text-transparent">
                        Simulation with<br />Quantified Confidence
                    </h1>
                    <p className="text-slate-500 text-[17px] leading-relaxed mb-8">
                        From single-engineer validation to full-scale robustness sweeps.
                        Cancel anytime â€” no lock-in.
                    </p>

                    {/* Billing toggle */}
                    <div className="inline-flex items-center gap-3 bg-white/5 border border-white/10 rounded-full p-1.5 pl-4">
                        <span className={`text-sm ${annual ? 'text-slate-500' : 'text-slate-900'}`}>Monthly</span>
                        <button
                            onClick={() => setAnnual(!annual)}
                            className={`w-11 h-6 rounded-full relative transition-colors duration-200 ${annual ? 'bg-blue-600' : 'bg-slate-300'}`}
                        >
                            <div className={`w-4.5 h-4.5 rounded-full bg-white absolute top-0.75 transition-all duration-200 shadow-[0_1px_4px_rgba(0,0,0,0.3)] ${annual ? 'left-[23px]' : 'left-0.75'}`} />
                        </button>
                        <span className={`text-sm ${annual ? 'text-slate-900' : 'text-slate-500'}`}>Annual</span>
                        {annual && (
                            <span className="text-[11px] font-bold bg-emerald-500/15 text-emerald-600 px-2.5 py-0.75 rounded-full border border-emerald-500/30">
                                Save up to 25%
                            </span>
                        )}
                    </div>
                </div>

                {/* Plans grid */}
                <div className="grid grid-cols-[repeat(auto-fit,minmax(280px,1fr))] gap-5 max-w-[1120px] mx-auto mb-20">
                    {plans.map((plan) => (
                        <div 
                            key={plan.name} 
                            className={`rounded-[20px] p-8 relative transition-all duration-200 hover:-translate-y-1 ${
                                plan.badge 
                                ? 'bg-slate-900/90 border-blue-500/50 shadow-[0_0_60px_rgba(59,130,246,0.12),0_4px_24px_rgba(0,0,0,0.4)]' 
                                : 'bg-white/[0.025] border-white/10'
                            }`}
                            style={{ border: `1px solid ${plan.border}` }}
                        >
                            {plan.badge && (
                                <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-blue-700 to-blue-500 text-white text-[11px] font-bold tracking-widest uppercase px-4.5 py-1.5 rounded-full whitespace-nowrap">
                                    {plan.badge}
                                </div>
                            )}

                            <div className="mb-6">
                                <p className="text-[11px] tracking-widest uppercase mb-1.5" style={{ color: plan.accent }}>{plan.tag}</p>
                                <h2 className="text-[26px] font-bold tracking-tight mb-4">{plan.name}</h2>
                                <div className="flex items-baseline gap-1.5 mb-2">
                                <span className="text-[44px] font-extrabold tracking-tighter">
                                    ${(annual ? plan.annualPrice : plan.monthlyPrice).toLocaleString()}
                                </span>
                                    <span className="text-slate-500 text-sm">/mo</span>
                                    {annual && <span className="text-emerald-400 text-xs ml-1">billed annually</span>}
                                </div>
                                <div 
                                    className="rounded-lg p-3 border"
                                    style={{ 
                                        backgroundColor: plan.accentLight, 
                                        borderColor: plan.border 
                                    }}
                                >
                                    <p className="text-[13px] font-semibold" style={{ color: plan.accent }}>{plan.credits}</p>
                                    <p className="text-[11px] text-slate-500 mt-0.5">{plan.overage}</p>
                                </div>
                            </div>

                            <form action="/create-checkout-session" method="POST">     
                                <input type="hidden" name="lookup_key" value={plan.lookupKey} />
                                <button 
                                    type="submit" 
                                    className={`w-full p-3.25 rounded-xl text-sm font-bold tracking-wide mb-7 transition-opacity duration-150 hover:opacity-85 ${
                                        plan.ctaStyle === "filled" 
                                        ? 'bg-gradient-to-br from-blue-700 to-blue-500 text-white' 
                                        : 'bg-transparent border'
                                    }`}
                                    style={plan.ctaStyle === "outline" ? { borderColor: plan.border, color: plan.accent } : {}}
                                >
                                    {plan.cta} â†’
                                </button>
                            </form>

                            <div className="border-t border-white/5 pt-6">
                                <p className="text-[11px] tracking-widest uppercase text-slate-500 mb-3.5">Includes</p>
                                <ul className="list-none p-0 m-0 mb-5 flex flex-col gap-2.5">
                                    {plan.features.map(f => (
                                        <li key={f} className="flex items-start gap-2.5 text-[13.5px] text-slate-300 leading-relaxed">        
                                            <span className="mt-1 flex-shrink-0"><CheckIcon color={plan.accent} /></span>
                                            {f}
                                        </li>
                                    ))}
                                </ul>
                                {plan.notIncluded.length > 0 && (
                                    <ul className="list-none p-0 m-0 flex flex-col gap-2.5">
                                        {plan.notIncluded.map(f => (
                                            <li key={f} className="flex items-start gap-2.5 text-[13px] text-slate-700 leading-relaxed">      
                                                <span className="mt-1 flex-shrink-0"><XIcon /></span>
                                                {f}
                                            </li>
                                        ))}
                                    </ul>
                                )}
                            </div>
                        </div>
                    ))}
                </div>

                {/* Credit Packs */}
                <div className="max-w-[820px] mx-auto">
                    <div className="text-center mb-9">
                        <h3 className="text-2xl font-bold tracking-tight mb-2.5">
                            Compute Credit Packs
                        </h3>
                        <p className="text-slate-500 text-[15px]">
                            Pay-as-you-go for burst capacity or one-off projects. Credits never expire.
                        </p>
                    </div>
                    <div className="grid grid-cols-[repeat(auto-fit,minmax(220px,1fr))] gap-4">
                        {creditPacks.map(pack => (
                            <div 
                                key={pack.amount} 
                                className={`rounded-2xl p-6 text-center relative cursor-pointer transition-transform duration-150 hover:-translate-y-0.5 border ${
                                    pack.popular 
                                    ? 'bg-blue-500/10 border-blue-500/40' 
                                    : 'bg-white/[0.03] border-white/10'
                                }`}
                            >
                                {pack.popular && (
                                    <div className="absolute -top-2.5 left-1/2 -translate-x-1/2 bg-blue-500 text-white text-[10px] font-bold tracking-widest uppercase px-3 py-1 rounded-full">
                                        Best Value
                                    </div>
                                )}
                                <p className="text-[36px] font-extrabold tracking-tighter">
                                    {pack.amount.toLocaleString()}
                                </p>
                                <p className="text-slate-600 text-[13px] mb-4">compute credits</p>
                                <p className={`text-[22px] font-bold mb-1 ${pack.popular ? 'text-blue-600' : 'text-slate-700'}`}>
                                    ${pack.price.toLocaleString()}
                                </p>
                                <p className="text-[11px] text-slate-500">{pack.perCredit} per credit</p>
                            </div>
                        ))}
                    </div>

                    {/* What is a credit callout */}
                    <div className="mt-8 bg-white/[0.02] border border-white/5 rounded-xl p-5 flex gap-5 flex-wrap items-center justify-center">
                        <span className="text-slate-500 text-[13px]">What's 1 credit?</span>
                                <span className="text-slate-400 text-[13px]">≈ 1 GPU-minute of compute</span>
                        <span className="text-slate-800">·</span>
                        <span className="text-slate-400 text-[13px]">A 500K-element mesh run ≈ 4–8 credits</span>
                        <span className="text-slate-800">·</span>
                        <span className="text-slate-400 text-[13px]">50-run robustness sweep ≈ 60–120 credits</span>
                    </div>
                </div>

                {/* Bottom trust row */}
                <div className="flex flex-wrap gap-6 justify-center mt-16 text-slate-700 text-[13px]">
                    {["No setup fees", "Cancel anytime", "SOC 2 in progress", "ITAR-aware architecture", "A40 GPU backbone"].map(t => (
                        <span key={t} className="flex items-center gap-1.5">
                            <span className="text-slate-800 text-xs">✦</span> {t}
                        </span>
                    ))}
                </div>
            </div>
        </PageLayout>
    );
}