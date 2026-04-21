"use client";

import Link from "next/link";
import { ArrowUpRight, Github, Linkedin, Shield, Sparkles, Star, Twitter } from "lucide-react";

const testimonials = [
  {
    name: "DCP Rakesh Sharma",
    role: "Deputy Commissioner, Delhi Cyber Cell",
    quote:
      "SafeGuard AI cut our FIR prep from hours to minutes. The legal mapping and explainability are reliable enough for daily field use.",
    initials: "RS",
  },
  {
    name: "Priya Mehta",
    role: "Child Safety Advocate, CyberShield India",
    quote:
      "The grooming detection flow helped us intervene in active cases quickly, while still giving human-readable reasoning to our team.",
    initials: "PM",
  },
  {
    name: "Dr. Ananya Roy",
    role: "Cybersecurity Researcher, IIT Delhi",
    quote:
      "Its multilingual handling is strong. Hinglish and Bengali normalization drastically improved our moderation quality in pilot studies.",
    initials: "AR",
  },
];

export function Testimonials() {
  return (
    <section className="px-6 py-24 md:py-32">
      <div className="mx-auto max-w-7xl">
        <div className="mb-12 md:mb-16">
          <div className="inline-flex rounded-full border border-amber-200 dark:border-amber-900/50 bg-amber-50 dark:bg-amber-900/20 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-amber-700 dark:text-amber-400">
            Trusted Teams
          </div>
          <h2 className="mt-6 text-4xl font-black leading-tight tracking-[-0.02em] text-slate-900 dark:text-white md:text-6xl">
            Built with people who protect
            <span className="gradient-text block">others every single day.</span>
          </h2>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {testimonials.map((item) => (
            <article key={item.name} className="glass rounded-2xl p-5 md:p-6">
              <div className="mb-4 flex items-center gap-1 text-amber-500">
                {Array.from({ length: 5 }).map((_, index) => (
                  <Star key={index} size={13} className="fill-current" />
                ))}
              </div>

              <p className="text-sm leading-relaxed text-slate-700 dark:text-slate-300">&ldquo;{item.quote}&rdquo;</p>

              <div className="mt-6 flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-br from-orange-500 to-amber-500 text-sm font-bold text-white">
                  {item.initials}
                </div>
                <div>
                  <p className="text-sm font-bold text-slate-900 dark:text-white">{item.name}</p>
                  <p className="text-xs text-slate-500 dark:text-slate-500">{item.role}</p>
                </div>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

export function CTASection() {
  return (
    <section className="px-6 pb-16 pt-8 md:pb-24 md:pt-10">
      <div className="mx-auto max-w-5xl">
        <div className="glass-red rounded-[30px] p-8 text-center md:p-12">
          <div className="mx-auto inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-600 to-amber-500 text-white shadow-[0_14px_30px_rgba(249,115,22,0.33)]">
            <Shield size={24} />
          </div>

          <h2 className="mx-auto mt-6 max-w-3xl text-4xl font-black leading-tight tracking-[-0.02em] text-slate-900 dark:text-white md:text-5xl">
            Ready to modernize how your team handles
            <span className="gradient-text block">online harm cases?</span>
          </h2>

          <p className="mx-auto mt-4 max-w-2xl text-base leading-relaxed text-slate-700 dark:text-slate-300">
            Deploy a full analysis-to-FIR workflow with explainable AI, legal mapping, and evidence traceability.
          </p>

          <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-orange-600 to-amber-500 px-6 py-3 text-sm font-bold text-white shadow-[0_16px_30px_rgba(249,115,22,0.32)] transition hover:translate-y-[-1px]"
            >
              Start Free Analysis
              <ArrowUpRight size={16} />
            </Link>
            <Link
              href="#demo"
              className="inline-flex items-center gap-2 rounded-2xl border border-slate-300 dark:border-slate-600 bg-white/85 dark:bg-slate-800/60 px-6 py-3 text-sm font-semibold text-slate-700 dark:text-slate-300 transition hover:border-slate-400 dark:hover:border-slate-500 dark:hover:bg-slate-700"
            >
              <Sparkles size={15} className="text-teal-700 dark:text-teal-400" />
              View Live Demo
            </Link>
          </div>

          <p className="mt-5 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-500">
            Free for NGOs • Onboarding support • Built in India
          </p>
        </div>
      </div>
    </section>
  );
}

export function Footer() {
  return (
    <footer className="border-t border-slate-300/70 px-6 py-12 md:py-16">
      <div className="mx-auto grid max-w-7xl gap-8 md:grid-cols-[1.2fr,1fr,1fr,1fr]">
        <div>
          <div className="mb-3 flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-gradient-to-br from-orange-600 to-amber-500 text-white">
              <Shield size={15} />
            </div>
            <p className="text-base font-bold text-slate-900 dark:text-white">
              Safe<span className="gradient-text">Guard</span> AI
            </p>
          </div>
          <p className="max-w-sm text-sm leading-relaxed text-slate-600 dark:text-slate-400">
            AI-assisted cyber safety platform for screening harmful content and preparing legally structured incident records.
          </p>
        </div>

        {[
          {
            title: "Platform",
            links: [
              { label: "Dashboard", href: "/dashboard" },
              { label: "Analysis", href: "/dashboard" },
              { label: "FIR Generator", href: "/dashboard" },
              { label: "Analytics", href: "/analytics" },
            ],
          },
          {
            title: "Policies",
            links: [
              { label: "Privacy", href: "/privacy" },
              { label: "Terms", href: "/terms" },
              { label: "Data Security", href: "/data-security" },
              { label: "Retention", href: "/retention" },
            ],
          },
          {
            title: "Resources",
            links: [
              { label: "API", href: "/api" },
              { label: "Documentation", href: "/documentation" },
              { label: "Case Studies", href: "/case-studies" },
              { label: "Support", href: "/support" },
            ],
          },
        ].map((column) => (
          <div key={column.title}>
            <p className="mb-3 text-xs font-bold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-500">{column.title}</p>
            <ul className="space-y-2">
              {column.links.map((item) => (
                <li key={item.label}>
                  <Link href={item.href} className="text-sm text-slate-700 dark:text-slate-400 transition hover:text-slate-900 dark:hover:text-white">
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div className="mx-auto mt-10 flex max-w-7xl flex-col items-center justify-between gap-4 border-t border-slate-300/70 dark:border-slate-700/70 pt-6 text-xs text-slate-600 dark:text-slate-400 md:flex-row">
        <p className="font-semibold uppercase tracking-[0.1em]">© 2026 SafeGuard AI • Built in India</p>
        <div className="flex items-center gap-3">
          {[
            { Icon: Github, href: "https://github.com/safeguard-ai" },
            { Icon: Twitter, href: "https://twitter.com/safeguard_ai" },
            { Icon: Linkedin, href: "https://linkedin.com/company/safeguard-ai" },
          ].map(({ Icon, href }, idx) => (
            <Link
              key={idx}
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex h-8 w-8 items-center justify-center rounded-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-400 transition hover:border-slate-400 dark:hover:border-slate-500 hover:text-slate-900 dark:hover:text-white"
            >
              <Icon size={14} />
            </Link>
          ))}
        </div>
      </div>
    </footer>
  );
}

export default Testimonials;
