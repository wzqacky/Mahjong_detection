import { PlayerIcon } from '../types';

export const PLAYER_ICONS: PlayerIcon[] = [
  // Mahjong Tiles
  { id: 'tile-chun',  emoji: '中', label: 'Chun (Red Dragon)',   category: 'Mahjong Tiles' },
  { id: 'tile-hatsu', emoji: '發', label: 'Hatsu (Green Dragon)', category: 'Mahjong Tiles' },
  { id: 'tile-haku',  emoji: '白', label: 'Haku (White Dragon)', category: 'Mahjong Tiles' },
  { id: 'tile-east',  emoji: '東', label: 'Higashi (East Wind)', category: 'Mahjong Tiles' },
  // Japanese Mythology
  { id: 'myth-kitsune', emoji: '🦊', label: 'Kitsune (Fox)',    category: 'Mythology' },
  { id: 'myth-dragon',  emoji: '🐉', label: 'Ryū (Dragon)',     category: 'Mythology' },
  { id: 'myth-tengu',   emoji: '👺', label: 'Tengu',            category: 'Mythology' },
  { id: 'myth-oni',     emoji: '😈', label: 'Oni',              category: 'Mythology' },
  // Nature & Tradition
  { id: 'nature-sakura', emoji: '🌸', label: 'Sakura',  category: 'Nature' },
  { id: 'nature-crane',  emoji: '🦢', label: 'Tsuru',   category: 'Nature' },
  { id: 'nature-koi',    emoji: '🐟', label: 'Koi',     category: 'Nature' },
  { id: 'nature-moon',   emoji: '🌙', label: 'Tsuki',   category: 'Nature' },
  // Anime Archetypes
  { id: 'arch-pro',   emoji: '🎴', label: 'The Pro',        category: 'Archetype' },
  { id: 'arch-lucky', emoji: '⭐', label: 'The Lucky One',  category: 'Archetype' },
  { id: 'arch-bold',  emoji: '⚡', label: 'The Aggressive', category: 'Archetype' },
  { id: 'arch-calm',  emoji: '🌊', label: 'The Defensive',  category: 'Archetype' },
];

// Default icons assigned to players 1–4 before they choose
export const DEFAULT_ICON_IDS = [
  'tile-chun',
  'tile-hatsu',
  'tile-haku',
  'tile-east',
];

export const ICON_CATEGORIES = [
  { key: 'Mahjong Tiles', labelJP: '麻雀牌', labelEN: 'MAHJONG TILES' },
  { key: 'Mythology',     labelJP: '神話',   labelEN: 'MYTHOLOGY' },
  { key: 'Nature',        labelJP: '自然',   labelEN: 'NATURE' },
  { key: 'Archetype',     labelJP: '個性',   labelEN: 'ARCHETYPE' },
];

export function getIconById(id: string): PlayerIcon {
  return PLAYER_ICONS.find(ic => ic.id === id) ?? PLAYER_ICONS[0];
}
