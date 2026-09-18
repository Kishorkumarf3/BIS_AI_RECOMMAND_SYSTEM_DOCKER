import { useState, useCallback, useRef } from "react";
import {
  UploadCloud,
  FileText,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Loader2,
  ShieldAlert,
} from "lucide-react";
import { auditPDF, type AuditResult } from "@/lib/api";

export default function ReverseAuditUploader() {
  const [isDragging, setIsDragging] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AuditResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(async (file: File) => {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Please upload a PDF file.");
      return;
    }
    setError(null);
    setFileName(file.name);
    setIsLoading(true);
    setResult(null);
    try {
      const res = await auditPDF(file);
      setResult(res);
    } catch {
      setError("Failed to analyze the PDF. Please try again.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const reset = () => {
    setFileName(null);
    setResult(null);
    setError(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="space-y-4">
      {/* Drop Zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`relative cursor-pointer rounded-xl border-2 border-dashed p-8 text-center transition-all duration-200 ${
          isDragging
            ? "border-sky-400 bg-sky-50 scale-[1.01]"
            : "border-slate-300 bg-slate-50 hover:border-sky-300 hover:bg-sky-50/50"
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf"
          onChange={handleFileSelect}
          className="hidden"
        />
        {isLoading ? (
          <div className="flex flex-col items-center gap-3">
            <Loader2 className="h-10 w-10 animate-spin text-sky-500" />
            <p className="text-sm font-medium text-slate-600">Analyzing tender document…</p>
          </div>
        ) : fileName ? (
          <div className="flex flex-col items-center gap-2">
            <FileText className="h-10 w-10 text-sky-500" />
            <p className="text-sm font-semibold text-slate-700">{fileName}</p>
            <button
              onClick={(e) => {
                e.stopPropagation();
                reset();
              }}
              className="text-xs text-slate-400 hover:text-slate-600 underline"
            >
              Upload a different file
            </button>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <UploadCloud className="h-10 w-10 text-slate-400" />
            <p className="text-sm font-medium text-slate-600">
              Drag & drop a tender PDF here, or click to browse
            </p>
            <p className="text-xs text-slate-400">Supports legacy tender documents</p>
          </div>
        )}
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
          <XCircle className="h-4 w-4 shrink-0" />
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
          {/* Summary */}
          <div className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-4">
            <CheckCircle2 className="h-5 w-5 shrink-0 text-sky-500 mt-0.5" />
            <div>
              <p className="text-sm font-semibold text-slate-800">Audit Complete</p>
              <p className="text-sm text-slate-600 mt-0.5">{result.summary}</p>
            </div>
          </div>

          {/* Extracted IS Codes */}
          {result.extracted_is_codes.length > 0 && (
            <div className="rounded-xl border border-slate-200 bg-white p-4">
              <p className="text-sm font-semibold text-slate-800 mb-2">
                Extracted IS Codes ({result.extracted_is_codes.length})
              </p>
              <div className="flex flex-wrap gap-2">
                {result.extracted_is_codes.map((code) => (
                  <span
                    key={code}
                    className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-mono font-medium text-slate-700"
                  >
                    {code}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Flagged Outdated */}
          {result.flagged_outdated.length > 0 && (
            <div className="rounded-xl border border-amber-200 bg-amber-50 p-4">
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className="h-5 w-5 text-amber-600" />
                <p className="text-sm font-semibold text-amber-800">
                  Outdated / Superseded Standards ({result.flagged_outdated.length})
                </p>
              </div>
              <div className="space-y-2">
                {result.flagged_outdated.map((item) => (
                  <div
                    key={item.is_code}
                    className="flex items-start justify-between rounded-lg bg-white px-3 py-2 border border-amber-100"
                  >
                    <div>
                      <p className="text-sm font-mono font-semibold text-slate-800">{item.is_code}</p>
                      <p className="text-xs text-slate-600">{item.title}</p>
                    </div>
                    <div className="text-right shrink-0 ml-3">
                      <span
                        className={`inline-block rounded-md px-2 py-0.5 text-[10px] font-bold uppercase ${
                          item.status === "Withdrawn"
                            ? "bg-red-100 text-red-700"
                            : "bg-amber-100 text-amber-700"
                        }`}
                      >
                        {item.status}
                      </span>
                      {item.superseded_by && (
                        <p className="text-[10px] text-slate-500 mt-1">
                          Replaced by: {item.superseded_by}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Missing QCO */}
          {result.missing_qco.length > 0 && (
            <div className="rounded-xl border border-rose-200 bg-rose-50 p-4">
              <div className="flex items-center gap-2 mb-3">
                <ShieldAlert className="h-5 w-5 text-rose-600" />
                <p className="text-sm font-semibold text-rose-800">
                  QCO Coverage Gaps ({result.missing_qco.length})
                </p>
              </div>
              <div className="space-y-2">
                {result.missing_qco.map((item) => (
                  <div
                    key={item.is_code}
                    className="flex items-start justify-between rounded-lg bg-white px-3 py-2 border border-rose-100"
                  >
                    <div>
                      <p className="text-sm font-mono font-semibold text-slate-800">{item.is_code}</p>
                      <p className="text-xs text-slate-600">{item.title}</p>
                      <p className="text-[10px] text-rose-600 mt-0.5">{item.note}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {result.flagged_outdated.length === 0 &&
            result.missing_qco.length === 0 && (
              <div className="flex items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
                <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                <p className="text-sm font-medium text-emerald-800">
                  All extracted standards are current with proper QCO coverage.
                </p>
              </div>
            )}
        </div>
      )}
    </div>
  );
}
