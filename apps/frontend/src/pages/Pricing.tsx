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
                <div style={{ textAlign: "center", maxWidth: 640, margin: "0 auto 56px" }}>
                    <div style={{
                        display: "inline-flex",
                        alignItems: "center",
                        gap: 8,
                        background: "rgba(59,130,246,0.1)",
                        border: "1px solid rgba(59,130,246,0.3)",
                        borderRadius: 999,
                        padding: "6px 16px",
                        fontSize: 12,
                        letterSpacing: "0.1em",
                        textTransform: "uppercase",
                        color: "#60A5FA",
                        marginBottom: 24,
                    }}>
                        GPU-Accelerated FEA · Cloud Native
                    </div>
                    <h1 style={{
                        fontSize: "clamp(32px, 5vw, 52px)",
                        fontWeight: 700,
                        lineHeight: 1.1,
                        letterSpacing: "-0.03em",
                        marginBottom: 16,
                        background: "linear-gradient(135deg, #F8FAFC 0%, #94A3B8 100%)",
                        WebkitBackgroundClip: "text",
                        WebkitTextFillColor: "transparent",
                    }}>
                        Simulation with<br />Quantified Confidence
                    </h1>
                    <p style={{ color: "#64748B", fontSize: 17, lineHeight: 1.6, marginBottom: 32 }}>
                        From single-engineer validation to full-scale robustness sweeps.
                        Cancel anytime — no lock-in.
                    </p>

                    {/* Billing toggle */}
                    <div style={{ display: "inline-flex", alignItems: "center", gap: 12, background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 999, padding: "6px 8px 6px 16px" }}>
                        <span style={{ fontSize: 14, color: annual ? "#94A3B8" : "#E2E8F0" }}>Monthly</span>
                        <button
                            onClick={() => setAnnual(!annual)}
                            style={{
                                width: 44, height: 24, borderRadius: 999, border: "none", cursor: "pointer",
                                background: annual ? "#3B82F6" : "rgba(255,255,255,0.15)",
                                position: "relative", transition: "background 0.2s",
                            }}
                        >
                            <div style={{
                                width: 18, height: 18, borderRadius: "50%", background: "#fff",
                                position: "absolute", top: 3,
                                left: annual ? 23 : 3,
                                transition: "left 0.2s",
                                boxShadow: "0 1px 4px rgba(0,0,0,0.3)",
                            }} />
                        </button>
                        <span style={{ fontSize: 14, color: annual ? "#E2E8F0" : "#94A3B8" }}>Annual</span>
                        {annual && (
                            <span style={{
                                fontSize: 11, fontWeight: 700, background: "rgba(16,185,129,0.15)",
                                color: "#34D399", padding: "3px 10px", borderRadius: 999,
                                border: "1px solid rgba(16,185,129,0.3)",
                            }}>Save up to 25%</span>
                        )}
                    </div>
                </div>

                {/* Plans grid */}
                <div style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
                    gap: 20,
                    maxWidth: 1120,
                    margin: "0 auto 80px",
                }}>
                    {plans.map((plan) => (
                        <div key={plan.name} style={{
                            background: plan.badge ? "rgba(15,23,42,0.9)" : "rgba(255,255,255,0.025)",
                            border: `1px solid ${plan.border}`,
                            borderRadius: 20,
                            padding: "32px 28px",
                            position: "relative",
                            boxShadow: plan.badge ? `0 0 60px ${plan.accentLight}, 0 4px 24px rgba(0,0,0,0.4)` : "none",
                            transition: "transform 0.2s, box-shadow 0.2s",
                        }}
                            onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-4px)"; }}
                            onMouseLeave={e => { e.currentTarget.style.transform = "translateY(0)"; }}
                        >
                            {plan.badge && (
                                <div style={{
                                    position: "absolute", top: -13, left: "50%", transform: "translateX(-50%)",
                                    background: `linear-gradient(90deg, #2563EB, #3B82F6)`,
                                    color: "#fff", fontSize: 11, fontWeight: 700, letterSpacing: "0.08em",
                                    textTransform: "uppercase", padding: "5px 18px", borderRadius: 999,
                                    whiteSpace: "nowrap",
                                }}>{plan.badge}</div>
                            )}

                            <div style={{ marginBottom: 24 }}>
                                <p style={{ fontSize: 11, letterSpacing: "0.1em", textTransform: "uppercase", color: plan.accent, marginBottom: 6 }}>{plan.tag}</p>
                                <h2 style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 16 }}>{plan.name}</h2>
                                <div style={{ display: "flex", alignItems: "baseline", gap: 6, marginBottom: 8 }}>
                                    <>
                                        <span style={{ fontSize: 44, fontWeight: 800, letterSpacing: "-0.04em" }}>
                                            ${(annual ? plan.annualPrice : plan.monthlyPrice).toLocaleString()}
                                        </span>
                                        <span style={{ color: "#475569", fontSize: 14 }}>/mo</span>
                                        {annual && <span style={{ color: "#34D399", fontSize: 12, marginLeft: 4 }}>billed annually</span>}
                                    </>
                                </div>
                                <div style={{
                                    background: plan.accentLight,
                                    border: `1px solid ${plan.border}`,
                                    borderRadius: 8,
                                    padding: "10px 14px",
                                }}>
                                    <p style={{ fontSize: 13, fontWeight: 600, color: plan.accent }}>{plan.credits}</p>
                                    <p style={{ fontSize: 11, color: "#475569", marginTop: 2 }}>{plan.overage}</p>
                                </div>
                            </div>

                            <form action="/create-checkout-session" method="POST">
                                <input type="hidden" name="lookup_key" value={plan.lookupKey} />
                                <button type="submit" style={{
                                    width: "100%",
                                    padding: "13px",
                                    borderRadius: 10,
                                    border: plan.ctaStyle === "filled" ? "none" : `1px solid ${plan.border}`,
                                    background: plan.ctaStyle === "filled" ? `linear-gradient(135deg, #2563EB, #3B82F6)` : "transparent",
                                    color: plan.ctaStyle === "filled" ? "#fff" : plan.accent,
                                    fontSize: 14,
                                    fontWeight: 700,
                                    cursor: "pointer",
                                    marginBottom: 28,
                                    letterSpacing: "0.01em",
                                    transition: "opacity 0.15s",
                                }}
                                    onMouseEnter={e => e.currentTarget.style.opacity = "0.85"}
                                    onMouseLeave={e => e.currentTarget.style.opacity = "1"}
                                >
                                    {plan.cta} →
                                </button>
                            </form>

                            <div style={{ borderTop: "1px solid rgba(255,255,255,0.06)", paddingTop: 24 }}>
                                <p style={{ fontSize: 11, letterSpacing: "0.08em", textTransform: "uppercase", color: "#475569", marginBottom: 14 }}>Includes</p>
                                <ul style={{ listStyle: "none", padding: 0, margin: "0 0 20px", display: "flex", flexDirection: "column", gap: 10 }}>
                                    {plan.features.map(f => (
                                        <li key={f} style={{ display: "flex", alignItems: "flex-start", gap: 10, fontSize: 13.5, color: "#CBD5E1", lineHeight: 1.4 }}>
                                            <span style={{ marginTop: 1, flexShrink: 0 }}><CheckIcon color={plan.accent} /></span>
                                            {f}
                                        </li>
                                    ))}
                                </ul>
                                {plan.notIncluded.length > 0 && (
                                    <ul style={{ listStyle: "none", padding: 0, margin: 0, display: "flex", flexDirection: "column", gap: 10 }}>
                                        {plan.notIncluded.map(f => (
                                            <li key={f} style={{ display: "flex", alignItems: "flex-start", gap: 10, fontSize: 13, color: "#334155", lineHeight: 1.4 }}>
                                                <span style={{ marginTop: 1, flexShrink: 0 }}><XIcon /></span>
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
                <div style={{ maxWidth: 820, margin: "0 auto" }}>
                    <div style={{ textAlign: "center", marginBottom: 36 }}>
                        <h3 style={{ fontSize: 24, fontWeight: 700, letterSpacing: "-0.02em", marginBottom: 10 }}>
                            Compute Credit Packs
                        </h3>
                        <p style={{ color: "#475569", fontSize: 15 }}>
                            Pay-as-you-go for burst capacity or one-off projects. Credits never expire.
                        </p>
                    </div>
                    <div style={{
                        display: "grid",
                        gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
                        gap: 16,
                    }}>
                        {creditPacks.map(pack => (
                            <div key={pack.amount} style={{
                                background: pack.popular ? "rgba(59,130,246,0.08)" : "rgba(255,255,255,0.03)",
                                border: `1px solid ${pack.popular ? "rgba(59,130,246,0.4)" : "rgba(255,255,255,0.07)"}`,
                                borderRadius: 16,
                                padding: "24px 20px",
                                textAlign: "center",
                                position: "relative",
                                cursor: "pointer",
                                transition: "transform 0.15s",
                            }}
                                onMouseEnter={e => e.currentTarget.style.transform = "translateY(-2px)"}
                                onMouseLeave={e => e.currentTarget.style.transform = "translateY(0)"}
                            >
                                {pack.popular && (
                                    <div style={{
                                        position: "absolute", top: -10, left: "50%", transform: "translateX(-50%)",
                                        background: "#3B82F6", color: "#fff", fontSize: 10, fontWeight: 700,
                                        letterSpacing: "0.1em", textTransform: "uppercase", padding: "4px 12px", borderRadius: 999,
                                    }}>Best Value</div>
                                )}
                                <p style={{ fontSize: 36, fontWeight: 800, letterSpacing: "-0.04em", color: "#F8FAFC" }}>
                                    {pack.amount.toLocaleString()}
                                </p>
                                <p style={{ color: "#475569", fontSize: 13, marginBottom: 16 }}>compute credits</p>
                                <p style={{ fontSize: 22, fontWeight: 700, color: pack.popular ? "#60A5FA" : "#E2E8F0", marginBottom: 4 }}>
                                    ${pack.price.toLocaleString()}
                                </p>
                                <p style={{ fontSize: 11, color: "#475569" }}>{pack.perCredit} per credit</p>
                            </div>
                        ))}
                    </div>

                    {/* What is a credit callout */}
                    <div style={{
                        marginTop: 32,
                        background: "rgba(255,255,255,0.02)",
                        border: "1px solid rgba(255,255,255,0.06)",
                        borderRadius: 14,
                        padding: "20px 24px",
                        display: "flex",
                        gap: 20,
                        flexWrap: "wrap",
                        alignItems: "center",
                        justifyContent: "center",
                    }}>
                        <span style={{ color: "#475569", fontSize: 13 }}>What's 1 credit?</span>
                        <span style={{ color: "#94A3B8", fontSize: 13 }}>≈ 1 GPU-minute of compute</span>
                        <span style={{ color: "#334155" }}>·</span>
                        <span style={{ color: "#94A3B8", fontSize: 13 }}>A 500K-element mesh run ≈ 4–8 credits</span>
                        <span style={{ color: "#334155" }}>·</span>
                        <span style={{ color: "#94A3B8", fontSize: 13 }}>50-run robustness sweep ≈ 60–120 credits</span>
                    </div>
                </div>

                {/* Bottom trust row */}
                <div style={{
                    display: "flex", flexWrap: "wrap", gap: 24, justifyContent: "center",
                    marginTop: 64, color: "#334155", fontSize: 13,
                }}>
                    {["No setup fees", "Cancel anytime", "SOC 2 in progress", "ITAR-aware architecture", "A40 GPU backbone"].map(t => (
                        <span key={t} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                            <span style={{ color: "#1E3A5F" }}>✦</span> {t}
                        </span>
                    ))}
                </div>
            </div>
        </PageLayout>
    );
}
