import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  Switch,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { Colors, Fonts, Spacing, FontSize, Radius } from '../constants/theme';
import { MeldEntry, ScoreRequest, ScoreResponse } from '../types';
import { useGameStore, selectRoundWindLower } from '../store/gameStore';
import { calculateScore } from '../api/score';
import TilePicker from '../components/TilePicker';
import SelectedHand from '../components/SelectedHand';
import MeldBuilder from '../components/MeldBuilder';

interface Props {
  winnerId: string;
  loserId: string | null;
  isTsumo: boolean;
  onBack: () => void;
  onResult: (response: ScoreResponse, melds: MeldEntry[]) => void;
}

export default function HandInputScreen({
  winnerId,
  loserId,
  isTsumo,
  onBack,
  onResult,
}: Props) {
  // All selected tiles in order (tap to add)
  const [tiles, setTiles] = useState<string[]>([]);
  // Count of each tile in `tiles`
  const [counts, setCounts] = useState<Record<string, number>>({});
  // Red dora flags for each position in tiles[] (by tile string, last occurrence)
  const [redFlags, setRedFlags] = useState<Record<string, boolean>>({});
  // Index in tiles[] of the winning tile (-1 = auto = last tile)
  const [winTileIndex, setWinTileIndex] = useState(-1);
  // Open / closed melds
  const [melds, setMelds] = useState<MeldEntry[]>([]);
  // Riichi
  const [isRiichi, setIsRiichi] = useState(false);
  // Dora indicator input
  const [doraIndicators, setDoraIndicators] = useState<string[]>([]);
  const [showDoraPicker, setShowDoraPicker] = useState(false);
  const [doraCounts, setDoraCounts] = useState<Record<string, number>>({});
  // Loading
  const [loading, setLoading] = useState(false);

  const players = useGameStore(s => s.players);
  const riichiBets = useGameStore(s => s.riichiBets);
  const honba = useGameStore(s => s.honba);
  const currentRoundNumber = useGameStore(s => s.currentRoundNumber);
  const roundWind = useGameStore(selectRoundWindLower);
  const dealerIndex = useGameStore(s => s.dealerIndex);

  const winner = players.find(p => p.id === winnerId)!;
  const winnerIndex = players.findIndex(p => p.id === winnerId);
  const dealerPos = dealerIndex; // 0-indexed, 0=East dealer

  const totalSelected = tiles.length;
  const effectiveWinIndex = winTileIndex >= 0 ? winTileIndex : tiles.length - 1;

  const handleTilePress = (tile: string) => {
    if (counts[tile] >= 4 || totalSelected >= 14) return;
    const newTiles = [...tiles, tile];
    const newCounts = { ...counts, [tile]: (counts[tile] ?? 0) + 1 };
    setTiles(newTiles);
    setCounts(newCounts);
    // Auto-set win tile to last added
    setWinTileIndex(newTiles.length - 1);
  };

  const handleSlotPress = (index: number) => {
    // Remove tile at index
    const tile = tiles[index];
    const newTiles = tiles.filter((_, i) => i !== index);
    const newCount = (counts[tile] ?? 1) - 1;
    const newCounts = { ...counts, [tile]: Math.max(0, newCount) };
    setTiles(newTiles);
    setCounts(newCounts);
    // Adjust win tile index
    if (winTileIndex >= newTiles.length) {
      setWinTileIndex(newTiles.length - 1);
    } else if (winTileIndex === index) {
      setWinTileIndex(newTiles.length - 1);
    }
    // Remove from any meld that contains this index
    setMelds(prev =>
      prev.filter(m => !m.tiles.includes(tile)).concat(
        prev.filter(m => m.tiles.includes(tile)) // keep meld but user can remove manually
      ).slice(0, prev.length) // no-op, just for clarity
    );
  };

  const handleToggleRed = (tile: string) => {
    setRedFlags(prev => ({ ...prev, [tile]: !prev[tile] }));
  };

  const handleAddMeld = (meld: MeldEntry) => {
    setMelds(prev => [...prev, meld]);
  };

  const handleRemoveMeld = (index: number) => {
    setMelds(prev => prev.filter((_, i) => i !== index));
  };

  const handleCalculate = async () => {
    if (tiles.length < 2) {
      Alert.alert('Error', 'Please select at least 2 tiles.');
      return;
    }

    const winTile = tiles[effectiveWinIndex];
    const meldTileStrings = melds.flatMap(m => [...m.tiles]);

    // Concealed tiles = all tiles minus the winning tile minus meld tiles
    const handTiles: string[] = [];
    const handRedFlags: boolean[] = [];
    // We need to remove meld tiles from tiles array
    // Build a working copy of meld tile counts
    const meldTileCounts: Record<string, number> = {};
    meldTileStrings.forEach(t => {
      meldTileCounts[t] = (meldTileCounts[t] ?? 0) + 1;
    });

    tiles.forEach((tile, i) => {
      if (i === effectiveWinIndex) return; // skip winning tile
      // Skip meld tiles (deduct from meld counts)
      if (meldTileCounts[tile] && meldTileCounts[tile] > 0) {
        meldTileCounts[tile]--;
        return;
      }
      handTiles.push(tile);
      handRedFlags.push(redFlags[tile] ?? false);
    });

    const meldInputs = melds.map(m => ({ tiles: m.tiles, is_open: m.isOpen }));

    // Dora indicators from doraCounts
    const doraInds: string[] = [];
    Object.entries(doraCounts).forEach(([tile, count]) => {
      for (let i = 0; i < count; i++) doraInds.push(tile);
    });

    const req: ScoreRequest = {
      tiles: handTiles,
      red_tile_flags: handRedFlags,
      winning_tile: winTile,
      winning_tile_is_red: redFlags[winTile] ?? false,
      melds: meldInputs,
      is_riichi: isRiichi,
      is_tsumo: isTsumo,
      is_ippatsu: false,
      is_first_turn: false,
      is_last_tile: false,
      is_rinshan: false,
      is_chankan: false,
      dora_indicators: doraInds,
      game_context: {
        round_wind: roundWind,
        round_number: currentRoundNumber,
        dealer_position: dealerPos,
        // Server constraint: ge=2, le=3 (3-player game=2, 4-player game=3)
        player_position: players.length - 1,
        honba,
        riichi_sticks: riichiBets,
      },
    };

    setLoading(true);
    try {
      const response = await calculateScore(req);
      onResult(response, melds);
    } finally {
      setLoading(false);
    }
  };

  const meldIndexGroups: number[][] = [];

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.headerRow}>
        <Pressable onPress={onBack} style={styles.backBtn}>
          <Text style={styles.backText}>← 戻る</Text>
        </Pressable>
        <Text style={styles.title}>手牌入力</Text>
      </View>

      <View style={styles.divider} />

      <ScrollView style={styles.scroll} keyboardShouldPersistTaps="handled">
        {/* Selected hand display */}
        <View style={styles.section}>
          <SelectedHand
            tiles={tiles}
            winningTileIndex={effectiveWinIndex}
            isRedFlags={tiles.map(t => redFlags[t] ?? false)}
            meldIndices={meldIndexGroups}
            onTilePress={handleSlotPress}
            onSetWinTile={setWinTileIndex}
          />
        </View>

        <View style={styles.divider} />

        {/* Tile picker */}
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>── TILE PICKER ──</Text>
          <TilePicker
            counts={counts}
            redFlags={redFlags}
            totalSelected={totalSelected}
            maxTiles={14}
            onTilePress={handleTilePress}
            onToggleRed={handleToggleRed}
          />
        </View>

        <View style={styles.divider} />

        {/* Options */}
        <View style={styles.section}>
          <Text style={styles.sectionLabel}>── OPTIONS ──</Text>
          <View style={styles.optionRow}>
            <Text style={styles.optionLabel}>立直 Riichi</Text>
            <Switch
              value={isRiichi}
              onValueChange={setIsRiichi}
              trackColor={{ true: Colors.accentTeal }}
              thumbColor={Colors.textPrimary}
            />
          </View>
          <Pressable
            onPress={() => setShowDoraPicker(!showDoraPicker)}
            style={styles.optionRow}
          >
            <Text style={styles.optionLabel}>
              赤/ドラ Dora Indicators ({Object.values(doraCounts).reduce((a,b)=>a+b,0)})
            </Text>
            <Text style={styles.chevron}>{showDoraPicker ? '▲' : '▼'}</Text>
          </Pressable>
          {showDoraPicker && (
            <View style={styles.doraContainer}>
              <Text style={styles.doraHint}>Select dora indicator tiles:</Text>
              <TilePicker
                counts={doraCounts}
                redFlags={{}}
                totalSelected={Object.values(doraCounts).reduce((a,b)=>a+b,0)}
                maxTiles={5}
                onTilePress={tile => {
                  const cur = doraCounts[tile] ?? 0;
                  setDoraCounts(prev => ({ ...prev, [tile]: Math.min(cur + 1, 4) }));
                }}
                onToggleRed={() => {}}
              />
            </View>
          )}
        </View>

        <View style={styles.divider} />

        {/* Melds */}
        <View style={styles.section}>
          <MeldBuilder
            melds={melds}
            onAdd={handleAddMeld}
            onRemove={handleRemoveMeld}
          />
        </View>

        <View style={{ height: 80 }} />
      </ScrollView>

      {/* Calculate button */}
      <View style={styles.footer}>
        <Pressable
          onPress={handleCalculate}
          disabled={loading || tiles.length < 2}
          style={[styles.calcBtn, (loading || tiles.length < 2) && styles.calcBtnDisabled]}
        >
          {loading ? (
            <ActivityIndicator color={Colors.bgDeep} />
          ) : (
            <>
              <Text style={styles.calcJP}>確認</Text>
              <Text style={styles.calcEN}>CALCULATE</Text>
            </>
          )}
        </Pressable>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.bgSurface,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
  },
  backBtn: {
    marginRight: Spacing.md,
  },
  backText: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.sm,
    color: Colors.accentGold,
  },
  title: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.lg,
    color: Colors.textPrimary,
  },
  divider: {
    height: 1,
    backgroundColor: Colors.borderGlow,
    marginHorizontal: Spacing.lg,
    marginVertical: Spacing.sm,
  },
  scroll: {
    flex: 1,
  },
  section: {
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.sm,
  },
  sectionLabel: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
    letterSpacing: 2,
    marginBottom: Spacing.sm,
  },
  optionRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: Spacing.sm,
  },
  optionLabel: {
    fontFamily: Fonts.sans,
    fontSize: FontSize.md,
    color: Colors.textPrimary,
  },
  chevron: {
    color: Colors.accentGold,
    fontSize: FontSize.sm,
  },
  doraContainer: {
    marginTop: Spacing.sm,
  },
  doraHint: {
    fontFamily: Fonts.sans,
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
    marginBottom: Spacing.xs,
  },
  footer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    padding: Spacing.lg,
    backgroundColor: Colors.bgSurface,
    borderTopWidth: 1,
    borderTopColor: Colors.borderGlow,
  },
  calcBtn: {
    backgroundColor: Colors.accentGold,
    borderRadius: Radius.button,
    paddingVertical: Spacing.md,
    alignItems: 'center',
  },
  calcBtnDisabled: {
    opacity: 0.4,
  },
  calcJP: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.lg,
    color: Colors.bgDeep,
  },
  calcEN: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.bgDeep,
    letterSpacing: 3,
  },
});
