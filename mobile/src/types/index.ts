// ─── Player & Icons ────────────────────────────────────────────────────────────
export interface PlayerIcon {
  id: string;
  emoji: string;
  label: string;
  category: string;
}

export interface Player {
  id: string;
  name: string;
  iconId: string;
  seatWind: 'East' | 'South' | 'West' | 'North';
  score: number;
  isDealer: boolean;
}

// ─── Melds ──────────────────────────────────────────────────────────────────────
export interface MeldEntry {
  tiles: string[];   // tile strings e.g. ["1B","2B","3B"]
  isOpen: boolean;
}

// ─── Yaku ───────────────────────────────────────────────────────────────────────
export interface YakuItem {
  code: string;
  name_zh: string;
  name_en: string;
  han: number;
  is_yakuman: boolean;
}

// ─── Round ──────────────────────────────────────────────────────────────────────
export interface Round {
  roundNumber: number;
  roundWind: 'East' | 'South';
  honba: number;
  riichiBets: number;
  winnerId: string | null;   // null = draw
  loserId: string | null;    // null = tsumo or draw
  isTsumo: boolean;
  isDraw: boolean;
  tenpaiPlayerIds: string[];
  yakuList: YakuItem[];
  han: number;
  fu: number;
  payments: Record<string, number>;  // playerId → signed delta
}

// ─── API request / response ──────────────────────────────────────────────────────
// Mirrors server/schemas.py exactly
export interface MeldInput {
  tiles: string[];
  is_open: boolean;
}

export interface GameContextInput {
  round_wind: 'east' | 'south' | 'west' | 'north';
  round_number: number;
  dealer_position: number;   // 0-indexed seat of dealer
  player_position: number;   // number of players (3 or 4, mapped as 2 or 3)
  honba: number;
  riichi_sticks: number;
}

export interface ScoreRequest {
  tiles: string[];
  red_tile_flags: boolean[];
  winning_tile: string;
  winning_tile_is_red: boolean;
  melds: MeldInput[];
  is_riichi: boolean;
  is_tsumo: boolean;
  is_ippatsu: boolean;
  is_first_turn: boolean;
  is_last_tile: boolean;
  is_rinshan: boolean;
  is_chankan: boolean;
  dora_indicators: string[];
  game_context: GameContextInput;
}

export interface ScoreResponse {
  is_winning: boolean;
  yaku: YakuItem[];
  han: number;
  fu: number;
  base_points: number;
  total_points: number;
  dealer_payment: number;
  non_dealer_payment: number;
  honba_bonus: number;
  riichi_sticks_bonus: number;
  is_yakuman: boolean;
  error?: string | null;
}

// ─── Hand level label ───────────────────────────────────────────────────────────
export type HandLevel =
  | 'mangan'    // 満貫  5han / 4han70fu / 3han110fu
  | 'haneman'   // 跳満  6-7han
  | 'baiman'    // 倍満  8-10han
  | 'sanbaiman' // 三倍満 11-12han
  | 'yakuman'   // 役満  13+han or true yakuman
  | 'normal';

export function getHandLevel(han: number, isYakuman: boolean): HandLevel {
  if (isYakuman) return 'yakuman';
  if (han >= 13) return 'yakuman';
  if (han >= 11) return 'sanbaiman';
  if (han >= 8)  return 'baiman';
  if (han >= 6)  return 'haneman';
  if (han >= 5)  return 'mangan';
  return 'normal';
}

export const HAND_LEVEL_LABELS: Record<HandLevel, { zh: string; en: string }> = {
  mangan:    { zh: '満貫',   en: 'MANGAN' },
  haneman:   { zh: '跳満',   en: 'HANEMAN' },
  baiman:    { zh: '倍満',   en: 'BAIMAN' },
  sanbaiman: { zh: '三倍満', en: 'SANBAIMAN' },
  yakuman:   { zh: '役満',   en: 'YAKUMAN' },
  normal:    { zh: '',      en: '' },
};

// ─── Navigation param lists ─────────────────────────────────────────────────────
export type RootStackParamList = {
  Setup: undefined;
  Game: undefined;
  Result: undefined;
};
