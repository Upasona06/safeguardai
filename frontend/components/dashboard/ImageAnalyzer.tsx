"use client";
import { useEffect, useRef, useState } from "react";
import { Upload, Image, Loader2, X } from "lucide-react";
import { analyzeImage } from "@/services/api";
import { AnalysisResult } from "@/types";
import toast from "react-hot-toast";

interface Props {
  onResult: (r: AnalysisResult | null) => void;
  onLoading: (l: boolean) => void;
}

export default function ImageAnalyzer({ onResult, onLoading }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const mountedRef = useRef(true);
  const requestSeqRef = useRef(0);

  useEffect(() => {
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const handleFile = (f: File) => {
    if (!f.type.startsWith("image/")) {
      toast.error("Please upload an image file");
      return;
    }
    setFile(f);
    setPreview(URL.createObjectURL(f));
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  };

  const handleAnalyze = async () => {
    if (!file) return;

    const runId = ++requestSeqRef.current;
    setLoading(true);
    onLoading(true);
    onResult(null);

    try {
      const formData = new FormData();
      formData.append("file", file);
      const result = await analyzeImage(formData);

      if (!mountedRef.current || runId !== requestSeqRef.current) {
        return;
      }

      onResult(result);
      toast.success("Image analyzed successfully");
    } catch (err) {
      if (!mountedRef.current || runId !== requestSeqRef.current) {
        return;
      }

      const message = err instanceof Error ? err.message : "Image analysis failed";
      toast.error(message);
    } finally {
      if (!mountedRef.current || runId !== requestSeqRef.current) {
        return;
      }

      setLoading(false);
      onLoading(false);
    }
  };

  const clear = () => {
    setFile(null);
    setPreview(null);
  };

  return (
    <div className="p-5 flex flex-col gap-4">
      <p className="text-xs font-mono text-slate-500 tracking-[0.12em] dark:text-slate-400">UPLOAD IMAGE / SCREENSHOT</p>

      {!preview ? (
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`relative border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center cursor-pointer transition-all duration-200 ${
            dragging
              ? "border-orange-400 bg-orange-50 dark:bg-orange-900/20"
              : "border-slate-300 hover:border-slate-400 hover:bg-white dark:border-slate-600 dark:hover:border-slate-500 dark:hover:bg-slate-800/60"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
          />
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-slate-100 dark:bg-slate-800">
            <Upload size={20} className="text-slate-600 dark:text-slate-300" />
          </div>
          <p className="text-center text-sm font-semibold text-slate-700 dark:text-slate-200">
            Drop an image here or click to upload
          </p>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">PNG, JPG, WEBP up to 10MB</p>
        </div>
      ) : (
        <div className="relative overflow-hidden rounded-xl border border-slate-300 dark:border-slate-600">
          <img src={preview} alt="Preview" className="w-full max-h-48 object-cover" />
          <button
            onClick={clear}
            className="absolute top-2 right-2 w-7 h-7 rounded-full bg-slate-900/70 flex items-center justify-center text-white hover:bg-slate-900"
          >
            <X size={14} />
          </button>
          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent p-3">
            <div className="flex items-center gap-2 text-xs text-white/70">
              <Image size={12} />
              {file?.name} · {((file?.size ?? 0) / 1024).toFixed(1)} KB
            </div>
          </div>
        </div>
      )}

      <div className="glass-red rounded-xl p-3 text-xs border">
        <p className="font-semibold mb-1 text-orange-700 tracking-[0.08em]">OCR + VISUAL ANALYSIS</p>
        <p className="text-slate-700 dark:text-slate-300">
          Our AI extracts text via Tesseract OCR and also analyzes visual context for harmful imagery, memes, and hate symbols.
        </p>
      </div>

      <button
        onClick={handleAnalyze}
        disabled={!file || loading}
        className="flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-gradient-to-r from-orange-600 to-amber-500 text-white font-bold text-sm disabled:opacity-50 hover:translate-y-[-1px] transition-all shadow-[0_14px_26px_rgba(249,115,22,0.25)]"
      >
        {loading ? (
          <>
            <Loader2 size={15} className="animate-spin" />
            Processing...
          </>
        ) : (
          <>
            <Image size={15} />
            Analyze Image
          </>
        )}
      </button>
    </div>
  );
}
