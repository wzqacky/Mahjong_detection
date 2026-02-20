import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Pressable,
  ScrollView,
  Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Colors, Fonts, Spacing, FontSize, Radius, GoldGradient } from '../constants/theme';
import { ScoreResponse, getHandLevel, HAND_LEVEL_LABELS } from '../types';
import { useGameStore } from '../store/gameStore';
import YakuList from '../components/YakuList';

interface Props {
  response: ScoreResponse;
  winnerId: string;
  loserId: string | null;
  isTsumo: boolean;
  onNext: (payments: Record<string, number>) => void;
  onClose: () => void;
}

function useCountUp(target: number, duration = 1000) {
  const [value, setValue] = useState(0);
  useEffect(() => {
    let start: number | null = null;
    let rafId: number;
    const step = (ts: number) => {
      if (!start) start = ts;
      const progress = Math.min((ts - start) / duration, 1);
      setValue(Math.floor(progress * target));
      if (progress < 1) rafId = requestAnimationFrame(step);
    };
    rafId = requestAnimationFrame(step);
    return () => cancelAnimationFrame(rafId);
  }, [target]);
  return value;
}

export default function ScoreModal({
  response,
  winnerId,
  loserId,
  isTsumo,
  onNext,
  onClose,
}: Props) {
  const players = useGameStore(s => s.players);
  const riichiBets = useGameStore(s => s.riichiBets);

  const winner = players.find(p => p.id === winnerId)!;
  const scaleAnim = useRef(new Animated.Value(0.8)).current;
  const opacityAnim = useRef(new Animated.Value(0)).current;
  const countedPoints = useCountUp(response.total_points);

  useEffect(() => {
    Animated.parallel([
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 60,
        friction: 8,
        useNativeDriver: true,
      }),
      Animated.timing(opacityAnim, {
        toValue: 1,
        duration: 300,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  // Compute payments
  const payments: Record<string, number> = {};
  players.forEach(p => { payments[p.id] = 0; });

  if (response.is_winning) {
    if (isTsumo) {
      const winnerIsDealer = winner.isDealer;
      players.forEach(p => {
        if (p.id === winnerId) return;
        const pays = (winnerIsDealer || p.isDealer) ? response.dealer_payment : response.non_dealer_payment;
        payments[p.id] = -pays;
      });
      const totalIn = players
        .filter(p => p.id !== winnerId)
        .reduce((sum, p) => sum + Math.abs(payments[p.id]), 0);
      payments[winnerId] = totalIn;
    } else if (loserId) {
      payments[loserId] = -response.total_points;
      payments[winnerId] = response.total_points;
    }
  }

  const handLevel = getHandLevel(response.han, response.is_yakuman);
  const levelLabel = HAND_LEVEL_LABELS[handLevel];
  const hasLevelLabel = handLevel !== 'normal';

  if (!response.is_winning) {
    return (
      <View style={styles.overlay}>
        <View style={styles.sheet}>
          <View style={styles.handle} />
          <Text style={styles.errorTitle}>Not a Winning Hand</Text>
          <Text style={styles.errorMsg}>{response.error ?? 'Invalid hand'}</Text>
          <Pressable onPress={onClose} style={styles.closeBtn}>
            <Text style={styles.closeBtnText}>戻る BACK</Text>
          </Pressable>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.overlay}>
      <Animated.View
        style={[styles.sheet, { opacity: opacityAnim, transform: [{ scale: scaleAnim }] }]}
      >
        <View style={styles.handle} />

        <ScrollView showsVerticalScrollIndicator={false}>
          {/* Winner announcement */}
          <View style={styles.announcementBlock}>
            <Text style={styles.stars}>✦ 和了 ✦</Text>
            <Text style={styles.winnerName}>{winner.name}</Text>
            <Text style={styles.winsLabel}>WINS</Text>
          </View>

          <View style={styles.divider} />

          {/* Yaku list */}
          <View style={styles.section}>
            <Text style={styles.sectionHeader}>役 YAKU</Text>
            <View style={styles.yakuContainer}>
              <YakuList yaku={response.yaku} />
              {response.error && (
                <Text style={styles.yakuError}>{response.error}</Text>
              )}
            </View>
          </View>

          {/* Han / Fu */}
          <View style={styles.hanFuRow}>
            <View style={styles.hanFuItem}>
              <Text style={styles.hanFuLabel}>符 FU</Text>
              <Text style={styles.hanFuValue}>{response.fu}</Text>
            </View>
            <View style={styles.hanFuItem}>
              <Text style={styles.hanFuLabel}>翻 HAN</Text>
              <Text style={styles.hanFuValue}>{response.han}</Text>
            </View>
          </View>

          <View style={styles.divider} />

          {/* Hand level + total points */}
          <View style={styles.totalBlock}>
            {hasLevelLabel && (
              <Text style={styles.levelLabel}>
                {levelLabel.zh}{'  '}
                <Text style={styles.levelEN}>{levelLabel.en}</Text>
              </Text>
            )}
            <Text style={styles.totalPoints}>{countedPoints.toLocaleString()}</Text>
          </View>

          <View style={styles.divider} />

          {/* Payment table */}
          <View style={styles.section}>
            <Text style={styles.sectionHeader}>支払い PAYMENT</Text>
            {players
              .filter(p => p.id !== winnerId)
              .map(p => (
                <View key={p.id} style={styles.paymentRow}>
                  <Text style={styles.paymentName}>{p.name}</Text>
                  <View style={styles.paymentLine} />
                  <Text
                    style={[
                      styles.paymentAmount,
                      { color: payments[p.id] < 0 ? Colors.accentRedLight : Colors.accentTeal },
                    ]}
                  >
                    {payments[p.id] > 0 ? '+' : ''}{payments[p.id].toLocaleString()}
                  </Text>
                </View>
              ))}
            {riichiBets > 0 && (
              <Text style={styles.richiBonus}>
                +{riichiBets * 1000} pts (riichi sticks)
              </Text>
            )}
          </View>

          <View style={{ height: 100 }} />
        </ScrollView>

        {/* Next button */}
        <View style={styles.footer}>
          <Pressable onPress={() => onNext(payments)} style={styles.nextBtn}>
            <LinearGradient
              colors={GoldGradient}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 0 }}
              style={styles.nextGradient}
            >
              <Text style={styles.nextJP}>次へ</Text>
              <Text style={styles.nextEN}>NEXT</Text>
            </LinearGradient>
          </Pressable>
        </View>
      </Animated.View>
    </View>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.8)',
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: Colors.bgSurface,
    borderTopLeftRadius: Radius.modal,
    borderTopRightRadius: Radius.modal,
    borderTopWidth: 1,
    borderColor: Colors.borderGlow,
    maxHeight: '90%',
    paddingTop: Spacing.md,
  },
  handle: {
    width: 40,
    height: 4,
    backgroundColor: Colors.borderGlow,
    borderRadius: 2,
    alignSelf: 'center',
    marginBottom: Spacing.md,
  },
  announcementBlock: {
    alignItems: 'center',
    paddingVertical: Spacing.md,
  },
  stars: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.xl,
    color: Colors.accentGold,
    marginBottom: Spacing.sm,
  },
  winnerName: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.xxl,
    color: Colors.textPrimary,
  },
  winsLabel: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
    letterSpacing: 3,
    marginTop: 4,
  },
  divider: {
    height: 1,
    backgroundColor: Colors.borderGlow,
    marginHorizontal: Spacing.lg,
    marginVertical: Spacing.md,
  },
  section: {
    paddingHorizontal: Spacing.lg,
  },
  sectionHeader: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
    letterSpacing: 2,
    marginBottom: Spacing.sm,
  },
  yakuContainer: {
    backgroundColor: Colors.bgSurface2,
    borderRadius: Radius.card,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.borderGlow,
  },
  yakuError: {
    fontFamily: Fonts.sans,
    fontSize: FontSize.sm,
    color: Colors.accentRedLight,
    marginTop: Spacing.sm,
  },
  hanFuRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: Spacing.xxl,
    paddingHorizontal: Spacing.lg,
    marginTop: Spacing.md,
  },
  hanFuItem: {
    alignItems: 'center',
  },
  hanFuLabel: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
    letterSpacing: 1,
  },
  hanFuValue: {
    fontFamily: Fonts.score,
    fontSize: FontSize.xxl,
    color: Colors.textPrimary,
  },
  totalBlock: {
    alignItems: 'center',
    paddingVertical: Spacing.sm,
  },
  levelLabel: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.lg,
    color: Colors.accentGold,
    marginBottom: Spacing.xs,
  },
  levelEN: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
    letterSpacing: 2,
  },
  totalPoints: {
    fontFamily: Fonts.score,
    fontSize: 56,
    color: Colors.accentGoldLight,
    letterSpacing: 2,
  },
  paymentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: Spacing.xs,
  },
  paymentName: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.sm,
    color: Colors.textPrimary,
    width: 100,
  },
  paymentLine: {
    flex: 1,
    height: 1,
    backgroundColor: Colors.borderGlow,
    marginHorizontal: Spacing.sm,
  },
  paymentAmount: {
    fontFamily: Fonts.score,
    fontSize: FontSize.xl,
    minWidth: 80,
    textAlign: 'right',
  },
  richiBonus: {
    fontFamily: Fonts.sans,
    fontSize: FontSize.xs,
    color: Colors.accentTeal,
    textAlign: 'right',
    marginTop: Spacing.xs,
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
  nextBtn: {
    borderRadius: Radius.button,
    overflow: 'hidden',
  },
  nextGradient: {
    paddingVertical: Spacing.md,
    alignItems: 'center',
  },
  nextJP: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.lg,
    color: Colors.bgDeep,
  },
  nextEN: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.bgDeep,
    letterSpacing: 3,
  },
  errorTitle: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.xl,
    color: Colors.accentRedLight,
    textAlign: 'center',
    marginBottom: Spacing.sm,
  },
  errorMsg: {
    fontFamily: Fonts.sans,
    fontSize: FontSize.md,
    color: Colors.textSecondary,
    textAlign: 'center',
    paddingHorizontal: Spacing.xl,
    marginBottom: Spacing.lg,
  },
  closeBtn: {
    alignSelf: 'center',
    paddingHorizontal: Spacing.xl,
    paddingVertical: Spacing.md,
    borderRadius: Radius.button,
    borderWidth: 1,
    borderColor: Colors.borderGlow,
  },
  closeBtnText: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.sm,
    color: Colors.accentGold,
  },
});
