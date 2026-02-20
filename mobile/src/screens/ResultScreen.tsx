import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Animated,
  Pressable,
  ScrollView,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { Colors, Fonts, Spacing, FontSize, Radius, GoldGradient } from '../constants/theme';
import { RootStackParamList, Player } from '../types';
import { useGameStore } from '../store/gameStore';
import PlayerIcon from '../components/PlayerIcon';

type Nav = NativeStackNavigationProp<RootStackParamList, 'Result'>;

const RANK_MEDALS = ['🥇', '🥈', '🥉', ''];
const RANK_LABELS = ['1位', '2位', '3位', '4位'];

interface RankedPlayer extends Player {
  rank: number;
  delta: number;
}

function ResultCard({ player, rank, delay }: { player: RankedPlayer; rank: number; delay: number }) {
  const translateY = useRef(new Animated.Value(-60)).current;
  const opacity = useRef(new Animated.Value(0)).current;
  const glowAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.spring(translateY, {
        toValue: 0,
        tension: 50,
        friction: 8,
        delay,
        useNativeDriver: true,
      }),
      Animated.timing(opacity, {
        toValue: 1,
        duration: 300,
        delay,
        useNativeDriver: true,
      }),
    ]).start(() => {
      if (rank === 0) {
        // Gold glow pulse for 1st place
        Animated.loop(
          Animated.sequence([
            Animated.timing(glowAnim, { toValue: 1, duration: 1000, useNativeDriver: true }),
            Animated.timing(glowAnim, { toValue: 0, duration: 1000, useNativeDriver: true }),
          ]),
        ).start();
      }
    });
  }, []);

  const isFirst = rank === 0;
  const isLast = rank === 3;

  const cardStyle = [
    styles.card,
    isFirst && styles.cardFirst,
    isLast && styles.cardLast,
  ];

  const glowOpacity = glowAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0, 0.3],
  });

  return (
    <Animated.View style={{ opacity, transform: [{ translateY }] }}>
      <View style={cardStyle}>
        {isFirst && (
          <Animated.View
            style={[StyleSheet.absoluteFillObject, styles.glowOverlay, { opacity: glowOpacity }]}
          />
        )}

        <View style={styles.cardLeft}>
          {RANK_MEDALS[rank] ? (
            <Text style={styles.medal}>{RANK_MEDALS[rank]}</Text>
          ) : (
            <Text style={styles.rankNum}>{RANK_LABELS[rank]}</Text>
          )}
          <Text style={styles.rankLabel}>{RANK_LABELS[rank]}</Text>
        </View>

        <PlayerIcon iconId={player.iconId} size={44} />

        <View style={styles.cardCenter}>
          <Text style={styles.playerName} numberOfLines={1}>{player.name}</Text>
        </View>

        <View style={styles.cardRight}>
          <Text style={[styles.finalScore, isFirst && styles.firstScore]}>
            {player.score.toLocaleString()}
          </Text>
          <Text
            style={[
              styles.deltaScore,
              { color: player.delta >= 0 ? Colors.accentTeal : Colors.accentRedLight },
            ]}
          >
            {player.delta >= 0 ? '+' : ''}{player.delta.toLocaleString()}
          </Text>
        </View>
      </View>
    </Animated.View>
  );
}

