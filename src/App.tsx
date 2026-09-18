import { useState } from "react";
import {
  Search,
  Loader2,
  Sparkles,
  FileSearch,
  Network,
  ShieldCheck,
  BookOpen,
  AlertCircle,
} from "lucide-react";
import { fetchRecommendations, type LegalCitation } from "@/lib/api";
import type { BISRecommendation } from "@/types/bis";
import RecommendationCard from "@/components/RecommendationCard";
import ComplianceClause from "@/components/ComplianceClause";
import LegalFrameworkView from "@/components/LegalFrameworkView";
import ReverseAuditUploader from "@/components/ReverseAuditUploader";
import StandardsGraph from "@/components/StandardsGraph";

type Tab = "recommend" | "audit" | "graph";

export default function App() {
  const [activeTab, setActiveTab] = useState<Tab>("recommend");
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [recommendations, setRecommendations] = useState<BISRecommendation[]>([]);
  const [clause, setClause] = useState<string | null>(null);
  const [legalFramework, setLegalFramework] = useState<LegalCitation[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);


  const handleSearch = async () => {
    if (query.trim().length < 5) return;
    setIsLoading(true);
    setError(null);
    setHasSearched(true);
    try {
      const data = await fetchRecommendations(query, 5, true);
      setRecommendations(data.recommendations);
      setClause(data.compliance_clause);
      setLegalFramework(data.legal_framework || []);
    } catch (err: any) {
      const msg = err?.message || "";
      if (msg.includes("Failed to fetch") || msg.includes("NetworkError")) {
        setError(
          "Unable to connect to the backend server. If using Render free tier, the backend may be waking up from sleep (50s cold start). Please wait a moment and click search again."
        );
      } else {
        setError(msg || "Failed to fetch recommendations. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const sampleQueries = [
    "Mild steel tubes for water distribution in municipal plumbing",
    "Structural steel plates for bridge construction",
    "Ordinary Portland cement for RCC construction",
    "Electrical plugs and socket-outlets for residential wiring",
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-gradient-to-br from-sky-500 to-sky-700 shadow-sm">
              <ShieldCheck className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-sm font-bold leading-tight text-slate-900">
                BIS Standards AI
              </h1>
              <p className="text-[10px] leading-tight text-slate-500">
                Recommendation Engine for Procurement
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Tab Navigation */}
      <div className="sticky top-[57px] z-30 border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl gap-1 px-4">
          <TabButton
            active={activeTab === "recommend"}
            onClick={() => setActiveTab("recommend")}
            icon={<Search className="h-4 w-4" />}
            label="Recommend"
          />
          <TabButton
            active={activeTab === "audit"}
            onClick={() => setActiveTab("audit")}
            icon={<FileSearch className="h-4 w-4" />}
            label="Reverse Audit"
          />
          <TabButton
            active={activeTab === "graph"}
            onClick={() => setActiveTab("graph")}
            icon={<Network className="h-4 w-4" />}
            label="Knowledge Graph"
          />
        </div>
      </div>

      {/* Main Content */}
      <main className="mx-auto max-w-6xl px-4 py-6">
        {activeTab === "recommend" && (
          <div className="space-y-5">
            {/* Search Bar */}
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="h-4 w-4 text-sky-500" />
                <h2 className="text-sm font-semibold text-slate-800">
                  Describe your procurement requirement
                </h2>
              </div>
              <div className="flex flex-col sm:flex-row gap-2">
                <textarea
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) handleSearch();
                  }}
                  rows={2}
                  placeholder="e.g., Mild steel tubes for water distribution in municipal plumbing…"
                  className="flex-1 resize-none rounded-lg border border-slate-200 px-3 py-2.5 text-sm text-slate-700 placeholder:text-slate-400 focus:border-sky-400 focus:outline-none focus:ring-2 focus:ring-sky-100 transition-all"
                />
                <button
                  onClick={handleSearch}
                  disabled={isLoading || query.trim().length < 5}
                  className="flex items-center justify-center gap-2 rounded-lg bg-sky-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-all hover:bg-sky-700 disabled:bg-slate-300 disabled:cursor-not-allowed sm:self-end"
                  style={{ minHeight: "46px" }}
                >
                  {isLoading ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Search className="h-4 w-4" />
                  )}
                  {isLoading ? "Searching…" : "Find Standards"}
                </button>
              </div>

              {/* Sample queries */}
              {!hasSearched && (
                <div className="mt-3">
                  <p className="text-xs text-slate-400 mb-2">Try a sample:</p>
                  <div className="flex flex-wrap gap-2">
                    {sampleQueries.map((q) => (
                      <button
                        key={q}
                        onClick={() => setQuery(q)}
                        className="rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs text-slate-600 hover:border-sky-200 hover:bg-sky-50 hover:text-sky-700 transition-all"
                      >
                        {q.length > 50 ? q.slice(0, 50) + "…" : q}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Error */}
            {error && (
              <div className="flex items-center gap-2 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
                <AlertCircle className="h-4 w-4 shrink-0" />
                {error}
              </div>
            )}

            {/* Loading skeleton */}
            {isLoading && (
              <div className="space-y-3">
                {[1, 2, 3].map((i) => (
                  <div
                    key={i}
                    className="h-24 rounded-xl border border-slate-200 bg-white animate-pulse"
                    style={{ animationDelay: `${i * 100}ms` }}
                  />
                ))}
              </div>
            )}

            {/* Results */}
            {!isLoading && recommendations.length > 0 && (
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-slate-700">
                    {recommendations.length} Matching Standards Found
                  </p>
                </div>
                {recommendations.map((rec, i) => (
                  <RecommendationCard key={rec.is_code} recommendation={rec} index={i} />
                ))}
              </div>
            )}

            {/* Compliance Clause */}
            {!isLoading && clause && (
              <ComplianceClause clause={clause} />
            )}

            {/* Applicable Statutory Acts, Rules & Gazette Regulations */}
            {!isLoading && legalFramework.length > 0 && (
              <LegalFrameworkView legalFramework={legalFramework} />
            )}

            {/* Empty state */}
            {!isLoading && !error && hasSearched && recommendations.length === 0 && (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <BookOpen className="h-12 w-12 text-slate-300" />
                <p className="mt-3 text-sm font-medium text-slate-600">
                  No matching standards found
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  Try rephrasing your requirement with more specific product details.
                </p>
              </div>
            )}

            {/* Initial state */}
            {!hasSearched && !isLoading && (
              <div className="flex flex-col items-center justify-center py-16 text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-sky-50">
                  <Search className="h-8 w-8 text-sky-400" />
                </div>
                <p className="mt-4 text-sm font-medium text-slate-600">
                  Enter a procurement requirement to find applicable BIS standards
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  Natural language search across the Indian Standards catalog
                </p>
              </div>
            )}
          </div>
        )}

        {activeTab === "audit" && (
          <div className="space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-1">
                <FileSearch className="h-4 w-4 text-sky-500" />
                <h2 className="text-sm font-semibold text-slate-800">Reverse Audit</h2>
              </div>
              <p className="text-xs text-slate-500 mb-4">
                Upload a draft tender PDF to automatically detect outdated IS codes,
                missing QCO flags, and superseded standards.
              </p>
              <ReverseAuditUploader />
            </div>
          </div>
        )}

        {activeTab === "graph" && (
          <div className="space-y-4">
            <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex items-center gap-2 mb-1">
                <Network className="h-4 w-4 text-sky-500" />
                <h2 className="text-sm font-semibold text-slate-800">Standards Knowledge Graph</h2>
              </div>
              <p className="text-xs text-slate-500 mb-4">
                Visualize the relationships between a primary product standard and its mandatory
                normative references. Search first to populate the graph.
              </p>
              {recommendations.length > 0 ? (
                <div className="space-y-4">
                  {recommendations.slice(0, 3).map((rec) => (
                    <div key={rec.is_code}>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="font-mono text-sm font-bold text-slate-900">{rec.is_code}</span>
                        <span className="text-xs text-slate-500">{rec.title}</span>
                      </div>
                      <GraphWrapper rec={rec} />
                    </div>
                  ))}
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <Network className="h-12 w-12 text-slate-300" />
                  <p className="mt-3 text-sm font-medium text-slate-600">
                    Run a search first to view the knowledge graph
                  </p>
                  <button
                    onClick={() => setActiveTab("recommend")}
                    className="mt-3 rounded-lg bg-sky-600 px-4 py-2 text-xs font-semibold text-white hover:bg-sky-700 transition-colors"
                  >
                    Go to Search
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </main>


    </div>
  );
}

// --- Helper components ---

function TabButton({
  active,
  onClick,
  icon,
  label,
}: {
  active: boolean;
  onClick: () => void;
  icon: React.ReactNode;
  label: string;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 border-b-2 px-3 py-2.5 text-sm font-medium transition-all ${
        active
          ? "border-sky-600 text-sky-700"
          : "border-transparent text-slate-500 hover:text-slate-700"
      }`}
    >
      {icon}
      {label}
    </button>
  );
}

function GraphWrapper({ rec }: { rec: BISRecommendation }) {
  return <StandardsGraph standard={rec} />;
}
