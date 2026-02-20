import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TextInput,
  ScrollView,
  Pressable,
  LayoutAnimation,
  Modal,
  FlatList,
  Platform,
  UIManager,
  Alert,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';

import { Colors, Fonts, Spacing, FontSize, Radius, GoldGradient } from '../constants/theme';
import { DEFAULT_ICON_IDS } from '../constants/icons';
import { RootStackParamList, Player } from '../types';
import { useGameStore } from '../store/gameStore';
import PlayerIcon from '../components/PlayerIcon';
import WindBadge from '../components/WindBadge';
import IconPickerModal from '../modals/IconPickerModal';

if (Platform.OS === 'android' && UIManager.setLayoutAnimationEnabledExperimental) {
  UIManager.setLayoutAnimationEnabledExperimental(true);
}

type Nav = NativeStackNavigationProp<RootStackParamList, 'Setup'>;

const WINDS: Array<'East' | 'South' | 'West' | 'North'> = ['East', 'South', 'West', 'North'];
const SCORE_OPTIONS = [
  { label: '25,000', value: 25000 },
  { label: '30,000', value: 30000 },
];

export default function SetupScreen() {
  const navigation = useNavigation<Nav>();
  const initGame = useGameStore(s => s.initGame);

  const [playerCount, setPlayerCount] = useState(4);
  const [names, setNames] = useState(['', '', '', '']);
  const [iconIds, setIconIds] = useState([...DEFAULT_ICON_IDS]);
  const [winds, setWinds] = useState<Array<'East' | 'South' | 'West' | 'North'>>([...WINDS]);
  const [startingScore, setStartingScore] = useState(25000);
  const [scorePickerVisible, setScorePickerVisible] = useState(false);
  const [iconPickerIndex, setIconPickerIndex] = useState<number | null>(null);

  const cycleWind = (idx: number) => {
    setWinds(prev => {
      const next = [...prev];
      const cur = WINDS.indexOf(next[idx]);
      next[idx] = WINDS[(cur + 1) % 4];
      return next;
    });
  };

  const togglePlayerCount = (count: number) => {
    LayoutAnimation.configureNext(LayoutAnimation.Presets.easeInEaseOut);
    setPlayerCount(count);
  };

  const handleStart = () => {
    const activePlayers = names.slice(0, playerCount);
    if (activePlayers.some(n => n.trim() === '')) {
      Alert.alert('入力エラー', 'すべてのプレイヤー名を入力してください。');
      return;
    }
    const players: Player[] = activePlayers.map((name, i) => ({
      id: `player-${i}`,
      name: name.trim(),
      iconId: iconIds[i],
      seatWind: winds[i],
      score: startingScore,
      isDealer: i === 0,
    }));
    initGame(players, startingScore);
    navigation.navigate('Game');
  };

  return (
    <SafeAreaView style={styles.safe}>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        {/* Watermark */}
        <Text style={styles.watermark}>麻</Text>

        {/* Title */}
        <View style={styles.titleBlock}>
          <Text style={styles.titleJP}>新しいゲーム</Text>
          <Text style={styles.titleEN}>NEW GAME</Text>
        </View>

        {/* Player count toggle */}
        <View style={styles.card}>
          <Text style={styles.cardLabel}>PLAYERS</Text>
          <View style={styles.segmentRow}>
            {[3, 4].map(n => (
              <Pressable
                key={n}
                style={[styles.segment, playerCount === n && styles.segmentActive]}
                onPress={() => togglePlayerCount(n)}
              >
                <Text style={[styles.segmentText, playerCount === n && styles.segmentTextActive]}>
                  {n}
                </Text>
              </Pressable>
            ))}
          </View>
        </View>

        {/* Player rows */}
        <View style={styles.card}>
          {Array.from({ length: playerCount }, (_, i) => (
            <View key={i} style={[styles.playerRow, i > 0 && styles.rowDivider]}>
              <PlayerIcon
                iconId={iconIds[i]}
                size={44}
                onPress={() => setIconPickerIndex(i)}
              />
              <WindBadge
                wind={winds[i]}
                isDealer={i === 0}
                onPress={() => cycleWind(i)}
                size="sm"
              />
              <TextInput
                style={styles.nameInput}
                placeholder={`Player ${i + 1}`}
                placeholderTextColor={Colors.textSecondary}
                value={names[i]}
                onChangeText={txt => {
                  const next = [...names];
                  next[i] = txt;
                  setNames(next);
                }}
                maxLength={16}
              />
            </View>
          ))}
        </View>

        {/* Starting score */}
        <Pressable style={styles.card} onPress={() => setScorePickerVisible(true)}>
          <Text style={styles.cardLabel}>STARTING SCORE</Text>
          <Text style={styles.cardValue}>
            {startingScore.toLocaleString()} ▾
          </Text>
        </Pressable>

        {/* Start button */}
        <Pressable onPress={handleStart} style={styles.startBtn}>
          <LinearGradient
            colors={GoldGradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.startGradient}
          >
            <Text style={styles.startJP}>始める</Text>
            <Text style={styles.startEN}>START</Text>
          </LinearGradient>
        </Pressable>
      </ScrollView>

      {/* Score picker modal */}
      <Modal
        visible={scorePickerVisible}
        transparent
        animationType="fade"
        onRequestClose={() => setScorePickerVisible(false)}
      >
        <Pressable style={styles.overlay} onPress={() => setScorePickerVisible(false)}>
          <View style={styles.pickerCard}>
            {SCORE_OPTIONS.map(opt => (
              <Pressable
                key={opt.value}
                style={[styles.pickerItem, startingScore === opt.value && styles.pickerItemActive]}
                onPress={() => {
                  setStartingScore(opt.value);
                  setScorePickerVisible(false);
                }}
              >
                <Text style={[styles.pickerText, startingScore === opt.value && styles.pickerTextActive]}>
                  {opt.label}
                </Text>
              </Pressable>
            ))}
          </View>
        </Pressable>
      </Modal>

      {/* Icon picker */}
      {iconPickerIndex !== null && (
        <IconPickerModal
          playerName={names[iconPickerIndex] || `Player ${iconPickerIndex + 1}`}
          currentIconId={iconIds[iconPickerIndex]}
          takenIconIds={iconIds.filter((_, i) => i !== iconPickerIndex)}
          onConfirm={iconId => {
            const next = [...iconIds];
            next[iconPickerIndex] = iconId;
            setIconIds(next);
            setIconPickerIndex(null);
          }}
          onClose={() => setIconPickerIndex(null)}
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: Colors.bgDeep,
  },
  scroll: {
    padding: Spacing.lg,
    paddingBottom: Spacing.xxl,
  },
  watermark: {
    position: 'absolute',
    top: -20,
    right: 20,
    fontSize: 160,
    color: 'rgba(201,168,76,0.03)',
    fontFamily: Fonts.serif,
  },
  titleBlock: {
    alignItems: 'center',
    marginBottom: Spacing.xl,
    marginTop: Spacing.lg,
  },
  titleJP: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.xxl,
    color: Colors.textPrimary,
    marginBottom: 4,
  },
  titleEN: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
    letterSpacing: 3,
  },
  card: {
    backgroundColor: Colors.bgSurface,
    borderRadius: Radius.card,
    borderWidth: 1,
    borderColor: Colors.borderGlow,
    padding: Spacing.md,
    marginBottom: Spacing.md,
  },
  cardLabel: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
    letterSpacing: 2,
    marginBottom: Spacing.sm,
  },
  cardValue: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.md,
    color: Colors.accentGold,
  },
  segmentRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
  },
  segment: {
    flex: 1,
    paddingVertical: Spacing.sm,
    borderRadius: Radius.button,
    borderWidth: 1,
    borderColor: Colors.borderGlow,
    alignItems: 'center',
  },
  segmentActive: {
    backgroundColor: 'rgba(201,168,76,0.15)',
    borderColor: Colors.accentGold,
  },
  segmentText: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.md,
    color: Colors.textSecondary,
  },
  segmentTextActive: {
    color: Colors.accentGold,
  },
  playerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: Spacing.sm,
    gap: Spacing.sm,
  },
  rowDivider: {
    borderTopWidth: 1,
    borderTopColor: Colors.borderGlow,
  },
  nameInput: {
    flex: 1,
    fontFamily: Fonts.sans,
    fontSize: FontSize.md,
    color: Colors.textPrimary,
    backgroundColor: Colors.bgSurface2,
    borderRadius: Radius.button,
    paddingHorizontal: Spacing.md,
    paddingVertical: Spacing.sm,
    borderWidth: 1,
    borderColor: Colors.borderGlow,
  },
  startBtn: {
    marginTop: Spacing.md,
    borderRadius: Radius.button,
    overflow: 'hidden',
  },
  startGradient: {
    paddingVertical: Spacing.md,
    alignItems: 'center',
  },
  startJP: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.lg,
    color: Colors.bgDeep,
  },
  startEN: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.bgDeep,
    letterSpacing: 3,
  },
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  pickerCard: {
    backgroundColor: Colors.bgSurface,
    borderRadius: Radius.modal,
    borderWidth: 1,
    borderColor: Colors.borderGlow,
    width: 240,
    overflow: 'hidden',
  },
  pickerItem: {
    padding: Spacing.lg,
    alignItems: 'center',
  },
  pickerItemActive: {
    backgroundColor: 'rgba(201,168,76,0.15)',
  },
  pickerText: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.lg,
    color: Colors.textPrimary,
  },
  pickerTextActive: {
    color: Colors.accentGold,
  },
});
