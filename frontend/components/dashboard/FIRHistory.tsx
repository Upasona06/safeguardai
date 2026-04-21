"use client";

import { useEffect, useState } from "react";
import { Download, FileText, Calendar, User, AlertCircle, Loader2 } from "lucide-react";
import toast from "react-hot-toast";
import { useSession } from "next-auth/react";
import { downloadFIR, firHistoryUpdatedEventName, getFIRHistory } from "@/services/api";

interface FIRItem {
  fir_id: string;
  status: string;
  complainant_name: string;
  accused_name?: string;
  incident_date: string;
  incident_location?: string;
  created_at: string;
  finalized_at?: string;
  pdf_url?: string;
}

export default function FIRHistory() {
  const { data: session, status } = useSession();
  const [firs, setFirs] = useState<FIRItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [totalCount, setTotalCount] = useState(0);

  useEffect(() => {
    if (status === "loading") {
      return;
    }

    const refresh = () => {
      void fetchFIRHistory();
    };

    refresh();
    window.addEventListener(firHistoryUpdatedEventName, refresh);

    return () => {
      window.removeEventListener(firHistoryUpdatedEventName, refresh);
    };
  }, [status, session?.user?.id, session?.user?.email]);

  const fetchFIRHistory = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await getFIRHistory(20, 0, session?.user);
      setFirs(response.firs);
      setTotalCount(response.total);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : "Failed to fetch FIR history";
      setError(errorMsg);
      toast.error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadFIR = (firId: string) => {
    try {
      downloadFIR(firId, session?.user);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to download FIR";
      toast.error(message);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString("en-IN", {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
    } catch {
      return dateString || "—";
    }
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      draft: "bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-300",
      finalized: "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-300",
      pending: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
    };
    return styles[status as keyof typeof styles] || "bg-gray-100 text-gray-800 dark:bg-slate-800 dark:text-slate-300";
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 size={20} className="animate-spin text-orange-500 mr-2" />
        <p className="text-slate-600 dark:text-slate-400">Loading FIR history...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-4 dark:border-red-900/40 dark:bg-red-950/20">
        <div className="flex items-start gap-3">
          <AlertCircle size={18} className="text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold text-red-900 dark:text-red-300">Error loading FIR history</p>
            <p className="mt-1 text-sm text-red-700 dark:text-red-300">{error}</p>
            <button
              onClick={fetchFIRHistory}
              className="mt-3 rounded px-3 py-1.5 text-sm font-semibold text-red-700 transition hover:bg-red-100 dark:text-red-300 dark:hover:bg-red-900/30"
            >
              Try Again
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (firs.length === 0) {
    return (
      <div className="text-center py-12">
        <FileText size={40} className="mx-auto mb-3 text-slate-300 dark:text-slate-600" />
        <p className="font-medium text-slate-600 dark:text-slate-300">No FIR reports yet</p>
        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">Generate your first FIR from an analysis result</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold text-slate-900 dark:text-white">FIR History</h3>
          <p className="mt-0.5 text-sm text-slate-500 dark:text-slate-400">{totalCount} total report{totalCount !== 1 ? "s" : ""}</p>
        </div>
        <button
          onClick={fetchFIRHistory}
          className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold transition hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
        >
          Refresh
        </button>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-700">
        <table className="w-full text-sm">
          <thead className="border-b border-slate-200 bg-slate-50 dark:border-slate-700 dark:bg-slate-800/50">
            <tr>
              <th className="px-4 py-3 text-left font-semibold text-slate-700 dark:text-slate-200">FIR ID</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700 dark:text-slate-200">Complainant</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700 dark:text-slate-200">Against</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700 dark:text-slate-200">Date</th>
              <th className="px-4 py-3 text-left font-semibold text-slate-700 dark:text-slate-200">Status</th>
              <th className="px-4 py-3 text-center font-semibold text-slate-700 dark:text-slate-200">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
            {firs.map((fir) => (
              <tr key={fir.fir_id} className="transition hover:bg-slate-50 dark:hover:bg-slate-800/40">
                <td className="px-4 py-3">
                  <code className="rounded bg-slate-100 px-2 py-1 font-mono text-xs text-slate-700 dark:bg-slate-800 dark:text-slate-300">
                    {fir.fir_id}
                  </code>
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <User size={14} className="text-slate-400 dark:text-slate-500" />
                    <span className="max-w-[200px] truncate font-medium text-slate-900 dark:text-slate-100">
                      {fir.complainant_name || "—"}
                    </span>
                  </div>
                </td>
                <td className="max-w-[200px] truncate px-4 py-3 text-slate-700 dark:text-slate-300">
                  {fir.accused_name || "—"}
                </td>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    <Calendar size={14} className="text-slate-400 dark:text-slate-500" />
                    <span className="text-slate-700 dark:text-slate-300">{formatDate(fir.incident_date)}</span>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-semibold ${getStatusBadge(
                      fir.status
                    )}`}
                  >
                    {fir.status.charAt(0).toUpperCase() + fir.status.slice(1)}
                  </span>
                </td>
                <td className="px-4 py-3 text-center">
                  {fir.status === "finalized" ? (
                    <button
                      onClick={() => handleDownloadFIR(fir.fir_id)}
                      className="inline-flex items-center gap-1.5 rounded px-3 py-1.5 text-xs font-semibold text-orange-600 transition hover:bg-orange-50 dark:text-orange-400 dark:hover:bg-orange-950/30"
                      title="Download PDF"
                    >
                      <Download size={14} />
                      Download
                    </button>
                  ) : (
                    <span className="text-xs text-slate-500 dark:text-slate-400">Not Ready</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
