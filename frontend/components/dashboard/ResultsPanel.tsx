"use client";

import { useState } from "react";
import {
  Download,
  FileText,
  Info,
  Loader2,
  Scale,
  Zap,
} from "lucide-react";
import { useSession } from "next-auth/react";
import { AnalysisResult } from "@/types";
import { generateFIR, downloadFIR } from "@/services/api";
import toast from "react-hot-toast";
import FIRModal from "./FIRModal";

interface Props {
  result: AnalysisResult | null;
  loading: boolean;
}

const riskConfig: Record<string, { className: string; icon: string }> = {
  LOW: { className: "badge-low", icon: "✓" },
  MEDIUM: { className: "badge-medium", icon: "!" },
  HIGH: { className: "badge-high", icon: "!!" },
  CRITICAL: { className: "badge-critical", icon: "⚠" },
};

const categoryLabels: Record<string, string> = {
  cyberbullying: "Cyberbullying",
  threat: "Threat / Intimidation",
  hate_speech: "Hate Speech",
  sexual_harassment: "Sexual Harassment",
  grooming: "Grooming",
};

export default function ResultsPanel({ result, loading }: Props) {
  const { data: session } = useSession();
  const [showFIRModal, setShowFIRModal] = useState(false);
  const [generatingFIR, setGeneratingFIR] = useState(false);
  const [firId, setFirId] = useState<string | null>(null);

  const handleGenerateFIR = async () => {
    if (!result) return;
    setGeneratingFIR(true);

    try {
      const { fir_id } = await generateFIR(result.id, session?.user);
      setFirId(fir_id);
      setShowFIRModal(true);
      toast.success("FIR generated successfully");
    } catch (error) {
      const message = error instanceof Error ? error.message : "FIR generation failed";
      toast.error(message);
    } finally {
      setGeneratingFIR(false);
    }
  };

  if (loading) {
    return (
      <div className="glass rounded-2xl p-6">
        <div className="mb-5 flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-300">
          <Loader2 size={17} className="animate-spin text-orange-600" />
          AI is processing your submission...
        </div>
        <div className="space-y-3">
          {[100, 84, 90, 72, 65].map((width, index) => (
            <div key={index} className="skeleton h-10 rounded-xl" style={{ width: `${width}%` }} />
          ))}
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="glass rounded-2xl flex min-h-[520px] flex-col items-center justify-center p-8 text-center">
        <div className="mb-4 rounded-full bg-orange-100 dark:bg-orange-900/40 p-3 text-orange-700 dark:text-orange-400">
          <Zap size={20} />
        </div>
        <h3 className="text-lg font-bold text-slate-900 dark:text-white">Analysis output appears here</h3>
        <p className="mt-2 max-w-sm text-sm leading-relaxed text-slate-600 dark:text-slate-400">
          Submit text, image, or conversation context from the left panel to inspect risk scores, highlights, and legal mapping.
        </p>
      </div>
    );
  }

  const risk = riskConfig[result.risk_level];

  const topLabels = Object.entries(result.labels)
    .sort(([, a], [, b]) => b - a)
    .filter(([, value], index) => value > 0.18 || index < 3);

  return (
    <>
      <div className="glass rounded-2xl p-5 md:p-6">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-3">
            <span className={`rounded-full px-4 py-2 text-xs font-black tracking-[0.14em] ${risk.className}`}>
              {risk.icon} {result.risk_level}
            </span>
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">
              {(result.overall_score * 100).toFixed(1)}% confidence
            </span>
          </div>
          <div className="rounded-full border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.1em] text-slate-600 dark:text-slate-400">
            {result.language_detected} • {new Date(result.timestamp).toLocaleTimeString()}
          </div>
        </div>

        <section className="mb-6">
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">Category Scores</p>
          <div className="space-y-2.5">
            {topLabels.map(([key, value]) => (
              <div key={key} className="grid grid-cols-[140px,1fr,48px] items-center gap-3">
                <p className="truncate text-xs font-semibold text-slate-600 dark:text-slate-400">{categoryLabels[key] || key}</p>
                <div className="h-2 overflow-hidden rounded-full bg-slate-200/80 dark:bg-slate-700/60">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-orange-500 to-amber-500"
                    style={{ width: `${value * 100}%` }}
                  />
                </div>
                <p className="text-right text-xs font-bold text-slate-600 dark:text-slate-400">{(value * 100).toFixed(0)}%</p>
              </div>
            ))}
          </div>
        </section>

        <section className="mb-6">
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">Highlighted Evidence</p>
          <div
            className="rounded-xl border border-slate-300 dark:border-slate-600 bg-white/90 dark:bg-slate-800/50 p-4 text-sm leading-relaxed text-slate-700 dark:text-slate-300"
            dangerouslySetInnerHTML={{ __html: result.highlighted_text || result.original_text }}
          />
          {result.toxic_tokens.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {result.toxic_tokens.slice(0, 10).map((token) => (
                <span
                  key={`${token.token}-${token.category}`}
                  className="rounded-full border border-orange-200 dark:border-orange-900/40 bg-orange-50 dark:bg-orange-900/20 px-2.5 py-1 text-[11px] font-semibold text-orange-700 dark:text-orange-400"
                >
                  {token.token} ({(token.score * 100).toFixed(0)}%)
                </span>
              ))}
            </div>
          )}
        </section>

        {result.explanation && (
          <section className="mb-6 rounded-xl border border-orange-200 dark:border-orange-900/40 bg-orange-50 dark:bg-orange-900/20 p-4">
            <div className="mb-2 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-orange-700 dark:text-orange-400">
              <Info size={13} />
              AI Reasoning Summary
            </div>
            <p className="text-sm leading-relaxed text-slate-700 dark:text-slate-300">{result.explanation}</p>
          </section>
        )}

        {result.legal_mappings.length > 0 && (
          <section className="mb-6">
            <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400">
              <Scale size={14} className="text-slate-700 dark:text-slate-400" />
              Applicable Legal Mapping
            </div>
            <div className="space-y-2">
              {result.legal_mappings.map((mapping) => (
                <article
                  key={`${mapping.law}-${mapping.section}`}
                  className="rounded-xl border border-amber-200 dark:border-amber-900/40 bg-amber-50 dark:bg-amber-900/20 p-3"
                >
                  <p className="text-xs font-bold uppercase tracking-[0.09em] text-amber-800 dark:text-amber-400">
                    {mapping.law} • {mapping.section}
                  </p>
                  <p className="mt-1 text-sm text-slate-700 dark:text-slate-300">{mapping.description}</p>
                </article>
              ))}
            </div>
          </section>
        )}

        {(result.risk_level === "MEDIUM" || result.risk_level === "HIGH" || result.risk_level === "CRITICAL") && (
          <section className="flex flex-wrap gap-3 border-t border-slate-300 dark:border-slate-700 pt-5">
            <button
              type="button"
              onClick={handleGenerateFIR}
              disabled={generatingFIR}
              className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-orange-600 to-amber-500 px-4 py-3 text-sm font-bold text-white shadow-[0_14px_26px_rgba(249,115,22,0.25)] transition hover:translate-y-[-1px] disabled:opacity-70"
            >
              {generatingFIR ? (
                <>
                  <Loader2 size={15} className="animate-spin" />
                  Preparing FIR...
                </>
              ) : (
                <>
                  <FileText size={15} />
                  Generate FIR Draft
                </>
              )}
            </button>

            {firId && (
              <button
                type="button"
                onClick={() => downloadFIR(firId, session?.user)}
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-400 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300 dark:hover:border-slate-500"
              >
                <Download size={15} />
                Download
              </button>
            )}
          </section>
        )}
      </div>

      {showFIRModal && firId && (
        <FIRModal
          firId={firId}
          result={result}
          user={session?.user}
          onClose={() => setShowFIRModal(false)}
        />
      )}
    </>
  );
}
