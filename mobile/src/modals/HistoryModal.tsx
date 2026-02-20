import React from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  FlatList,
  Pressable,
} from 'react-native';
import { Colors, Fonts, Spacing, FontSize, Radius } from '../constants/theme';
import { Round, YakuItem } from '../types';
import { useGameStore } from '../store/gameStore';

interface Props {
  visible: boolean;
  onClose: () => void;
}

function roundLabel(round: Round): string {
  const wind = round.roundWind === 'East' ? '東' : '南';
  return `${wind}${round.roundNumber}局`;
}

function RoundRow({ round, players }: { round: Round; players: { id: string; name: string }[] }) {
  const getName = (id: string | null) =>
    id ? (players.find(p => p.id === id)?.name ?? '?') : '—';

  const label = roundLabel(round);
  const honbaStr = round.honba > 0 ? ` ${round.honba}本場` : '';

  if (round.isDraw) {
    const tenpaiNames = round.tenpaiPlayerIds.map(getName).join(', ');
    return (
      <View style={styles.row}>
        <View style={styles.rowHeader}>
          <Text style={styles.rowLabel}>{label}{honbaStr}</Text>
          <Text style={styles.drawBadge}>流局 DRAW</Text>
        </View>
        {tenpaiNames ? (
          <Text style={styles.rowSub}>Tenpai: {tenpaiNames}</Text>
        ) : (
          <Text style={styles.rowSub}>All noten</Text>
        )}
        {Object.entries(round.payments)
          .filter(([, v]) => v !== 0)
          .map(([id, delta]) => (
            <Text
              key={id}
              style={[styles.delta, { color: delta > 0 ? Colors.accentTeal : Colors.accentRedLight }]}
            >
              {getName(id)}: {delta > 0 ? '+' : ''}{delta.toLocaleString()}
            </Text>
          ))}
      </View>
    );
  }

  const winType = round.isTsumo ? 'TSUMO' : 'RON';
  const winnerName = getName(round.winnerId);
  const yakuSummary = round.yakuList.slice(0, 3).map(y => y.name_zh).join(' + ');

  return (
    <View style={styles.row}>
      <View style={styles.rowHeader}>
        <Text style={styles.rowLabel}>{label}{honbaStr}</Text>
        <Text style={[styles.winBadge, round.isTsumo ? styles.tsumo : styles.ron]}>
          {winType}
        </Text>
      </View>
      <Text style={styles.rowSub}>
        {winnerName}  {round.han}翻{round.fu}符
      </Text>
      {yakuSummary ? <Text style={styles.yakuSummary}>{yakuSummary}</Text> : null}
      {Object.entries(round.payments)
        .filter(([, v]) => v !== 0)
        .map(([id, delta]) => (
          <Text
            key={id}
            style={[styles.delta, { color: delta > 0 ? Colors.accentTeal : Colors.accentRedLight }]}
          >
            {getName(id)}: {delta > 0 ? '+' : ''}{delta.toLocaleString()}
          </Text>
        ))}
    </View>
  );
}

export default function HistoryModal({ visible, onClose }: Props) {
  const rounds = useGameStore(s => s.rounds);
  const players = useGameStore(s => s.players);

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.sheet}>
          <View style={styles.header}>
            <Pressable onPress={onClose}>
              <Text style={styles.backText}>← 戻る</Text>
            </Pressable>
            <Text style={styles.title}>対局履歴 LOG</Text>
          </View>
          <View style={styles.divider} />

          {rounds.length === 0 ? (
            <View style={styles.empty}>
              <Text style={styles.emptyText}>まだラウンドがありません</Text>
              <Text style={styles.emptySubText}>No rounds yet</Text>
            </View>
          ) : (
            <FlatList
              data={rounds}
              keyExtractor={(_, i) => String(i)}
              renderItem={({ item }) => (
                <RoundRow round={item} players={players} />
              )}
              contentContainerStyle={styles.list}
              showsVerticalScrollIndicator={false}
            />
          )}
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
  },
  sheet: {
    flex: 1,
    backgroundColor: Colors.bgDeep,
    marginTop: 60,
    borderTopLeftRadius: Radius.modal,
    borderTopRightRadius: Radius.modal,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: Spacing.lg,
    paddingVertical: Spacing.md,
    gap: Spacing.md,
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
  },
  list: {
    padding: Spacing.lg,
    gap: Spacing.sm,
  },
  row: {
    backgroundColor: Colors.bgSurface,
    borderRadius: Radius.card,
    borderWidth: 1,
    borderColor: Colors.borderGlow,
    padding: Spacing.md,
    gap: Spacing.xs,
  },
  rowHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  rowLabel: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.md,
    color: Colors.accentGold,
  },
  winBadge: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    letterSpacing: 1,
    paddingHorizontal: Spacing.xs,
    paddingVertical: 2,
    borderRadius: Radius.badge,
    overflow: 'hidden',
  },
  tsumo: {
    backgroundColor: 'rgba(45,212,191,0.2)',
    color: Colors.accentTeal,
  },
  ron: {
    backgroundColor: 'rgba(179,48,64,0.2)',
    color: Colors.accentRedLight,
  },
  drawBadge: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
    letterSpacing: 1,
  },
  rowSub: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.sm,
    color: Colors.textPrimary,
  },
  yakuSummary: {
    fontFamily: Fonts.sans,
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
  },
  delta: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
  },
  empty: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyText: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.lg,
    color: Colors.textSecondary,
  },
  emptySubText: {
    fontFamily: Fonts.sans,
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
    marginTop: Spacing.xs,
  },
});