export default function ResultScreen() {
  const navigation = useNavigation<Nav>();
  const players = useGameStore(s => s.players);
  const startingScore = useGameStore(s => s.startingScore);
  const resetGame = useGameStore(s => s.resetGame);

  // Sort by score descending
  const ranked: RankedPlayer[] = [...players]
    .sort((a, b) => b.score - a.score)
    .map((p, i) => ({
      ...p,
      rank: i,
      delta: p.score - startingScore,
    }));

  const handleRematch = () => {
    resetGame();
    navigation.navigate('Setup');
  };

  return (
    <SafeAreaView style={styles.safe}>
      {/* Watermark */}
      <Text style={styles.watermark}>終</Text>

      {/* Title */}
      <View style={styles.titleBlock}>
        <Text style={styles.titleJP}>対局終了</Text>
        <Text style={styles.titleEN}>GAME OVER</Text>
      </View>

      <ScrollView contentContainerStyle={styles.scroll}>
        {ranked.map((player, i) => (
          <ResultCard
            key={player.id}
            player={player}
            rank={i}
            delay={i * 120}
          />
        ))}
      </ScrollView>

      {/* Actions */}
      <View style={styles.footer}>
        <View style={styles.divider} />
        <Pressable onPress={handleRematch} style={styles.rematchBtn}>
          <LinearGradient
            colors={GoldGradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.rematchGradient}
          >
            <Text style={styles.rematchJP}>再戦</Text>
            <Text style={styles.rematchEN}>REMATCH</Text>
          </LinearGradient>
        </Pressable>
        <Pressable onPress={handleRematch} style={styles.quitBtn}>
          <Text style={styles.quitText}>終了  QUIT</Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: Colors.bgDeep,
  },
  watermark: {
    position: 'absolute',
    top: 40,
    right: 20,
    fontSize: 180,
    color: 'rgba(201,168,76,0.03)',
    fontFamily: Fonts.serif,
  },
  titleBlock: {
    alignItems: 'center',
    paddingTop: Spacing.xl,
    paddingBottom: Spacing.md,
  },
  titleJP: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.xxl,
    color: Colors.textPrimary,
  },
  titleEN: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
    letterSpacing: 3,
    marginTop: 4,
  },
  scroll: {
    padding: Spacing.lg,
    gap: Spacing.sm,
  },
  card: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.bgSurface,
    borderRadius: Radius.card,
    borderWidth: 1,
    borderColor: Colors.borderGlow,
    padding: Spacing.md,
    gap: Spacing.sm,
    overflow: 'hidden',
  },
  cardFirst: {
    borderColor: Colors.accentGold,
    backgroundColor: '#141209',
    shadowColor: Colors.accentGold,
    shadowOpacity: 0.3,
    shadowRadius: 12,
    shadowOffset: { width: 0, height: 4 },
    elevation: 8,
  },
  cardLast: {
    borderColor: 'rgba(179,48,64,0.3)',
  },
  glowOverlay: {
    backgroundColor: Colors.accentGold,
    borderRadius: Radius.card,
  },
  cardLeft: {
    width: 40,
    alignItems: 'center',
  },
  medal: {
    fontSize: FontSize.xl,
  },
  rankNum: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
  },
  rankLabel: {
    fontFamily: Fonts.sans,
    fontSize: 9,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  cardCenter: {
    flex: 1,
    marginLeft: Spacing.xs,
  },
  playerName: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.md,
    color: Colors.textPrimary,
  },
  cardRight: {
    alignItems: 'flex-end',
  },
  finalScore: {
    fontFamily: Fonts.score,
    fontSize: FontSize.xxl,
    color: Colors.textPrimary,
  },
  firstScore: {
    color: Colors.accentGoldLight,
    fontSize: FontSize.score,
  },
  deltaScore: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.sm,
  },
  footer: {
    padding: Spacing.lg,
    paddingTop: 0,
    gap: Spacing.sm,
  },
  divider: {
    height: 1,
    backgroundColor: Colors.borderGlow,
    marginBottom: Spacing.sm,
  },
  rematchBtn: {
    borderRadius: Radius.button,
    overflow: 'hidden',
  },
  rematchGradient: {
    paddingVertical: Spacing.md,
    alignItems: 'center',
  },
  rematchJP: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.lg,
    color: Colors.bgDeep,
  },
  rematchEN: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.bgDeep,
    letterSpacing: 3,
  },
  quitBtn: {
    paddingVertical: Spacing.sm,
    borderRadius: Radius.button,
    borderWidth: 1,
    borderColor: Colors.borderGlow,
    alignItems: 'center',
  },
  quitText: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
  },
});
