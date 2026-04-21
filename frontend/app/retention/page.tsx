"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function RetentionPage() {
  return (
    <main className="app-shell grid-bg">
      <div className="mx-auto max-w-4xl px-6 py-20">
        <Link
          href="/"
          className="inline-flex items-center gap-2 mb-8 text-slate-300 hover:text-orange-500 transition"
        >
          <ArrowLeft size={18} />
          Back to Home
        </Link>

        <article className="glass rounded-3xl p-8 md:p-12">
          <h1 className="text-4xl font-black text-white mb-4">Data Retention Policy</h1>
          <p className="text-sm text-slate-400 mb-8">Last updated: April 18, 2026</p>

          <div className="prose prose-slate max-w-none space-y-6 text-slate-200">
            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Overview</h2>
              <p>
                This policy outlines how SafeGuard AI collects, retains, uses, and deletes personal and case data in compliance with applicable laws and regulations.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">User Account Data</h2>
              <p>
                User account information (name, email, organization, role) is retained for as long as your account is active. Account data is deleted within 30 days of account deletion request.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Analysis Records</h2>
              <div className="space-y-3">
                <div>
                  <h3 className="font-bold text-white">Active Cases:</h3>
                  <p>Retained for the duration of the case and 3 years post-closure for audit purposes</p>
                </div>
                <div>
                  <h3 className="font-bold text-white">Archived Cases:</h3>
                  <p>Retained for 7 years as per legal requirements, then securely deleted</p>
                </div>
              </div>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">FIR Reports</h2>
              <p>
                Generated FIR reports are retained as evidence records for the period specified by applicable jurisdiction requirements, typically 5-10 years.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">System Logs and Metadata</h2>
              <ul className="list-disc pl-6 space-y-2">
                <li>Activity logs: Retained for 1 year</li>
                <li>System audit logs: Retained for 2 years</li>
                <li>Error logs: Retained for 90 days or until resolved</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Data Deletion</h2>
              <p>
                Upon request or policy expiration, data is securely deleted using industry-standard techniques. For sensitive data, we use multi-pass deletion protocols.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Legal Holds</h2>
              <p>
                Data subject to legal proceedings may be retained longer than standard retention periods in compliance with preservation orders and legal requirements.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Data Portability</h2>
              <p>
                You can request an export of your data in standard formats at any time. Submit requests to data-export@safeguard-ai.com.
              </p>
            </section>
          </div>
        </article>
      </div>
    </main>
  );
}
