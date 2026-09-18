import { useState } from "react";
import { Copy, Check, FileText } from "lucide-react";

interface Props {
  clause: string;
}

export default function ComplianceClause({ clause }: Props) {
  const [copied, setCopied] = useState(false);

  const copyToClipboard = () => {
    navigator.clipboard.writeText(clause);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
      <div className="flex items-center justify-between border-b border-slate-100 px-4 py-2.5 bg-slate-50">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-sky-600" />
          <span className="text-sm font-semibold text-slate-700">Generated Compliance Clause</span>
        </div>
        <button
          onClick={copyToClipboard}
          className="flex items-center gap-1.5 rounded-md bg-sky-50 px-2.5 py-1 text-xs font-medium text-sky-700 hover:bg-sky-100 transition-colors"
        >
          {copied ? (
            <>
              <Check className="h-3.5 w-3.5" />
              Copied
            </>
          ) : (
            <>
              <Copy className="h-3.5 w-3.5" />
              Copy
            </>
          )}
        </button>
      </div>
      <pre className="px-4 py-3 text-xs leading-relaxed text-slate-700 whitespace-pre-wrap font-mono max-h-64 overflow-y-auto">
        {clause}
      </pre>
    </div>
  );
}
