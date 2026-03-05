import { BASE_URL } from '../config';
import { ScoreRequest, ScoreResponse } from '../types';

export async function calculateScore(req: ScoreRequest): Promise<ScoreResponse> {
  try {
    const res = await fetch(`${BASE_URL}/api/score`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    });
    if (!res.ok) {
      const body = await res.json().catch(() => null);
      const detail = body?.detail;
      throw new Error(typeof detail === 'string' ? detail : `HTTP ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Network error';
    return {
      is_winning: false,
      yaku: [],
      han: 0,
      fu: 0,
      base_points: 0,
      total_points: 0,
      dealer_payment: 0,
      non_dealer_payment: 0,
      honba_bonus: 0,
      riichi_sticks_bonus: 0,
      is_yakuman: false,
      error: message,
    };
  }
}

export async function healthCheck(): Promise<boolean> {
  try {
    const res = await fetch(`${BASE_URL}/api/health`, { signal: AbortSignal.timeout(5000) });
    return res.ok;
  } catch {
    return false;
  }
}
