"use client";

import Link from "next/link";
import { ArrowLeft, BarChart3, TrendingUp, Shield } from "lucide-react";

export default function CaseStudiesPage() {
  return (
    <main className="app-shell grid-bg">
      <div className="mx-auto max-w-4xl px-6 py-20">
        <Link
          href="/"
          className="mb-8 inline-flex items-center gap-2 text-slate-600 transition hover:text-orange-500 dark:text-slate-400"
        >
          <ArrowLeft size={18} />
          Back to Home
        </Link>

        <article className="glass rounded-3xl p-8 md:p-12">
          <h1 className="mb-4 text-4xl font-black text-slate-900 dark:text-white">Case Studies</h1>
          <p className="mb-8 text-sm text-slate-600 dark:text-slate-400">Real-world implementations and success stories</p>

          <div className="prose prose-slate max-w-none space-y-8 text-slate-700 dark:text-slate-300">
            <section>
              <h2 className="mb-4 text-2xl font-bold text-slate-900 dark:text-white">Delhi Cyber Cell</h2>
              <div className="flex gap-3 mb-4">
                <BarChart3 className="text-orange-600 flex-shrink-0" size={24} />
                <div>
                  <p className="font-semibold text-slate-900 dark:text-white">80% reduction in FIR preparation time</p>
                  <p className="text-sm text-slate-600 dark:text-slate-300">From 2-3 hours to 15 minutes per case</p>
                </div>
              </div>
              <p>
                The Delhi Cyber Cell integrated SafeGuard AI into their incident response workflow. By automating FIR generation and legal mapping, they reduced administrative overhead while improving consistency.
              </p>
            </section>

            <section>
              <h2 className="mb-4 text-2xl font-bold text-slate-900 dark:text-white">CyberShield India NGO</h2>
              <div className="flex gap-3 mb-4">
                <TrendingUp className="text-orange-600 flex-shrink-0" size={24} />
                <div>
                  <p className="font-semibold text-slate-900 dark:text-white">3x increase in case screening capacity</p>
                  <p className="text-sm text-slate-600 dark:text-slate-300">From 50 to 150 cases per week</p>
                </div>
              </div>
              <p>
                By leveraging SafeGuard AI&apos;s multilingual grooming detection, CyberShield India was able to screen significantly more cases without increasing team size. The explainable AI allowed them to train new analysts faster.
              </p>
            </section>

            <section>
              <h2 className="mb-4 text-2xl font-bold text-slate-900 dark:text-white">IIT Delhi Research</h2>
              <div className="flex gap-3 mb-4">
                <Shield className="text-orange-600 flex-shrink-0" size={24} />
                <div>
                  <p className="font-semibold text-slate-900 dark:text-white">92% accuracy in Hinglish detection</p>
                  <p className="text-sm text-slate-600 dark:text-slate-300">Pilot study with 2000+ annotated samples</p>
                </div>
              </div>
              <p>
                Research collaboration validated SafeGuard AI&apos;s effectiveness in detecting harmful content in code-mixed Indian languages. Published in peer-reviewed venues.
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-2xl font-bold text-slate-900 dark:text-white">Key Metrics</h2>
              <div className="grid md:grid-cols-3 gap-4 mt-4">
                <div className="glass rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-orange-600">500K+</p>
                  <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">Cases Analyzed</p>
                </div>
                <div className="glass rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-orange-600">15 Agencies</p>
                  <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">Active Users</p>
                </div>
                <div className="glass rounded-lg p-4 text-center">
                  <p className="text-3xl font-bold text-orange-600">24/7</p>
                  <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">System Uptime</p>
                </div>
              </div>
            </section>

            <section>
              <h2 className="mb-3 text-2xl font-bold text-slate-900 dark:text-white">Interested in a Case Study?</h2>
              <p>
                If you&apos;d like to share your success story or discuss a custom implementation, contact us at partnerships@safeguard-ai.com
              </p>
            </section>
          </div>
        </article>
      </div>
    </main>
  );
}
