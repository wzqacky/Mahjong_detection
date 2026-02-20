import React, { useRef, useEffect } from 'react';
import { View, Text, StyleSheet, Pressable, Animated } from 'react-native';
import { Colors, Fonts, Spacing, FontSize, Radius } from '../constants/theme';
import { Player } from '../types';
import PlayerIcon from './PlayerIcon';
import WindBadge from './WindBadge';
import RiichiBadge from './RiichiBadge';

interface Props {
  player: Player;
  delta: number;
  hasRiichi: boolean;
  onLongPress?: () => void;
}

export default function PlayerCard({ player, delta, hasRiichi, onLongPress }: Props) {
  const deltaAnim = useRef(new Animated.Value(0)).current;
  const prevDelta = useRef(delta);

  useEffect(() => {
    if (prevDelta.current !== delta) {
      deltaAnim.setValue(delta > prevDelta.current ? 20 : -20);
      Animated.spring(deltaAnim, {
        toValue: 0,
        tension: 60,
        friction: 8,
        useNativeDriver: true,
      }).start();
      prevDelta.current = delta;
    }
  }, [delta]);

  const deltaColor =
    delta > 0 ? Colors.accentTeal : delta < 0 ? Colors.accentRedLight : Colors.textSecondary;

  const deltaSign = delta > 0 ? '+' : '';

  return (
    <Pressable onLongPress={onLongPress} style={styles.card} delayLongPress={400}>
      {/* Header row */}
      <View style={styles.header}>
        <PlayerIcon iconId={player.iconId} size={40} />
        <View style={styles.headerText}>
          <WindBadge wind={player.seatWind} isDealer={player.isDealer} size="sm" />
          <Text style={styles.name} numberOfLines={1}>
            {player.name}
          </Text>
        </View>
      </View>

      {/* Score */}
      <Text style={styles.score}>{player.score.toLocaleString()}</Text>

      {/* Delta */}
      <Animated.Text
        style={[styles.delta, { color: deltaColor, transform: [{ translateY: deltaAnim }] }]}
      >
        {delta !== 0 ? `${deltaSign}${delta.toLocaleString()}` : '±0'}
      </Animated.Text>

      {/* Riichi badge */}
      <RiichiBadge visible={hasRiichi} />
    </Pressable>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: Colors.bgSurface,
    borderRadius: Radius.card,
    borderWidth: 1,
    borderColor: Colors.borderGlow,
    padding: Spacing.md,
    flex: 1,
    minHeight: 140,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    marginBottom: Spacing.sm,
  },
  headerText: {
    flex: 1,
    gap: 4,
  },
  name: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.sm,
    color: Colors.textPrimary,
  },
  score: {
    fontFamily: Fonts.score,
    fontSize: FontSize.score,
    color: Colors.accentGoldLight,
    letterSpacing: 1,
    marginBottom: 2,
  },
  delta: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.sm,
    marginBottom: Spacing.xs,
  },
});
