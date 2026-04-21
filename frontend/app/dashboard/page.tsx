"use client";

import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  ScanText,
  Image,
  MessageSquareText,
  Loader2,
  ArrowLeft,
  type LucideIcon,
} from "lucide-react";
import TextAnalyzer from "@/components/dashboard/TextAnalyzer";
import ImageAnalyzer from "@/components/dashboard/ImageAnalyzer";
import ContextAnalyzer from "@/components/dashboard/ContextAnalyzer";
import ResultsPanel from "@/components/dashboard/ResultsPanel";
import FIRHistory from "@/components/dashboard/FIRHistory";
import ProfileInfo from "@/components/ProfileInfo";
import { AnalysisResult } from "@/types";
import { wakeBackend } from "@/services/api";

type Tab = "text" | "image" | "context";

const tabs: Array<{ id: Tab; label: string; icon: LucideIcon }> = [
  { id: "text", label: "Text Analysis", icon: ScanText },
  { id: "image", label: "Image + OCR", icon: Image },
  { id: "context", label: "Conversation Context", icon: MessageSquareText },
];

export default function DashboardPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<Tab>("text");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/auth/signin?callbackUrl=/dashboard");
    }
  }, [status, router]);

  useEffect(() => {
    if (status === "authenticated") {
      wakeBackend().catch(() => {
      });
    }
  }, [status]);

  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orange-50 via-white to-sky-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-900">
        <Loader2 className="w-8 h-8 animate-spin text-orange-600" />
      </div>
    );
  }

  if (!session?.user) {
    return null;
  }

  return (
    <main className="app-shell grid-bg">
      <div className="mx-auto max-w-7xl px-6 pb-16 pt-28 md:pt-32">
        <header className="glass rounded-3xl p-6 md:p-8">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
            <div className="flex items-start gap-4">
              <button
                onClick={() => router.push("/")}
                className="rounded-lg p-2 hover:bg-orange-50 dark:hover:bg-slate-800 transition mt-1"
                title="Back to homepage"
              >
                <ArrowLeft size={20} className="text-orange-600" />
              </button>
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">
                  Operations Console
                </p>
                <h1 className="mt-2 text-3xl font-black tracking-tight text-slate-900 dark:text-white md:text-4xl">
                  AI Incident Analysis
                  <span className="gradient-text block">for high-priority cases</span>
                </h1>
                <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-600 dark:text-slate-400 md:text-base">
                  Analyze text, screenshots, and conversation evidence to generate
                  explainable risk assessments and legal section mappings.
                </p>
              </div>
            </div>

            {session.user && (
              <ProfileInfo compact={true} />
            )}
          </div>
        </header>

        <div className="mt-6 grid gap-6 lg:grid-cols-12">
          <section className="space-y-4 lg:col-span-5">
            <div className="glass rounded-2xl p-2">
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-3 lg:grid-cols-1 xl:grid-cols-3">
                {tabs.map((tab) => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      type="button"
                      onClick={() => {
                        setActiveTab(tab.id);
                        setResult(null);
                        setLoading(false);
                      }}
                      className={`flex items-center justify-center gap-2 rounded-xl px-3 py-3 text-xs font-bold uppercase tracking-[0.1em] transition ${
                        activeTab === tab.id
                          ? "bg-gradient-to-r from-orange-600 to-amber-500 text-white shadow-[0_14px_25px_rgba(249,115,22,0.28)]"
                          : "bg-white/70 text-slate-600 hover:bg-white hover:text-slate-900 dark:bg-slate-800/70 dark:text-slate-300 dark:hover:bg-slate-700 dark:hover:text-slate-100"
                      }`}
                    >
                      <Icon size={15} />
                      {tab.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="glass rounded-2xl border border-slate-300/70">
              {activeTab === "text" && (
                <TextAnalyzer onResult={setResult} onLoading={setLoading} />
              )}
              {activeTab === "image" && (
                <ImageAnalyzer onResult={setResult} onLoading={setLoading} />
              )}
              {activeTab === "context" && (
                <ContextAnalyzer onResult={setResult} onLoading={setLoading} />
              )}
            </div>
          </section>

          <section className="lg:col-span-7">
            <ResultsPanel result={result} loading={loading} />
          </section>
        </div>

        <section className="mt-8 glass rounded-2xl p-6 md:p-8">
          <FIRHistory />
        </section>
      </div>
    </main>
  );
}
