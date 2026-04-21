"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function TermsPage() {
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
          <h1 className="text-4xl font-black text-white mb-4">Terms of Service</h1>
          <p className="text-sm text-slate-400 mb-8">Last updated: April 18, 2026</p>

          <div className="prose prose-slate max-w-none space-y-6 text-slate-200">
            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Acceptance of Terms</h2>
              <p>
                By accessing and using SafeGuard AI, you accept and agree to be bound by the terms and provision of this agreement. If you do not agree to abide by the above, please do not use this service.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Use License</h2>
              <p>
                Permission is granted to temporarily download one copy of the materials (information or software) on SafeGuard AI for personal, non-commercial transitory viewing only. This is the grant of a license, not a transfer of title, and under this license you may not:
              </p>
              <ul className="list-disc pl-6 space-y-2 mt-2">
                <li>Modify or copy the materials</li>
                <li>Use the materials for any commercial purpose or for any public display</li>
                <li>Attempt to decompile or reverse engineer any software contained on the platform</li>
                <li>Remove any copyright or other proprietary notations from the materials</li>
                <li>Transfer the materials to another person or &ldquo;mirror&rdquo; the materials on any other server</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Disclaimer</h2>
              <p>
                The materials on SafeGuard AI are provided for informational purposes and should not be considered legal advice. While we strive for accuracy, we do not warrant that all information is accurate, complete, or current.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Limitations</h2>
              <p>
                In no event shall SafeGuard AI or its suppliers be liable for any damages (including, without limitation, damages for loss of data or profit, or due to business interruption) arising out of the use or inability to use the materials on SafeGuard AI.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Accuracy of Materials</h2>
              <p>
                The materials appearing on SafeGuard AI could include technical, typographical, or photographic errors. SafeGuard AI does not warrant that any of the materials on its website are accurate, complete, or current.
              </p>
            </section>
          </div>
        </article>
      </div>
    </main>
  );
}
