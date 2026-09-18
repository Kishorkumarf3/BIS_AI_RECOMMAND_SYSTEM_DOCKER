/**
 * Bureau of Indian Standards (BIS) Data Contracts & TypeScript Types
 * Used across the Recommendation Engine, Knowledge Graph, and Reverse Audit.
 */

export type NormativeRelation = "testing" | "safety" | "material" | "method" | "dimensional";

export interface NormativeRef {
  is_code: string;
  title: string;
  relation: NormativeRelation;
}

export interface LegalCitation {
  source_pdf: string;
  act_or_regulation: string;
  provision: string;
  excerpt: string;
  applicability: string;
}

export interface BISRecommendation {
  is_code: string;
  title: string;
  score: number;
  scope: string;
  category: string;
  qco_mandatory: boolean;
  crs_applicable: boolean;
  simplified_procedure: boolean;
  fast_track_days: number | null;
  normative_refs: NormativeRef[];
}

export interface RecommendationResponse {
  recommendations: BISRecommendation[];
  compliance_clause: string | null;
  legal_framework: LegalCitation[];
}

export interface OutdatedStandard {
  is_code: string;
  title: string;
  status: string;
  superseded_by: string | null;
}

export interface MissingQCOStandard {
  is_code: string;
  title: string;
  note: string;
}

export interface AuditResult {
  extracted_is_codes: string[];
  flagged_outdated: OutdatedStandard[];
  missing_qco: MissingQCOStandard[];
  summary: string;
}
