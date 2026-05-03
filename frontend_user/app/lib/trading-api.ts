/**
 * Trading Test API Client
 */

export interface ApiQuestion {
  id: string;
  type: 'single' | 'qa';
  topic?: string;
  difficulty: number;
  dimension?: string | null;
  stem: string;
  options: { key: string; text: string }[];
}

export interface ApiProgress {
  current: number;
  total: number;
  pct: number;
}

export interface ApiResult {
  persona: string;
  persona_description: string;
  route_action: string;
  trait_tags: string[];
  dimension_scores: Record<string, { score: number; normalized: number }>;
}

export interface ApiResponse {
  user_id: string;
  status: 'question' | 'finished';
  progress?: ApiProgress;
  question?: ApiQuestion;
  result?: ApiResult;
  message?: string;
  retry_count?: number;
}

const API_BASE = 'http://47.120.54.24:8866/api/v1';

export async function playTradingTest(userId: string, answer: string[] = []): Promise<ApiResponse> {
  const response = await fetch(`${API_BASE}/play`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      user_id: userId,
      answer: answer,
    }),
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}
