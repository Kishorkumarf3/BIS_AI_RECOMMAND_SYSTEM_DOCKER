import { Scale, BookOpen, ShieldAlert, FileText, CheckCircle2, AlertOctagon } from "lucide-react";
import type { LegalCitation } from "@/types/bis";

interface Props {
  legalFramework: LegalCitation[];
}

export default function LegalFrameworkView({ legalFramework }: Props) {
  if (!legalFramework || legalFramework.length === 0) return null;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden transition-all">
      {/* Header */}
      <div className="border-b border-slate-100 bg-gradient-to-r from-slate-900 to-slate-800 px-5 py-4 text-white">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-500/20 text-sky-400 border border-sky-400/30">
            <Scale className="h-4 w-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold tracking-tight text-white flex items-center gap-2">
              Applicable BIS Act Provisions & Gazette Regulations
              <span className="rounded-full bg-sky-500/20 px-2 py-0.5 text-[10px] font-semibold text-sky-300 border border-sky-400/30">
                {legalFramework.length} Provisions Cited
              </span>
            </h3>
            <p className="text-xs text-slate-300 mt-0.5">
              Statutory rules and Gazette orders retrieved from the official BIS regulations library
            </p>
          </div>
        </div>
      </div>

      {/* Citations Grid */}
      <div className="p-5 space-y-4 bg-slate-50/50">
        {legalFramework.map((item, idx) => {
          const isAct = item.act_or_regulation.toLowerCase().includes("act");
          const isCA = item.act_or_regulation.toLowerCase().includes("conformity");

          const badgeColor = isAct
            ? "bg-indigo-50 text-indigo-700 border-indigo-200"
            : isCA
            ? "bg-emerald-50 text-emerald-700 border-emerald-200"
            : "bg-amber-50 text-amber-700 border-amber-200";

          return (
            <div
              key={idx}
              className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm hover:border-sky-300 transition-all"
            >
              <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-2.5 mb-2.5">
                <div className="flex items-center gap-2">
                  <span className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] font-bold border ${badgeColor}`}>
                    {isAct ? <Scale className="h-3 w-3" /> : isCA ? <CheckCircle2 className="h-3 w-3" /> : <ShieldAlert className="h-3 w-3" />}
                    {item.act_or_regulation}
                  </span>
                </div>
                <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1">
                  <FileText className="h-3 w-3 text-slate-400" />
                  {item.source_pdf}
                </span>
              </div>

              {/* Section / Provision */}
              <h4 className="text-xs font-bold text-slate-900 mb-1.5 flex items-center gap-1.5">
                <BookOpen className="h-3.5 w-3.5 text-sky-600" />
                {item.provision}
              </h4>

              {/* Legal Excerpt */}
              <blockquote className="rounded-lg bg-slate-50 border-l-2 border-sky-500 px-3 py-2 text-xs text-slate-600 leading-relaxed italic mb-2.5 font-sans">
                "{item.excerpt}"
              </blockquote>

              {/* Tender Applicability */}
              <div className="flex items-start gap-1.5 text-[11px] text-slate-700 bg-amber-50/60 rounded-md p-2 border border-amber-100">
                <AlertOctagon className="h-3.5 w-3.5 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-amber-900">Procurement Officer Mandate: </span>
                  <span className="text-slate-700">{item.applicability}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
