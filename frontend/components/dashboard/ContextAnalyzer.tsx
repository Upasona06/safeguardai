"use client";
import { useEffect, useRef, useState } from "react";
import { Plus, Trash2, Loader2, MessageSquare } from "lucide-react";
import { analyzeContext } from "@/services/api";
import { AnalysisResult, ConversationMessage } from "@/types";
import toast from "react-hot-toast";

interface Props {
  onResult: (r: AnalysisResult | null) => void;
  onLoading: (l: boolean) => void;
}

export default function ContextAnalyzer({ onResult, onLoading }: Props) {
  const [messages, setMessages] = useState<ConversationMessage[]>([
    { role: "sender", text: "" },
  ]);
  const [loading, setLoading] = useState(false);
  const mountedRef = useRef(true);
  const requestSeqRef = useRef(0);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const addMessage = () => {
    setMessages((prev) => [
      ...prev,
      { role: prev.length % 2 === 0 ? "sender" : "receiver", text: "" },
    ]);
  };

  const updateMessage = (i: number, field: keyof ConversationMessage, val: string) => {
    setMessages((prev) => {
      const updated = [...prev];
      updated[i] = { ...updated[i], [field]: val };
      return updated;
    });
  };

  const removeMessage = (i: number) => {
    setMessages((prev) => prev.filter((_, idx) => idx !== i));
  };

  const handleAnalyze = async () => {
    const validMessages = messages.filter((m) => m.text.trim());
    if (validMessages.length < 2) {
      toast.error("Please add at least 2 messages for context analysis");
      return;
    }

    const runId = ++requestSeqRef.current;
    setLoading(true);
    onLoading(true);
    onResult(null);

    try {
      const result = await analyzeContext(validMessages);

      if (!mountedRef.current || runId !== requestSeqRef.current) {
        return;
      }

      onResult(result);
      toast.success("Context analysis complete");
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
    <div className="p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <p className="text-xs font-mono text-slate-500 tracking-[0.12em] dark:text-slate-400">CONVERSATION THREAD</p>
        <button
          onClick={addMessage}
          className="flex items-center gap-1 text-xs text-slate-500 transition-colors hover:text-slate-800 dark:text-slate-400 dark:hover:text-slate-200"
        >
          <Plus size={12} /> Add message
        </button>
      </div>

      <div className="flex flex-col gap-2 max-h-[280px] overflow-y-auto pr-1">
        {messages.map((msg, i) => (
          <div key={i} className={`flex gap-2 ${msg.role === "receiver" ? "flex-row-reverse" : ""}`}>
            <div className={`flex-shrink-0 w-6 h-6 rounded-full text-[10px] font-bold flex items-center justify-center ${
              msg.role === "sender" ? "bg-orange-100 text-orange-700" : "bg-sky-100 text-sky-700"
            }`}>
              {msg.role === "sender" ? "A" : "B"}
            </div>
            <div className="flex-1 flex gap-1">
              <input
                value={msg.text}
                onChange={(e) => updateMessage(i, "text", e.target.value)}
                placeholder={`Message ${i + 1}...`}
                className="flex-1 rounded-lg border border-slate-300 bg-white/85 px-3 py-2 text-xs text-slate-700 placeholder-slate-400 transition-colors focus:border-orange-400 focus:outline-none dark:border-slate-600 dark:bg-slate-800/60 dark:text-slate-100 dark:placeholder-slate-500"
              />
              {messages.length > 1 && (
                <button
                  onClick={() => removeMessage(i)}
                  className="text-slate-400 transition-colors hover:text-rose-600 dark:hover:text-rose-400"
                >
                  <Trash2 size={12} />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>

      <div className="glass-red rounded-xl border p-3 text-xs text-slate-700 dark:text-slate-300">
        <p className="text-orange-700 font-semibold mb-1 tracking-[0.08em]">CONTEXT-AWARE ANALYSIS</p>
        Detects escalation patterns, grooming progressions, and sustained harassment across the full conversation thread.
      </div>

      <button
        onClick={handleAnalyze}
        disabled={loading}
        className="flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-gradient-to-r from-orange-600 to-amber-500 text-white font-bold text-sm disabled:opacity-50 hover:translate-y-[-1px] transition-all shadow-[0_14px_26px_rgba(249,115,22,0.25)]"
      >
        {loading ? (
          <>
            <Loader2 size={15} className="animate-spin" />
            Analyzing Context...
          </>
        ) : (
          <>
            <MessageSquare size={15} />
            Analyze Conversation
          </>
        )}
      </button>
    </div>
  );
}
