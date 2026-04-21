"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, BadgeCheck, Radar, Siren, Sparkles } from "lucide-react";

const TYPED_WORDS = [
  "Cyberbullying",
  "Hate Speech",
  "Child Grooming",
  "Coordinated Threats",
  "Sexual Harassment",
];

const stats = [
  { value: "98.7%", label: "Model Precision" },
  { value: "< 2 sec", label: "Average Scan Time" },
  { value: "12+", label: "Indian Laws Mapped" },
  { value: "24/7", label: "Case Monitoring" },
];

export default function Hero() {
  const [typedText, setTypedText] = useState("");
  const [wordIndex, setWordIndex] = useState(0);
  const [charIndex, setCharIndex] = useState(0);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    const currentWord = TYPED_WORDS[wordIndex];
    const speed = isDeleting ? 40 : 95;

    const timer = setTimeout(() => {
      if (!isDeleting) {
        const nextChar = charIndex + 1;
        setTypedText(currentWord.slice(0, nextChar));
        setCharIndex(nextChar);

        if (nextChar === currentWord.length) {
          setTimeout(() => setIsDeleting(true), 1200);
        }
      } else {
        const nextChar = Math.max(charIndex - 1, 0);
        setTypedText(currentWord.slice(0, nextChar));
        setCharIndex(nextChar);

        if (nextChar === 0) {
          setIsDeleting(false);
          setWordIndex((idx) => (idx + 1) % TYPED_WORDS.length);
        }
      }
    }, speed);

    return () => clearTimeout(timer);
  }, [charIndex, isDeleting, wordIndex]);

  return (
    <section className="relative overflow-hidden px-6 pb-16 pt-36 md:pb-24 md:pt-44">
      <div className="orb left-[-180px] top-[-120px] h-[340px] w-[340px] bg-orange-400/30" />
      <div className="orb right-[-120px] top-[10%] h-[260px] w-[260px] bg-sky-300/35" />
      <div className="orb bottom-[-140px] left-[38%] h-[280px] w-[280px] bg-amber-300/35" />

      <div className="mx-auto grid max-w-7xl items-end gap-10 lg:grid-cols-[1.08fr,0.92fr]">
        <div className="relative z-10">
          <div className="inline-flex items-center gap-2 rounded-full border border-orange-200 dark:border-orange-900/50 bg-white/90 dark:bg-slate-800/60 px-4 py-2 text-[11px] font-semibold uppercase tracking-[0.2em] text-orange-700 dark:text-orange-400 shadow-[0_10px_24px_rgba(249,115,22,0.17)]">
            <Radar size={14} />
            Active Safety Intelligence
          </div>

          <h1 className="mt-6 text-5xl font-extrabold leading-[0.95] tracking-[-0.03em] text-slate-900 dark:text-white sm:text-6xl lg:text-7xl">
            Detect harmful signals
            <span className="mt-2 block text-4xl sm:text-5xl lg:text-6xl">
              <span className="gradient-text">{typedText}</span>
              <span className="cursor" />
            </span>
            <span className="mt-3 block text-slate-700 dark:text-slate-300">before damage escalates.</span>
          </h1>

          <p className="mt-7 max-w-xl text-base leading-relaxed text-slate-600 dark:text-slate-400 md:text-lg">
            SafeGuard AI scans text, screenshots, and conversation threads to produce evidence-backed risk scores and legally mappable incident reports in one flow.
          </p>

          <div className="mt-8 flex flex-wrap items-center gap-3">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-orange-600 to-amber-500 px-6 py-3 text-sm font-bold text-white shadow-[0_16px_30px_rgba(249,115,22,0.3)] transition hover:translate-y-[-1px]"
            >
              Start Safety Scan
              <ArrowRight size={16} />
            </Link>
            <Link
              href="#demo"
              className="inline-flex items-center gap-2 rounded-2xl border border-slate-300 dark:border-slate-600 bg-white/75 dark:bg-slate-800/60 px-6 py-3 text-sm font-semibold text-slate-700 dark:text-slate-300 transition hover:border-slate-400 dark:hover:border-slate-500 hover:bg-white dark:hover:bg-slate-700"
            >
              <Sparkles size={15} className="text-teal-700 dark:text-teal-400" />
              Watch Interactive Demo
            </Link>
          </div>

          <div className="mt-8 flex flex-wrap gap-2">
            {["Explainable AI", "OCR + Visual Analysis", "POCSO/IPC Mapping", "Hinglish & Bengali Ready"].map((chip) => (
              <span
                key={chip}
                className="rounded-full border border-slate-300/90 bg-white/70 px-3 py-1.5 text-[11px] font-semibold uppercase tracking-[0.08em] text-slate-600 dark:border-slate-600 dark:bg-slate-800/60 dark:text-slate-300"
              >
                {chip}
              </span>
            ))}
          </div>
        </div>

        <div className="relative z-10">
          <div className="glass noise scanline rounded-[30px] p-6 md:p-7">
            <div className="mb-4 flex items-center justify-between">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">Live Command Feed</p>
              <div className="inline-flex items-center gap-2 rounded-full bg-emerald-100 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.15em] text-emerald-700">
                <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                Online
              </div>
            </div>

            <div className="space-y-3 rounded-2xl border border-slate-200/80 bg-white/90 p-4 text-sm dark:border-slate-700 dark:bg-slate-800/60">
              <div className="flex items-start gap-3 rounded-xl bg-rose-50 p-3 dark:bg-rose-900/20">
                <Siren size={18} className="mt-0.5 text-rose-600" />
                <div>
                  <p className="font-semibold text-slate-900 dark:text-white">Critical threat detected in conversation thread</p>
                  <p className="text-xs text-slate-600 dark:text-slate-300">Confidence: 96% • Triggered sections: IPC 503, IT Act 66D</p>
                </div>
              </div>
              <div className="flex items-start gap-3 rounded-xl bg-amber-50 p-3 dark:bg-amber-900/20">
                <BadgeCheck size={18} className="mt-0.5 text-amber-700" />
                <div>
                  <p className="font-semibold text-slate-900 dark:text-white">FIR draft generated with legal mapping</p>
                  <p className="text-xs text-slate-600 dark:text-slate-300">Evidence links + timestamps preserved for chain of custody.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-5 grid grid-cols-2 gap-3">
            {stats.map((stat) => (
              <article key={stat.label} className="glass rounded-2xl p-4">
                <p className="text-2xl font-extrabold tracking-tight text-slate-900 dark:text-white">{stat.value}</p>
                <p className="mt-1 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">{stat.label}</p>
              </article>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
