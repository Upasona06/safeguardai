"use client";
import { useEffect, useRef, useState } from "react";
import { Send, Loader2, X } from "lucide-react";
import { analyzeText } from "@/services/api";
import { AnalysisResult } from "@/types";
import toast from "react-hot-toast";

interface Props {
  onResult: (r: AnalysisResult | null) => void;
  onLoading: (l: boolean) => void;
}

const QUICK_EXAMPLES = [
  "I'll make you regret this. Watch your back.",
  "तेरे जैसे लोगों को तो जीने का हक़ नहीं",
  "Hey little one, you're so grown up. Let's keep this our secret.",
];

export default function TextAnalyzer({ onResult, onLoading }: Props) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const mountedRef = useRef(true);
  const requestSeqRef = useRef(0);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const handleAnalyze = async () => {
    if (!text.trim()) {
      toast.error("Please enter some text to analyze");
      return;
    }
    const runId = ++requestSeqRef.current;
    setLoading(true);
    onLoading(true);
    onResult(null);

    try {
      const result = await analyzeText(text);

      if (!mountedRef.current || runId !== requestSeqRef.current) {
        return;
      }

      onResult(result);
      toast.success("Analysis complete");
    } catch (err) {
      if (!mountedRef.current || runId !== requestSeqRef.current) {
        return;
      }

      const message = err instanceof Error ? err.message : "Analysis failed";
      toast.error(message);
    } finally {
      if (!mountedRef.current || runId !== requestSeqRef.current) {
        return;
      }

      setLoading(false);
      onLoading(false);
    }
  };

  return (
    <div className="p-5 flex flex-col gap-4 h-full">
      <div className="flex items-center justify-between">
        <p className="text-xs font-mono text-slate-500 tracking-[0.12em] dark:text-slate-400">INPUT TEXT</p>
        {text && (
          <button onClick={() => setText("")} className="text-slate-400 hover:text-slate-700 dark:hover:text-slate-200">
            <X size={14} />
          </button>
        )}
      </div>

      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Paste text, message, or post to analyze for harmful content..."
        className="w-full min-h-[180px] resize-none rounded-xl border border-slate-300 bg-white/85 p-4 text-sm leading-relaxed text-slate-700 placeholder-slate-400 transition-colors focus:border-orange-400 focus:outline-none dark:border-slate-600 dark:bg-slate-800/60 dark:text-slate-100 dark:placeholder-slate-500"
      />

      <div className="text-right font-mono text-xs text-slate-500 dark:text-slate-400">{text.length} chars</div>

      <div>
        <p className="mb-2 text-xs font-mono text-slate-500 tracking-[0.12em] dark:text-slate-400">QUICK EXAMPLES</p>
        <div className="flex flex-col gap-1">
          {QUICK_EXAMPLES.map((ex, i) => (
            <button
              key={i}
              onClick={() => setText(ex)}
              className="truncate rounded-lg px-2 py-1.5 text-left text-xs text-slate-600 transition-colors hover:bg-white hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-slate-200"
            >
              → {ex}
            </button>
          ))}
        </div>
      </div>

      <button
        onClick={handleAnalyze}
        disabled={loading || !text.trim()}
        className="mt-auto flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-gradient-to-r from-orange-600 to-amber-500 text-white font-bold text-sm disabled:opacity-50 hover:translate-y-[-1px] transition-all shadow-[0_14px_26px_rgba(249,115,22,0.25)]"
      >
        {loading ? (
          <>
            <Loader2 size={15} className="animate-spin" />
            Analyzing...
          </>
        ) : (
          <>
            <Send size={15} />
            Analyze Text
          </>
        )}
      </button>
    </div>
  );
}
