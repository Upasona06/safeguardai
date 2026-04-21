import axios from "axios";
import { AnalysisResult, ConversationMessage } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_TIMEOUT_MS = Number(process.env.NEXT_PUBLIC_API_TIMEOUT_MS || 180000);
const FIR_HISTORY_UPDATED_EVENT = "fir-history-updated";

export interface ApiUserContext {
  id?: string | null;
  email?: string | null;
}

function buildUserHeaders(user?: ApiUserContext): Record<string, string> {
  const headers: Record<string, string> = {};
  const userId = user?.id?.trim();
  const userEmail = user?.email?.trim();

  if (userId) {
    headers["x-user-id"] = userId;
  }
  if (userEmail) {
    headers["x-user-email"] = userEmail.toLowerCase();
  }

  return headers;
}

const api = axios.create({
  baseURL: API_BASE,
  timeout: API_TIMEOUT_MS,
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (axios.isAxiosError(err)) {
      if (err.code === "ECONNABORTED") {
        return Promise.reject(
          new Error(
            "Analysis timed out while the backend is warming up. Please retry in 30-60 seconds."
          )
        );
      }

      if (err.response?.status === 503) {
        return Promise.reject(
          new Error("Backend is waking up. Please wait a few seconds and retry.")
        );
      }
    }

    const message =
      err.response?.data?.detail || err.message || "An unexpected error occurred";
    return Promise.reject(new Error(message));
  }
);

export async function analyzeText(text: string): Promise<AnalysisResult> {
  const { data } = await api.post("/analyze-text", { text });
  return data;
}

export async function analyzeImage(formData: FormData): Promise<AnalysisResult> {
  const { data } = await api.post("/analyze-image", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

export async function analyzeContext(
  messages: ConversationMessage[]
): Promise<AnalysisResult> {
  const { data } = await api.post("/analyze-context", { messages });
  return data;
}

export async function generateFIR(
  analysisId: string,
  user?: ApiUserContext
): Promise<{ fir_id: string }> {
  const { data } = await api.post(
    "/generate-fir",
    { analysis_id: analysisId },
    { headers: buildUserHeaders(user) }
  );
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(FIR_HISTORY_UPDATED_EVENT));
  }
  return data;
}

export async function generateFIRPDF(payload: {
  fir_id: string;
  analysis_id: string;
  complainant_name: string;
  complainant_contact: string;
  complainant_address?: string;
  accused_name?: string;
  accused_details?: string;
  incident_date: string;
  incident_time?: string;
  incident_location?: string;
  additional_info?: string;
  legal_sections: string[];
  evidence_urls: string[];
}, user?: ApiUserContext): Promise<{ fir_id: string; pdf_url: string; status: string }> {
  const { data } = await api.post("/finalize-fir", payload, {
    headers: buildUserHeaders(user),
  });
  if (typeof window !== "undefined") {
    window.dispatchEvent(new CustomEvent(FIR_HISTORY_UPDATED_EVENT));
  }
  return data;
}

export function downloadFIR(firId: string, user?: ApiUserContext): void {
  const params = new URLSearchParams();
  const userId = user?.id?.trim();
  const userEmail = user?.email?.trim();
  if (userId) {
    params.set("user_id", userId);
  }
  if (userEmail) {
    params.set("user_email", userEmail.toLowerCase());
  }

  const query = params.toString();
  const url = query
    ? `${API_BASE}/download-fir/${firId}?${query}`
    : `${API_BASE}/download-fir/${firId}`;
  window.open(url, "_blank");
}

export async function getFIRHistory(
  limit: number = 50,
  skip: number = 0,
  user?: ApiUserContext
) {
  const { data } = await api.get("/fir-history", {
    params: { limit, skip },
    headers: buildUserHeaders(user),
  });
  return data;
}

export const firHistoryUpdatedEventName = FIR_HISTORY_UPDATED_EVENT;

export async function fetchAnalytics(user?: ApiUserContext) {
  const { data } = await api.get("/analytics", {
    headers: buildUserHeaders(user),
  });
  return data;
}

export async function wakeBackend(): Promise<void> {
  await api.get("/health", { timeout: 90000 });
}
