import {
  Shield,
  Zap,
  FileText,
  ChevronDown,
  ChevronRight,
  Network,
  Scale,
} from "lucide-react";
import { useState } from "react";
import type { BISRecommendation } from "@/types/bis";
import StandardsGraph from "@/components/StandardsGraph";

interface Props {
  recommendation: BISRecommendation;
  index: number;
}

export default function RecommendationCard({ recommendation: rec, index }: Props) {
  const [expanded, setExpanded] = useState(false);
  const [showGraph, setShowGraph] = useState(false);
  const matchPercent = Math.round(rec.score * 100);

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 transition-all hover:border-sky-200 hover:shadow-sm">
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 min-w-0">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-sky-50">
            <FileText className="h-5 w-5 text-sky-600" />
          </div>
          <div className="min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-mono text-sm font-bold text-slate-900">{rec.is_code}</span>
              <span className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[10px] font-medium text-slate-500">
                #{index + 1}
              </span>
            </div>
            <p className="text-sm text-slate-600 mt-0.5 leading-snug">{rec.title}</p>
            <p className="text-xs text-slate-400 mt-0.5">{rec.category}</p>
          </div>
        </div>
        <div className="shrink-0 text-right">
          <div className="flex items-baseline gap-0.5">
            <span className="text-lg font-bold text-sky-600">{matchPercent}</span>
            <span className="text-xs text-slate-400">%</span>
          </div>
          <span className="text-[10px] text-slate-400">match</span>
        </div>
      </div>

      {/* Flags */}
      <div className="mt-3 flex flex-wrap gap-1.5">
        {rec.qco_mandatory && (
          <span className="inline-flex items-center gap-1 rounded-md bg-red-50 px-2 py-1 text-[10px] font-semibold text-red-700">
            <Shield className="h-3 w-3" />
            QCO Mandatory
          </span>
        )}
        {rec.crs_applicable && (
          <span className="inline-flex items-center gap-1 rounded-md bg-amber-50 px-2 py-1 text-[10px] font-semibold text-amber-700">
            <Shield className="h-3 w-3" />
            CRS Required
          </span>
        )}
        {rec.simplified_procedure && (
          <span className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-1 text-[10px] font-semibold text-emerald-700">
            <Zap className="h-3 w-3" />
            30-Day Fast Track
          </span>
        )}
      </div>

      {/* Scope preview / expand */}
      <div className="mt-3">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs font-medium text-sky-600 hover:text-sky-700"
        >
          {expanded ? <ChevronDown className="h-3.5 w-3.5" /> : <ChevronRight className="h-3.5 w-3.5" />}
          {expanded ? "Hide details" : "View scope & references"}
        </button>
        {expanded && (
          <div className="mt-2 space-y-3 animate-in fade-in slide-in-from-top-1 duration-200">
            <p className="text-xs text-slate-600 leading-relaxed">{rec.scope}</p>

            {/* Statutory Legal Mandate */}
            <div className="rounded-lg border border-slate-200 bg-slate-50/80 p-2.5 text-xs">
              <div className="flex items-center gap-1.5 font-semibold text-slate-800 mb-1">
                <Scale className="h-3.5 w-3.5 text-indigo-600" />
                <span>Statutory Regulatory Framework & Mandate</span>
              </div>
              <ul className="space-y-1 text-[11px] text-slate-600 list-disc list-inside">
                {rec.qco_mandatory && (
                  <li>
                    <strong className="text-slate-700">BIS Act 2016 (Section 16):</strong> Enforced under mandatory Quality Control Order (QCO). Supply of non-certified goods attracts penal liabilities under Section 29.
                  </li>
                )}
                {rec.simplified_procedure && (
                  <li>
                    <strong className="text-slate-700">Conformity Assessment Regulations, 2018 (Option 2):</strong> Listed in Annexure II(C) for 30-day accelerated grant of license based on recognized third-party test reports.
                  </li>
                )}
                {rec.crs_applicable && (
                  <li>
                    <strong className="text-slate-700">Compulsory Registration Scheme (Scheme-II):</strong> Requires mandatory registration number from BIS before tender delivery.
                  </li>
                )}
                {!rec.qco_mandatory && !rec.simplified_procedure && (
                  <li>
                    <strong className="text-slate-700">Conformity Assessment Scheme-I:</strong> Voluntary or tender-stipulated ISI Mark certification under BIS Act, 2016.
                  </li>
                )}
              </ul>
            </div>

            {rec.normative_refs.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-slate-700 mb-1.5">
                  Normative References ({rec.normative_refs.length})
                </p>
                <div className="space-y-1">
                  {rec.normative_refs.map((ref) => (
                    <div
                      key={ref.is_code}
                      className="flex items-center gap-2 rounded-md bg-slate-50 px-2.5 py-1.5"
                    >
                      <span className="font-mono text-xs font-semibold text-slate-700">
                        {ref.is_code}
                      </span>
                      <span className="text-xs text-slate-500 truncate">{ref.title}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {rec.normative_refs.length > 0 && (
              <button
                onClick={() => setShowGraph(!showGraph)}
                className="flex items-center gap-1.5 text-xs font-medium text-sky-600 hover:text-sky-700"
              >
                <Network className="h-3.5 w-3.5" />
                {showGraph ? "Hide" : "Show"} Knowledge Graph
              </button>
            )}

            {showGraph && (
              <div className="mt-2 animate-in fade-in duration-200">
                <StandardsGraph standard={rec} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
