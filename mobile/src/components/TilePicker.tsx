import React from 'react';
import { View, Text, StyleSheet, Pressable, ScrollView } from 'react-native';
import { Colors, Fonts, Spacing, FontSize, Radius } from '../constants/theme';

// Tile data
type TileRow = { suit: string; suitKanji: string; tiles: string[] };

const TILE_ROWS: TileRow[] = [
  {
    suit: 'D',
    suitKanji: '萬',
    tiles: ['1D', '2D', '3D', '4D', '5D', '6D', '7D', '8D', '9D'],
  },
  {
    suit: 'B',
    suitKanji: '筒',
    tiles: ['1B', '2B', '3B', '4B', '5B', '6B', '7B', '8B', '9B'],
  },
  {
    suit: 'C',
    suitKanji: '索',
    tiles: ['1C', '2C', '3C', '4C', '5C', '6C', '7C', '8C', '9C'],
  },
];

const HONOUR_TILES = ['EW', 'SW', 'WW', 'NW', 'WD', 'GD', 'RD'];
const HONOUR_LABELS: Record<string, { rank: string; suit: string }> = {
  EW: { rank: '東', suit: '風' },
  SW: { rank: '南', suit: '風' },
  WW: { rank: '西', suit: '風' },
  NW: { rank: '北', suit: '風' },
  WD: { rank: '白', suit: '龍' },
  GD: { rank: '發', suit: '龍' },
  RD: { rank: '中', suit: '龍' },
};

// Red dora tiles (5th of each number suit)
const RED_DORA_TILES = new Set(['5D', '5B', '5C']);

interface Props {
  // counts[tileStr] = how many of that tile are selected (0-4)
  counts: Record<string, number>;
  redFlags: Record<string, boolean>; // tileStr → is red dora
  totalSelected: number;
  maxTiles?: number;
  onTilePress: (tile: string) => void;
  onToggleRed: (tile: string) => void;
}

export default function TilePicker({
  counts,
  redFlags,
  totalSelected,
  maxTiles = 14,
  onTilePress,
  onToggleRed,
}: Props) {
  const renderTile = (tileStr: string, rank: string, suit: string) => {
    const count = counts[tileStr] ?? 0;
    const isMaxed = count >= 4 || totalSelected >= maxTiles;
    const isRed = redFlags[tileStr] ?? false;
    const canRed = RED_DORA_TILES.has(tileStr) && count > 0;

    return (
      <View key={tileStr} style={styles.tileWrapper}>
        <Pressable
          onPress={() => onTilePress(tileStr)}
          disabled={isMaxed && count === 0}
          style={[
            styles.tile,
            count > 0 && styles.tileSelected,
            isMaxed && count === 0 && styles.tileDim,
            isRed && styles.tileRed,
          ]}
        >
          <Text style={styles.tileRank}>{rank}</Text>
          <Text style={styles.tileSuit}>{suit}</Text>
        </Pressable>
        {count > 0 && (
          <View style={styles.badge}>
            <Text style={styles.badgeText}>{count}</Text>
          </View>
        )}
        {canRed && (
          <Pressable onPress={() => onToggleRed(tileStr)} style={styles.redToggle}>
            <Text style={[styles.redToggleText, isRed && styles.redToggleActive]}>◆</Text>
          </Pressable>
        )}
      </View>
    );
  };

  return (
    <ScrollView showsVerticalScrollIndicator={false}>
      {TILE_ROWS.map(row => (
        <View key={row.suit} style={styles.row}>
          <Text style={styles.suitLabel}>{row.suitKanji}</Text>
          <View style={styles.tilesRow}>
            {row.tiles.map(t => {
              const rank = t.slice(0, -1);
              return renderTile(t, rank, row.suitKanji);
            })}
          </View>
        </View>
      ))}

      {/* Honours */}
      <View style={styles.row}>
        <Text style={styles.suitLabel}>字</Text>
        <View style={styles.tilesRow}>
          {HONOUR_TILES.map(t => {
            const lbl = HONOUR_LABELS[t];
            return renderTile(t, lbl.rank, lbl.suit);
          })}
        </View>
      </View>

      <View style={styles.totalRow}>
        <Text style={styles.totalText}>
          Selected: {totalSelected} / {maxTiles}
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: Spacing.sm,
    gap: Spacing.xs,
  },
  suitLabel: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.sm,
    color: Colors.accentGold,
    width: 16,
    marginTop: 8,
  },
  tilesRow: {
    flex: 1,
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.xs,
  },
  tileWrapper: {
    position: 'relative',
  },
  tile: {
    backgroundColor: Colors.tileBg,
    borderWidth: 1,
    borderColor: Colors.tileBorder,
    borderRadius: Radius.tile,
    width: 36,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 2,
  },
  tileSelected: {
    borderColor: Colors.accentGold,
    borderWidth: 2,
    shadowColor: Colors.accentGold,
    shadowOpacity: 0.4,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 0 },
    elevation: 4,
  },
  tileDim: {
    opacity: 0.35,
  },
  tileRed: {
    borderColor: Colors.accentRed,
    backgroundColor: '#FFF0EC',
  },
  tileRank: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.sm,
    color: '#2A1A00',
    lineHeight: 16,
  },
  tileSuit: {
    fontFamily: Fonts.serif,
    fontSize: 8,
    color: '#5A3A00',
    lineHeight: 12,
  },
  badge: {
    position: 'absolute',
    top: -4,
    right: -4,
    backgroundColor: Colors.accentGold,
    borderRadius: 8,
    width: 16,
    height: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  badgeText: {
    fontFamily: Fonts.sansBold,
    fontSize: 9,
    color: Colors.bgDeep,
  },
  redToggle: {
    position: 'absolute',
    bottom: -4,
    right: -4,
    backgroundColor: Colors.bgSurface,
    borderRadius: 8,
    width: 14,
    height: 14,
    alignItems: 'center',
    justifyContent: 'center',
  },
  redToggleText: {
    fontSize: 8,
    color: Colors.textSecondary,
  },
  redToggleActive: {
    color: Colors.accentRed,
  },
  totalRow: {
    alignItems: 'center',
    marginTop: Spacing.sm,
  },
  totalText: {
    fontFamily: Fonts.sans,
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
  },
});
