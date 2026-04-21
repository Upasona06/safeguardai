"use client";

import Link from "next/link";
import { ArrowLeft, BookOpen, FileText, Users, Zap } from "lucide-react";

export default function DocumentationPage() {
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
          <h1 className="mb-4 text-4xl font-black text-slate-900 dark:text-white">Documentation</h1>
          <p className="mb-8 text-sm text-slate-600 dark:text-slate-400">Complete guides and references for SafeGuard AI</p>

          <div className="prose prose-slate max-w-none space-y-8 text-slate-700 dark:text-slate-300">
            <section>
              <h2 className="mb-4 text-2xl font-bold text-slate-900 dark:text-white">Getting Started</h2>
              <div className="space-y-3">
                <div className="flex gap-3 rounded-lg border border-orange-200 bg-orange-50 p-4 dark:border-orange-900/40 dark:bg-orange-900/20">
                  <BookOpen className="text-orange-600 flex-shrink-0" size={20} />
                  <div>
                    <h3 className="font-bold text-slate-900 dark:text-white">Installation Guide</h3>
                    <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Step-by-step guide to set up SafeGuard AI on your system</p>
                  </div>
                </div>
                <div className="flex gap-3 rounded-lg border border-orange-200 bg-orange-50 p-4 dark:border-orange-900/40 dark:bg-orange-900/20">
                  <Zap className="text-orange-600 flex-shrink-0" size={20} />
                  <div>
                    <h3 className="font-bold text-slate-900 dark:text-white">Quick Start</h3>
                    <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Get up and running in 5 minutes with our quick start guide</p>
                  </div>
                </div>
              </div>
            </section>

            <section>
              <h2 className="mb-4 text-2xl font-bold text-slate-900 dark:text-white">User Guides</h2>
              <div className="space-y-3">
                <div className="flex gap-3 rounded-lg bg-slate-50 p-4 dark:bg-slate-800/50">
                  <FileText className="text-teal-600 flex-shrink-0" size={20} />
                  <div>
                    <h3 className="font-bold text-slate-900 dark:text-white">Text Analysis Guide</h3>
                    <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Analyze text content for harmful signals</p>
                  </div>
                </div>
                <div className="flex gap-3 rounded-lg bg-slate-50 p-4 dark:bg-slate-800/50">
                  <FileText className="text-teal-600 flex-shrink-0" size={20} />
                  <div>
                    <h3 className="font-bold text-slate-900 dark:text-white">Image Analysis Guide</h3>
                    <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Process images and extract text with OCR</p>
                  </div>
                </div>
                <div className="flex gap-3 rounded-lg bg-slate-50 p-4 dark:bg-slate-800/50">
                  <FileText className="text-teal-600 flex-shrink-0" size={20} />
                  <div>
                    <h3 className="font-bold text-slate-900 dark:text-white">FIR Generation Guide</h3>
                    <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Generate legally valid FIR reports with evidence</p>
                  </div>
                </div>
              </div>
            </section>

            <section>
              <h2 className="mb-4 text-2xl font-bold text-slate-900 dark:text-white">Advanced Topics</h2>
              <div className="space-y-3">
                <div className="flex gap-3 rounded-lg bg-slate-50 p-4 dark:bg-slate-800/50">
                  <Users className="text-slate-600 flex-shrink-0" size={20} />
                  <div>
                    <h3 className="font-bold text-slate-900 dark:text-white">Team Management</h3>
                    <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Configure teams, roles, and permissions</p>
                  </div>
                </div>
                <div className="flex gap-3 rounded-lg bg-slate-50 p-4 dark:bg-slate-800/50">
                  <Users className="text-slate-600 flex-shrink-0" size={20} />
                  <div>
                    <h3 className="font-bold text-slate-900 dark:text-white">Analytics Dashboard</h3>
                    <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Track trends, metrics, and case statistics</p>
                  </div>
                </div>
              </div>
            </section>

            <section>
              <h2 className="mb-3 text-2xl font-bold text-slate-900 dark:text-white">Need Help?</h2>
              <p>
                Check our <Link href="/support" className="text-orange-600 font-semibold hover:underline">support page</Link> or 
                contact us at <a href="mailto:support@safeguard-ai.com" className="text-orange-600 font-semibold hover:underline">support@safeguard-ai.com</a>
              </p>
            </section>
          </div>
        </article>
      </div>
    </main>
  );
}
