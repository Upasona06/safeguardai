"use client";

import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { AlertTriangle, BarChart3, Clock3, FileText, Shield, TrendingUp, Loader2, ArrowLeft } from "lucide-react";
import { fetchAnalytics } from "@/services/api";
import { AnalyticsData } from "@/types";

export default function AnalyticsPage() {
  const { data: session, status } = useSession();
  const router = useRouter();
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (status === "unauthenticated") {
      router.push("/auth/signin?callbackUrl=/analytics");
    }
  }, [status, router]);

  useEffect(() => {
    if (session?.user) {
      fetchAnalytics()
        .then(setData)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [session]);

  if (status === "loading" || !session?.user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-orange-50 via-white to-sky-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-900">
        <Loader2 className="w-8 h-8 animate-spin text-orange-600" />
      </div>
    );
  }

  const statCards = data
    ? [
        { label: "Total Reports", value: data.total_reports.toLocaleString(), icon: Shield },
        { label: "Critical Cases", value: data.critical_cases.toLocaleString(), icon: AlertTriangle },
        { label: "FIRs Generated", value: data.fir_generated.toLocaleString(), icon: FileText },
        { label: "Average Response", value: `${data.avg_response_time}s`, icon: Clock3 },
      ]
    : [];

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
                <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500 dark:text-slate-400">Observability</p>
                <h1 className="mt-2 text-3xl font-black tracking-tight text-slate-900 dark:text-white md:text-4xl">
                  Platform Analytics
                  <span className="gradient-text block">for {session.user.name || "your"} operations</span>
                </h1>
                <p className="mt-3 max-w-3xl text-sm leading-relaxed text-slate-600 dark:text-slate-400 md:text-base">
                  Monitor detection trends, response performance, and legal-report generation to optimize intervention workflows.
                </p>
              </div>
            </div>
          </div>
        </header>

        {loading ? (
          <div className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
            {[1, 2, 3, 4].map((index) => (
              <div key={index} className="skeleton h-36 rounded-2xl" />
            ))}
          </div>
        ) : (
          <>
            <section className="mt-6 grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              {statCards.map((card) => {
                const Icon = card.icon;
                return (
                  <article key={card.label} className="glass rounded-2xl p-5">
                    <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-orange-100 to-amber-100 dark:from-orange-900/40 dark:to-amber-900/40 text-orange-700 dark:text-orange-400">
                      <Icon size={19} />
                    </div>
                    <p className="text-3xl font-black tracking-tight text-slate-900 dark:text-white">{card.value}</p>
                    <p className="mt-1 text-xs font-semibold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">{card.label}</p>
                  </article>
                );
              })}
            </section>

            <section className="mt-6 grid gap-6 xl:grid-cols-2">
              {data?.category_breakdown && (
                <article className="glass rounded-2xl p-5 md:p-6">
                  <h3 className="mb-5 flex items-center gap-2 text-sm font-bold uppercase tracking-[0.12em] text-slate-600 dark:text-slate-400">
                    <BarChart3 size={16} className="text-orange-700 dark:text-orange-400" />
                    Category Breakdown
                  </h3>
                  <div className="space-y-3">
                    {Object.entries(data.category_breakdown).map(([category, count]) => {
                      const maxCount = Math.max(...Object.values(data.category_breakdown), 1);
                      const width = (count / maxCount) * 100;

                      return (
                        <div key={category} className="grid grid-cols-[130px,1fr,42px] items-center gap-3">
                          <p className="truncate text-xs font-semibold text-slate-600 dark:text-slate-400">{category.replace("_", " ")}</p>
                          <div className="h-2 overflow-hidden rounded-full bg-slate-200/80 dark:bg-slate-700/60">
                            <div
                              className="h-full rounded-full bg-gradient-to-r from-orange-600 to-amber-500"
                              style={{ width: `${width}%` }}
                            />
                          </div>
                          <p className="text-right text-xs font-bold text-slate-600 dark:text-slate-400">{count}</p>
                        </div>
                      );
                    })}
                  </div>
                </article>
              )}

              {data?.daily_counts && data.daily_counts.length > 0 && (
                <article className="glass rounded-2xl p-5 md:p-6">
                  <h3 className="mb-5 flex items-center gap-2 text-sm font-bold uppercase tracking-[0.12em] text-slate-600 dark:text-slate-400">
                    <TrendingUp size={16} className="text-teal-700 dark:text-teal-400" />
                    Last 7 Days Activity
                  </h3>
                  <div className="flex h-44 items-end gap-2">
                    {data.daily_counts.map((entry) => {
                      const maxValue = Math.max(...data.daily_counts.map((item) => item.count), 1);
                      const height = (entry.count / maxValue) * 100;
                      return (
                        <div key={entry.date} className="flex flex-1 flex-col items-center gap-1">
                          <span className="text-[10px] font-semibold text-slate-500 dark:text-slate-400">{entry.count}</span>
                          <div
                            className="w-full min-h-[8px] rounded-t-md bg-gradient-to-t from-teal-700 to-sky-500"
                            style={{ height: `${Math.max(height, 4)}%` }}
                          />
                          <span className="text-[10px] font-semibold uppercase tracking-[0.08em] text-slate-500 dark:text-slate-400">
                            {new Date(entry.date).toLocaleDateString("en", { weekday: "short" })}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                </article>
              )}
            </section>
          </>
        )}
      </div>
    </main>
  );
}
