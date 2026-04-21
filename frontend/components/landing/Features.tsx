"use client";

import { useEffect, useRef } from "react";
import {
  Brain,
  Eye,
  FileText,
  Globe,
  Lock,
  ScanSearch,
  Shield,
  Users,
} from "lucide-react";

const features = [
  {
    icon: Brain,
    title: "Multi-label threat intelligence",
    description:
      "Classifies cyberbullying, threat, hate speech, and sexual harassment in one pass using transformer + rules hybrid scoring.",
  },
  {
    icon: Eye,
    title: "Explainability by default",
    description:
      "Highlights exact phrases and confidence slices so human reviewers understand why a case is escalated.",
  },
  {
    icon: Users,
    title: "Grooming progression tracking",
    description:
      "Detects subtle manipulation patterns over conversation turns, not just isolated toxic words.",
  },
  {
    icon: Globe,
    title: "Indian language ready",
    description:
      "Processes Hindi, Bengali, Hinglish and obfuscated slang with normalization before risk scoring.",
  },
  {
    icon: FileText,
    title: "FIR-ready legal mapping",
    description:
      "Maps findings to IPC, IT Act and POCSO references and prepares structured output for filing.",
  },
  {
    icon: ScanSearch,
    title: "OCR + screenshot analysis",
    description:
      "Extracts and evaluates text from memes, chats, and screenshots with visual evidence support.",
  },
  {
    icon: Shield,
    title: "Risk tier engine",
    description:
      "Produces LOW to CRITICAL escalation tags with weighted confidence for triage pipelines.",
  },
  {
    icon: Lock,
    title: "Evidence integrity flow",
    description:
      "Preserves linked artifacts and timestamps for traceable legal workflows and audits.",
  },
];

export default function Features() {
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("visible");
          }
        });
      },
      { threshold: 0.12 }
    );

    rootRef.current
      ?.querySelectorAll(".fade-in-up")
      .forEach((element) => observer.observe(element));

    return () => observer.disconnect();
  }, []);

  return (
    <section id="features" ref={rootRef} className="px-6 py-24 md:py-32">
      <div className="mx-auto max-w-7xl">
        <div className="fade-in-up mb-14 md:mb-20">
          <div className="inline-flex rounded-full border border-orange-200 dark:border-orange-900/50 bg-orange-50 dark:bg-orange-900/20 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-orange-700 dark:text-orange-400">
            Core Capabilities
          </div>
          <div className="mt-6 grid gap-6 md:grid-cols-[1.15fr,0.85fr] md:items-end">
            <h2 className="text-4xl font-black leading-[0.98] tracking-[-0.02em] text-slate-900 dark:text-white md:text-6xl">
              Built for teams that need fast
              <span className="gradient-text block">signal, evidence, and action.</span>
            </h2>
            <p className="max-w-lg text-base leading-relaxed text-slate-600 dark:text-slate-400">
              This platform is designed for cyber cells, NGOs, schools, and trust teams handling high-risk incidents where explainability and legal structure matter.
            </p>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <article
                key={feature.title}
                className="fade-in-up feature-card glass rounded-2xl p-5"
                style={{ transitionDelay: `${index * 45}ms` }}
              >
                <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-orange-100 dark:from-orange-900/30 to-amber-100 dark:to-amber-900/30 text-orange-700 dark:text-orange-400">
                  <Icon size={19} />
                </div>
                <h3 className="text-base font-bold leading-tight text-slate-900 dark:text-white">{feature.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-400">{feature.description}</p>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
