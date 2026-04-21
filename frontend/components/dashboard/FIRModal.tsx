"use client";

import { useState } from "react";
import { CheckCircle2, Download, FileText, Loader2, X } from "lucide-react";
import { ApiUserContext, generateFIRPDF, downloadFIR } from "@/services/api";
import { AnalysisResult } from "@/types";
import toast from "react-hot-toast";

interface Props {
  firId: string;
  result: AnalysisResult;
  user?: ApiUserContext;
  onClose: () => void;
}

export default function FIRModal({ firId, result, user, onClose }: Props) {
  const [form, setForm] = useState({
    complainant_name: "",
    complainant_contact: "",
    complainant_address: "",
    accused_name: "",
    accused_details: "",
    incident_date: new Date().toISOString().split("T")[0],
    incident_time: new Date().toTimeString().split(" ")[0],
    incident_location: "Online Platform",
    additional_info: "",
  });
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async () => {
    if (!form.complainant_name || !form.complainant_contact) {
      toast.error("Please fill in all required fields");
      return;
    }

    setSubmitting(true);
    try {
      await generateFIRPDF({
        fir_id: firId,
        analysis_id: result.id,
        ...form,
        legal_sections: result.legal_mappings.map((mapping) => `${mapping.law} ${mapping.section}`),
        evidence_urls: result.image_url ? [result.image_url] : [],
      }, user);
      setSubmitted(true);
      toast.success("FIR report finalized");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Failed to generate FIR";
      toast.error(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-slate-900/45 dark:bg-slate-950/65 backdrop-blur-sm"
        onClick={onClose}
        aria-label="Close FIR modal"
      />

      <div className="glass relative z-10 max-h-[92vh] w-full max-w-2xl overflow-y-auto rounded-3xl p-6 md:p-7 dark:bg-slate-800/50">
        <header className="mb-5 flex items-start justify-between gap-3 border-b border-slate-300 dark:border-slate-700 pb-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500 dark:text-slate-400">FIR Generation</p>
            <h3 className="mt-1 text-xl font-black text-slate-900 dark:text-white">Finalize incident report</h3>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">Reference ID: {firId}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-xl border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-700 p-2 text-slate-600 dark:text-slate-400 transition hover:border-slate-400 dark:hover:border-slate-500 hover:text-slate-900 dark:hover:text-slate-300"
          >
            <X size={16} />
          </button>
        </header>

        {!submitted ? (
          <div className="space-y-4">
            <section className="rounded-xl border border-amber-200 dark:border-amber-900/40 bg-amber-50 dark:bg-amber-900/20 p-3">
              <p className="text-xs font-semibold uppercase tracking-[0.12em] text-amber-700 dark:text-amber-400">Triggered Legal Sections</p>
              <div className="mt-2 flex flex-wrap gap-1.5">
                {result.legal_mappings.map((mapping) => (
                  <span
                    key={mapping.section}
                    className="rounded-full border border-amber-200 dark:border-amber-900/40 bg-white dark:bg-slate-700 px-2.5 py-1 text-[11px] font-semibold text-amber-700 dark:text-amber-400"
                  >
                    {mapping.section}
                  </span>
                ))}
              </div>
            </section>

            <div>
              <p className="mb-3 text-xs font-bold uppercase text-slate-600 dark:text-slate-400 tracking-widest">Complainant Details</p>
              <div className="grid gap-3 md:grid-cols-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                  Full Name *
                  <input
                    value={form.complainant_name}
                    onChange={(event) => setForm({ ...form, complainant_name: event.target.value })}
                    placeholder="Full legal name"
                    className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-700 placeholder-slate-400 focus:border-orange-400 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500"
                  />
                </label>

                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                  Contact Number *
                  <input
                    value={form.complainant_contact}
                    onChange={(event) => setForm({ ...form, complainant_contact: event.target.value })}
                    placeholder="+91 98XXXXXXXX"
                    className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-700 placeholder-slate-400 focus:border-orange-400 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500"
                  />
                </label>
              </div>
              <label className="mt-3 block text-sm font-semibold text-slate-700 dark:text-slate-300">
                Address
                <input
                  value={form.complainant_address}
                  onChange={(event) => setForm({ ...form, complainant_address: event.target.value })}
                  placeholder="Residential address"
                  className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-700 placeholder-slate-400 focus:border-orange-400 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500"
                />
              </label>
            </div>

            <div>
              <p className="mb-3 text-xs font-bold uppercase text-slate-600 tracking-widest dark:text-slate-400">Against Whom (Accused)</p>
              <div className="grid gap-3 md:grid-cols-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                  Name/Account Name
                  <input
                    value={form.accused_name}
                    onChange={(event) => setForm({ ...form, accused_name: event.target.value })}
                    placeholder="Person/account being complained against"
                    className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-700 placeholder-slate-400 focus:border-orange-400 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500"
                  />
                </label>

                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                  Username/Profile URL
                  <input
                    value={form.accused_details}
                    onChange={(event) => setForm({ ...form, accused_details: event.target.value })}
                    placeholder="@username or profile link"
                    className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-700 placeholder-slate-400 focus:border-orange-400 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500"
                  />
                </label>
              </div>
            </div>

            <div>
              <p className="mb-3 text-xs font-bold uppercase text-slate-600 tracking-widest dark:text-slate-400">Incident Details</p>
              <div className="grid gap-3 md:grid-cols-2">
                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                  Date
                  <input
                    type="date"
                    value={form.incident_date}
                    onChange={(event) => setForm({ ...form, incident_date: event.target.value })}
                    className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-700 focus:border-orange-400 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
                  />
                </label>

                <label className="text-sm font-semibold text-slate-700 dark:text-slate-300">
                  Time (IST)
                  <input
                    type="time"
                    value={form.incident_time}
                    onChange={(event) => setForm({ ...form, incident_time: event.target.value })}
                    className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-700 focus:border-orange-400 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
                  />
                </label>
              </div>

              <label className="mt-3 block text-sm font-semibold text-slate-700 dark:text-slate-300">
                Incident Location
                <input
                  value={form.incident_location}
                  onChange={(event) => setForm({ ...form, incident_location: event.target.value })}
                  placeholder="Online platform, social media site, etc."
                  className="mt-1.5 w-full rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-700 placeholder-slate-400 focus:border-orange-400 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500"
                />
              </label>
            </div>

            <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300">
              Additional Details / Description
              <textarea
                rows={4}
                value={form.additional_info}
                onChange={(event) => setForm({ ...form, additional_info: event.target.value })}
                placeholder="Detailed description of the incident, context, prior incidents, etc."
                className="mt-1.5 w-full resize-none rounded-xl border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-700 placeholder-slate-400 focus:border-orange-400 focus:outline-none dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500"
              />
            </label>

            <button
              type="button"
              onClick={handleSubmit}
              disabled={submitting}
              className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-orange-600 to-amber-500 px-4 py-3 text-sm font-bold text-white shadow-[0_14px_26px_rgba(249,115,22,0.25)] transition hover:translate-y-[-1px] disabled:opacity-70"
            >
              {submitting ? (
                <>
                  <Loader2 size={15} className="animate-spin" />
                  Generating PDF...
                </>
              ) : (
                <>
                  <FileText size={15} />
                  Generate Court-Ready FIR
                </>
              )}
            </button>
          </div>
        ) : (
          <div className="py-8 text-center">
            <div className="mx-auto mb-4 inline-flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-emerald-700">
              <CheckCircle2 size={26} />
            </div>
            <h4 className="text-xl font-black text-slate-900 dark:text-white">FIR successfully generated</h4>
            <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-slate-600 dark:text-slate-400">
              The final report includes legal mappings, timestamps, and evidence links ready for download and further submission.
            </p>
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <button
                type="button"
                onClick={() => downloadFIR(firId, user)}
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-orange-600 to-amber-500 px-5 py-3 text-sm font-bold text-white"
              >
                <Download size={15} />
                Download PDF
              </button>
              <button
                type="button"
                onClick={onClose}
                className="rounded-xl border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-slate-700 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-300"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
