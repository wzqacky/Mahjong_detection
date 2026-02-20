import React from 'react';
import { View, Text, StyleSheet, ScrollView, Pressable } from 'react-native';
import { Colors, Fonts, Spacing, FontSize, Radius } from '../constants/theme';

const TILE_DISPLAY: Record<string, { rank: string; suit: string }> = {
  EW: { rank: '東', suit: '風' }, SW: { rank: '南', suit: '風' },
  WW: { rank: '西', suit: '風' }, NW: { rank: '北', suit: '風' },
  WD: { rank: '白', suit: '龍' }, GD: { rank: '發', suit: '龍' },
  RD: { rank: '中', suit: '龍' },
};

function tileDisplay(tile: string): { rank: string; suit: string } {
  if (TILE_DISPLAY[tile]) return TILE_DISPLAY[tile];
  const suitMap: Record<string, string> = { D: '萬', B: '筒', C: '索' };
  const rank = tile.slice(0, -1);
  const suit = suitMap[tile.slice(-1)] ?? '?';
  return { rank, suit };
}

interface Props {
  tiles: string[];                     // ordered list of all selected tiles
  winningTileIndex: number;            // index of the winning tile (-1 = none)
  isRedFlags: boolean[];               // parallel to tiles
  meldIndices: number[][];             // groups of indices that form melds
  onTilePress: (index: number) => void; // tap to remove tile
  onSetWinTile: (index: number) => void; // long-press to designate win tile
}

export default function SelectedHand({
  tiles,
  winningTileIndex,
  isRedFlags,
  meldIndices,
  onTilePress,
  onSetWinTile,
}: Props) {
  const meldSet = new Set(meldIndices.flat());

  const renderSlot = (tile: string | null, index: number) => {
    const isWin = index === winningTileIndex;
    const isMeld = meldSet.has(index);
    const isRed = isRedFlags[index] ?? false;

    if (!tile) {
      return (
        <View key={`empty-${index}`} style={[styles.slot, styles.emptySlot]}>
          <Text style={styles.emptyText}>·</Text>
        </View>
      );
    }

    const { rank, suit } = tileDisplay(tile);

    return (
      <Pressable
        key={`tile-${index}-${tile}`}
        onPress={() => onTilePress(index)}
        onLongPress={() => onSetWinTile(index)}
        style={[
          styles.slot,
          styles.filledSlot,
          isWin && styles.winSlot,
          isMeld && styles.meldSlot,
          isRed && styles.redSlot,
        ]}
      >
        <Text style={[styles.tileRank, isWin && styles.winText]}>{rank}</Text>
        <Text style={[styles.tileSuit, isWin && styles.winText]}>{suit}</Text>
        {isWin && <Text style={styles.winLabel}>WIN</Text>}
        {isRed && <Text style={styles.redDot}>◆</Text>}
      </Pressable>
    );
  };

  // Show 14 slots total
  const slots = Array.from({ length: 14 }, (_, i) => tiles[i] ?? null);

  return (
    <View style={styles.container}>
      <Text style={styles.header}>
        手牌  ({tiles.length}/13 + WIN)
      </Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.row}>
        <View style={styles.tileRow}>
          {slots.map((tile, i) => renderSlot(tile, i))}
        </View>
      </ScrollView>
      <Text style={styles.hint}>Tap to remove · Long-press to set WIN tile</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginBottom: Spacing.sm,
  },
  header: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
    letterSpacing: 1,
    marginBottom: Spacing.xs,
  },
  row: {
    flexDirection: 'row',
  },
  tileRow: {
    flexDirection: 'row',
    gap: 4,
    paddingVertical: 4,
  },
  slot: {
    width: 34,
    height: 44,
    borderRadius: Radius.tile,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
  },
  emptySlot: {
    borderColor: Colors.borderGlow,
    borderStyle: 'dashed',
    backgroundColor: 'transparent',
  },
  filledSlot: {
    backgroundColor: Colors.tileBg,
    borderColor: Colors.tileBorder,
  },
  winSlot: {
    borderColor: Colors.accentGold,
    borderWidth: 2,
    backgroundColor: '#FFF8E5',
    shadowColor: Colors.accentGold,
    shadowOpacity: 0.5,
    shadowRadius: 6,
    shadowOffset: { width: 0, height: 0 },
    elevation: 6,
  },
  meldSlot: {
    borderColor: Colors.accentTeal,
    borderWidth: 2,
  },
  redSlot: {
    backgroundColor: '#FFF0EC',
  },
  emptyText: {
    color: Colors.textSecondary,
    fontSize: FontSize.lg,
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
    lineHeight: 10,
  },
  winText: {
    color: '#7A4E00',
  },
  winLabel: {
    fontFamily: Fonts.sansBold,
    fontSize: 7,
    color: Colors.accentGold,
    letterSpacing: 0.5,
    marginTop: 1,
  },
  redDot: {
    fontSize: 7,
    color: Colors.accentRed,
    position: 'absolute',
    bottom: 2,
    right: 2,
  },
  hint: {
    fontFamily: Fonts.sans,
    fontSize: 10,
    color: Colors.textSecondary,
    marginTop: 4,
    fontStyle: 'italic',
  },
});
