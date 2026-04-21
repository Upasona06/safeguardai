"use client";

import { useEffect, useRef } from "react";
import { AlertTriangle, FileText, Radar, Scale, UploadCloud } from "lucide-react";

const steps = [
  {
    icon: UploadCloud,
    title: "Ingest raw evidence",
    summary:
      "Upload image proofs, paste chat content, or submit full conversation threads from incident reports.",
    tag: "INPUT",
  },
  {
    icon: Radar,
    title: "Run multi-layer AI analysis",
    summary:
      "OCR extraction, toxicity classification, grooming heuristics, and context escalation are computed together.",
    tag: "ANALYSIS",
  },
  {
    icon: AlertTriangle,
    title: "Prioritize by risk",
    summary:
      "Each case gets LOW/MEDIUM/HIGH/CRITICAL status with confidence, token highlights, and reviewer context.",
    tag: "TRIAGE",
  },
  {
    icon: Scale,
    title: "Map to legal sections",
    summary:
      "Detected categories are matched to IPC, IT Act, and POCSO references to speed legal drafting.",
    tag: "LEGAL",
  },
  {
    icon: FileText,
    title: "Generate FIR package",
    summary:
      "Finalize complainant details and export court-ready PDF with evidence links and chain-of-custody metadata.",
    tag: "OUTPUT",
  },
];

export default function HowItWorks() {
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
      { threshold: 0.15 }
    );

    rootRef.current
      ?.querySelectorAll(".fade-in-up")
      .forEach((element) => observer.observe(element));

    return () => observer.disconnect();
  }, []);

  return (
    <section id="how-it-works" ref={rootRef} className="px-6 py-24 md:py-32">
      <div className="mx-auto max-w-6xl">
        <div className="fade-in-up text-center">
          <div className="inline-flex rounded-full border border-teal-200 dark:border-teal-900/50 bg-teal-50 dark:bg-teal-900/20 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-teal-700 dark:text-teal-400">
            Workflow
          </div>
          <h2 className="mx-auto mt-6 max-w-4xl text-4xl font-black leading-tight tracking-[-0.02em] text-slate-900 dark:text-white md:text-6xl">
            From user complaint to FIR draft
            <span className="gradient-text block">in five focused steps.</span>
          </h2>
        </div>

        <div className="mt-14 space-y-4 md:mt-16">
          {steps.map((step, index) => {
            const Icon = step.icon;
            return (
              <article
                key={step.title}
                className="fade-in-up glass rounded-2xl p-4 md:p-6"
                style={{ transitionDelay: `${index * 70}ms` }}
              >
                <div className="grid gap-4 md:grid-cols-[auto,1fr,auto] md:items-center">
                  <div className="flex items-center gap-3">
                    <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-orange-100 dark:from-orange-900/30 to-amber-100 dark:to-amber-900/30 text-orange-700 dark:text-orange-400">
                      <Icon size={20} />
                    </div>
                    <div>
                      <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-500">
                        Step {String(index + 1).padStart(2, "0")}
                      </p>
                      <p className="text-lg font-bold text-slate-900 dark:text-white">{step.title}</p>
                    </div>
                  </div>

                  <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-400 md:max-w-2xl">{step.summary}</p>

                  <div className="justify-self-start rounded-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-600 dark:text-slate-400 md:justify-self-end">
                    {step.tag}
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
