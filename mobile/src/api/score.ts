import axios, { AxiosError } from 'axios';
import { BASE_URL } from '../config';
import { ScoreRequest, ScoreResponse } from '../types';

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 15_000,
  headers: { 'Content-Type': 'application/json' },
});

export async function calculateScore(req: ScoreRequest): Promise<ScoreResponse> {
  try {
    const { data } = await client.post<ScoreResponse>('/api/score', req);
    return data;
  } catch (err) {
    const axiosErr = err as AxiosError<{ detail?: unknown }>;
    // FastAPI validation error (422) or network error
    const detail = axiosErr.response?.data?.detail;
    const message =
      typeof detail === 'string'
        ? detail
        : axiosErr.message ?? 'Network error';
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
    await client.get('/api/health', { timeout: 5_000 });
    return true;
  } catch {
    return false;
  }
}
