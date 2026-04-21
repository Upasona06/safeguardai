"use client";

import Link from "next/link";
import { ArrowLeft } from "lucide-react";

export default function PrivacyPage() {
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
          <h1 className="text-4xl font-black text-white mb-4">Privacy Policy</h1>
          <p className="text-sm text-slate-400 mb-8">Last updated: April 18, 2026</p>

          <div className="prose prose-slate max-w-none space-y-6 text-slate-200">
            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Introduction</h2>
              <p>
                SafeGuard AI (&ldquo;Company,&rdquo; &ldquo;we,&rdquo; &ldquo;our,&rdquo; or &ldquo;us&rdquo;) is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and otherwise process your information through our website and services.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Information We Collect</h2>
              <p>
                We collect information you voluntarily provide, including your name, email, organization details, and profile preferences when you sign up for SafeGuard AI. We also collect technical information about your usage patterns and platform interactions.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">How We Use Your Information</h2>
              <ul className="list-disc pl-6 space-y-2">
                <li>To provide and maintain our services</li>
                <li>To process your analysis requests</li>
                <li>To improve and optimize platform performance</li>
                <li>To communicate with you about updates and support</li>
                <li>To comply with legal obligations</li>
              </ul>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Data Security</h2>
              <p>
                We implement industry-standard security measures to protect your data. All communications are encrypted, and sensitive information is stored securely with restricted access.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Your Rights</h2>
              <p>
                You have the right to access, correct, or delete your personal information. To exercise these rights, please contact us at privacy@safeguard-ai.com.
              </p>
            </section>

            <section>
              <h2 className="text-2xl font-bold text-white mb-3">Contact Us</h2>
              <p>
                If you have any questions about this Privacy Policy, please contact us at privacy@safeguard-ai.com or visit our support page.
              </p>
            </section>
          </div>
        </article>
      </div>
    </main>
  );
}
