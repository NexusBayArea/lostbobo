import { useRef } from 'react';
import { motion, useInView } from 'framer-motion';
import { Check, X } from 'lucide-react';
import { Link } from 'react-router-dom';

const plans = [
  {
    name: 'Starter',
    description: 'Rapid Engineering Answers',
    price: 299,
    priceUnit: '/month',
    features: [
      '5 simulations per month',
      'Up to 100K mesh elements',
      'Basic visualization',
      'Email support',
      'Community access',
    ],
    notIncluded: [
      'Robustness analysis',
      'AI-generated reports',
      'API access',
      'Priority support',
    ],
    cta: 'Get Started',
    highlighted: false,
  },
  {
    name: 'Professional',
    description: 'Engineering Confidence',
    price: 499,
    priceUnit: '/month',
    features: [
      '25 simulations per month',
      'Up to 2M mesh elements',
      'Advanced visualization',
      'Robustness analysis',
      'AI-generated reports',
      'Priority email support',
      'Export capabilities',
    ],
    notIncluded: [
      'API access',
      'Dedicated support',
    ],
    cta: 'Start Free Trial',
    highlighted: true,
  },
  {
    name: 'Enterprise',
    description: 'Simulation Infrastructure at Scale',
    price: null,
    priceUnit: 'Custom',
    features: [
      'Unlimited simulations',
      'Unlimited mesh elements',
      'Full feature access',
      'API access',
      'Dedicated support',
      'Custom integrations',
      'SLA guarantee',
      'On-premise option',
    ],
    notIncluded: [],
    cta: 'Contact Sales',
    highlighted: false,
  },
];

export function Pricing() {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, margin: '-100px' });

  return (
    <section
      id="pricing"
      ref={ref}
      className="py-24 lg:py-32 bg-background dark:bg-slate-900"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={isInView ? { opacity: 1, y: 0 } : {}}
          transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
          className="text-center max-w-3xl mx-auto mb-16"
        >
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold text-slate-900 dark:text-white tracking-tight mb-6">
            Simple, Transparent Pricing
          </h2>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            Choose the plan that fits your simulation needs. 
            Robustness Analysis included in Professional and above.
          </p>
        </motion.div>

        {/* Pricing Cards */}
        <div className="grid lg:grid-cols-3 gap-8">
          {plans.map((plan, index) => (
            <motion.div
              key={plan.name}
              initial={{ opacity: 0, y: 40 }}
              animate={isInView ? { opacity: 1, y: 0 } : {}}
              transition={{
                duration: 0.7,
                delay: index * 0.1,
                ease: [0.22, 1, 0.36, 1],
              }}
              className={`relative rounded-2xl ${
                plan.highlighted
                  ? 'bg-slate-900 dark:bg-white border-2 border-blue-500'
                  : 'bg-slate-50 dark:bg-slate-800 border border-slate-200 dark:border-slate-700'
              } p-8`}
            >
              {/* Popular Badge */}
              {plan.highlighted && (
                <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                  <span className="inline-flex items-center px-4 py-1 rounded-full bg-blue-500 text-white text-sm font-medium">
                    Most Popular
                  </span>
                </div>
              )}

              {/* Plan Header */}
              <div className="mb-6">
                <h3
                  className={`text-xl font-semibold mb-2 ${
                    plan.highlighted
                      ? 'text-white dark:text-slate-900'
                      : 'text-slate-900 dark:text-white'
                  }`}
                >
                  {plan.name}
                </h3>
                <p
                  className={`text-sm ${
                    plan.highlighted
                      ? 'text-slate-300 dark:text-slate-500'
                      : 'text-slate-500 dark:text-slate-400'
                  }`}
                >
                  {plan.description}
                </p>
              </div>

              {/* Price */}
              <div className="mb-8">
                {plan.price ? (
                  <div className="flex items-baseline gap-1">
                    <span
                      className={`text-4xl font-bold ${
                        plan.highlighted
                          ? 'text-white dark:text-slate-900'
                          : 'text-slate-900 dark:text-white'
                      }`}
                    >
                      ${plan.price}
                    </span>
                    <span
                      className={`text-sm ${
                        plan.highlighted
                          ? 'text-slate-300 dark:text-slate-500'
                          : 'text-slate-500 dark:text-slate-400'
                      }`}
                    >
                      {plan.priceUnit}
                    </span>
                  </div>
                ) : (
                  <div
                    className={`text-2xl font-bold ${
                      plan.highlighted
                        ? 'text-white dark:text-slate-900'
                        : 'text-slate-900 dark:text-white'
                    }`}
                  >
                    {plan.priceUnit}
                  </div>
                )}
              </div>

              {/* Features */}
              <ul className="space-y-3 mb-8">
                {plan.features.map((feature) => (
                  <li
                    key={feature}
                    className={`flex items-start gap-3 text-sm ${
                      plan.highlighted
                        ? 'text-slate-200 dark:text-slate-600'
                        : 'text-slate-600 dark:text-slate-400'
                    }`}
                  >
                    <Check
                      className={`w-5 h-5 flex-shrink-0 ${
                        plan.highlighted ? 'text-green-400' : 'text-green-500'
                      }`}
                    />
                    {feature}
                  </li>
                ))}
                {plan.notIncluded.map((feature) => (
                  <li
                    key={feature}
                    className={`flex items-start gap-3 text-sm ${
                      plan.highlighted
                        ? 'text-slate-500 dark:text-slate-400'
                        : 'text-slate-400 dark:text-slate-600'
                    }`}
                  >
                    <X className="w-5 h-5 flex-shrink-0" />
                    <span className="line-through">{feature}</span>
                  </li>
                ))}
              </ul>

              {/* CTA */}
              <Link
                to={plan.name === 'Enterprise' ? '/contact' : '/signup'}
                className={`block w-full py-3 px-6 rounded-xl text-center font-medium transition-all hover:scale-[1.02] ${
                  plan.highlighted
                    ? 'bg-white dark:bg-slate-900 text-slate-900 dark:text-white hover:bg-slate-100 dark:hover:bg-slate-800'
                    : 'bg-slate-900 dark:bg-white text-white dark:text-slate-900 hover:bg-slate-800 dark:hover:bg-slate-100'
                }`}
              >
                {plan.cta}
              </Link>
            </motion.div>
          ))}
        </div>

        {/* Free Trial Note */}
        <motion.p
          initial={{ opacity: 0 }}
          animate={isInView ? { opacity: 1 } : {}}
          transition={{ duration: 0.7, delay: 0.4 }}
          className="text-center text-sm text-slate-500 dark:text-slate-400 mt-8"
        >
          All plans include a 14-day free trial. No credit card required.
        </motion.p>
      </div>
    </section>
  );
}
