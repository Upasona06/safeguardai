"use client";

import Link from "next/link";
import { ArrowLeft, Shield, Lock, Eye, Zap } from "lucide-react";

export default function DataSecurityPage() {
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
          <h1 className="mb-4 text-4xl font-black text-slate-900 dark:text-white">Data Security</h1>
          <p className="mb-8 text-sm text-slate-600 dark:text-slate-400">Last updated: April 18, 2026</p>

          <div className="prose prose-slate max-w-none space-y-6 text-slate-700 dark:text-slate-300">
            <section>
              <h2 className="mb-3 text-2xl font-bold text-slate-900 dark:text-white">Security Framework</h2>
              <p>
                SafeGuard AI implements a comprehensive security framework designed to protect your data from unauthorized access, disclosure, alteration, and destruction.
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-2xl font-bold text-slate-900 dark:text-white">Encryption Standards</h2>
              <div className="space-y-4">
                <div className="flex gap-3">
                  <Lock className="text-orange-600 flex-shrink-0" size={24} />
                  <div>
                    <h3 className="font-bold text-slate-900 dark:text-white">End-to-End Encryption</h3>
                    <p className="text-slate-600 dark:text-slate-300">All data in transit is encrypted using TLS 1.3 protocol</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <Shield className="text-orange-600 flex-shrink-0" size={24} />
                  <div>
                    <h3 className="font-bold text-slate-900 dark:text-white">At-Rest Encryption</h3>
                    <p className="text-slate-600 dark:text-slate-300">Sensitive data stored in databases is encrypted using AES-256</p>
                  </div>
                </div>
                <div className="flex gap-3">
                  <Eye className="text-orange-600 flex-shrink-0" size={24} />
                  <div>
                    <h3 className="font-bold text-slate-900 dark:text-white">Access Controls</h3>
                    <p className="text-slate-600 dark:text-slate-300">Strict role-based access control (RBAC) with audit logging</p>
                  </div>
                </div>
              </div>
            </section>

            <section>
              <h2 className="mb-3 text-2xl font-bold text-slate-900 dark:text-white">Compliance</h2>
              <ul className="list-disc pl-6 space-y-2">
                <li>GDPR Compliance for EU data subjects</li>
                <li>CCPA Compliance for California residents</li>
                <li>ISO 27001 Information Security Management</li>
                <li>Regular security audits and penetration testing</li>
              </ul>
            </section>

            <section>
              <h2 className="mb-3 text-2xl font-bold text-slate-900 dark:text-white">Incident Response</h2>
              <p>
                We maintain a comprehensive incident response plan and will notify affected users within 24 hours of any confirmed data breach.
              </p>
            </section>

            <section>
              <h2 className="mb-3 text-2xl font-bold text-slate-900 dark:text-white">Regular Security Updates</h2>
              <div className="flex gap-3">
                <Zap className="text-orange-600 flex-shrink-0" size={24} />
                <div>
                  <p>
                    Our security team continuously monitors for vulnerabilities and applies patches. We conduct security assessments at least quarterly.
                  </p>
                </div>
              </div>
            </section>

            <section>
              <h2 className="mb-3 text-2xl font-bold text-slate-900 dark:text-white">Report Security Issues</h2>
              <p>
                If you discover a security vulnerability, please report it to security@safeguard-ai.com. We appreciate responsible disclosure.
              </p>
            </section>
          </div>
        </article>
      </div>
    </main>
  );
}
