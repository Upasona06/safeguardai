export interface ToxicToken {
  token: string;
  score: number;
  category: string;
}

export interface LegalMapping {
  law: string;
  section: string;
  description: string;
  severity: string;
}

export interface AnalysisResult {
  id: string;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  overall_score: number;
  labels: {
    cyberbullying: number;
    threat: number;
    hate_speech: number;
    sexual_harassment: number;
    grooming: number;
  };
  toxic_tokens: ToxicToken[];
  original_text: string;
  highlighted_text: string;
  legal_mappings: LegalMapping[];
  explanation: string;
  timestamp: string;
  language_detected: string;
  image_url?: string;
  fir_id?: string;
}

export interface FIRData {
  complainant_name: string;
  complainant_contact: string;
  incident_date: string;
  incident_description: string;
  evidence_urls: string[];
  legal_sections: string[];
  analysis_id: string;
}

export interface ConversationMessage {
  role: "sender" | "receiver";
  text: string;
  timestamp?: string;
}

export interface AnalyticsData {
  total_reports: number;
  critical_cases: number;
  fir_generated: number;
  avg_response_time: number;
  daily_counts: { date: string; count: number }[];
  category_breakdown: Record<string, number>;
}
