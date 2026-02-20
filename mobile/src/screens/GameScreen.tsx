import React, { useRef, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  ActionSheetIOS,
  Platform,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { LinearGradient } from 'expo-linear-gradient';

import { Colors, Fonts, Spacing, FontSize, Radius, GoldGradient } from '../constants/theme';
import { RootStackParamList } from '../types';
import { useGameStore, selectRoundLabel } from '../store/gameStore';
import PlayerCard from '../components/PlayerCard';
import RoundModal from '../modals/RoundModal';
import DrawModal from '../modals/DrawModal';
import HistoryModal from '../modals/HistoryModal';

type Nav = NativeStackNavigationProp<RootStackParamList, 'Game'>;

export default function GameScreen() {
  const navigation = useNavigation<Nav>();

  const players = useGameStore(s => s.players);
  const playerRiichi = useGameStore(s => s.playerRiichi);
  const riichiBets = useGameStore(s => s.riichiBets);
  const honba = useGameStore(s => s.honba);
  const rounds = useGameStore(s => s.rounds);
  const roundLabel = useGameStore(selectRoundLabel);
  const currentRoundWind = useGameStore(s => s.currentRoundWind);
  const currentRoundNumber = useGameStore(s => s.currentRoundNumber);
  const endGame = useGameStore(s => s.endGame);
  const declareRiichi = useGameStore(s => s.declareRiichi);
  const undoRiichi = useGameStore(s => s.undoRiichi);

  const [roundModalVisible, setRoundModalVisible] = useState(false);
  const [drawModalVisible, setDrawModalVisible] = useState(false);
  const [historyModalVisible, setHistoryModalVisible] = useState(false);

  // Track score deltas (difference from last round)
  const lastScores = useRef<number[]>(players.map(p => p.score));
  const deltas = players.map((p, i) => p.score - (lastScores.current[i] ?? p.score));

  const handleLongPress = (playerIndex: number) => {
    const hasRiichi = playerRiichi[playerIndex];
    const options = hasRiichi
      ? ['undo Riichi', 'Cancel']
      : ['Declare Riichi', 'Cancel'];
    const destructiveIdx = hasRiichi ? 0 : undefined;

    if (Platform.OS === 'ios') {
      ActionSheetIOS.showActionSheetWithOptions(
        { options, cancelButtonIndex: options.length - 1, destructiveButtonIndex: destructiveIdx },
        buttonIndex => {
          if (buttonIndex === 0) {
            if (hasRiichi) undoRiichi(playerIndex);
            else declareRiichi(playerIndex);
          }
        },
      );
    } else {
      // Android fallback
      Alert.alert(
        players[playerIndex].name,
        hasRiichi ? '立直を取り消しますか？' : '立直を宣言しますか？',
        [
          { text: 'Cancel', style: 'cancel' },
          {
            text: hasRiichi ? 'Undo Riichi' : 'Declare Riichi',
            onPress: () => {
              if (hasRiichi) undoRiichi(playerIndex);
              else declareRiichi(playerIndex);
            },
          },
        ],
      );
    }
  };

  const handleEnd = () => {
    Alert.alert('終了', 'ゲームを終了しますか？', [
      { text: 'キャンセル', style: 'cancel' },
      {
        text: '終了',
        style: 'destructive',
        onPress: () => {
          endGame();
          navigation.navigate('Result');
        },
      },
    ]);
  };

  const windLabel = currentRoundWind === 'East' ? '東' : '南';

  return (
    <SafeAreaView style={styles.safe}>
      {/* Header */}
      <View style={styles.header}>
        <View>
          <Text style={styles.roundLabel}>{roundLabel}</Text>
          <Text style={styles.roundSub}>
            {currentRoundWind.toUpperCase()} {currentRoundNumber}
            {'  ·  HONBA '}
            {honba}
          </Text>
        </View>
        <Pressable onPress={() => setHistoryModalVisible(true)} style={styles.historyBtn}>
          <Text style={styles.historyText}>≡ 履歴</Text>
        </Pressable>
      </View>

      <View style={styles.divider} />

      <ScrollView contentContainerStyle={styles.scroll}>
        {/* Watermark */}
        <Text style={styles.watermark}>雀</Text>

        {/* 2×2 player grid */}
        <View style={styles.grid}>
          {players.map((player, i) => (
            <View key={player.id} style={styles.cardWrapper}>
              <PlayerCard
                player={player}
                delta={deltas[i]}
                hasRiichi={playerRiichi[i] ?? false}
                onLongPress={() => handleLongPress(i)}
              />
            </View>
          ))}
        </View>

        {/* Riichi sticks info */}
        <View style={styles.sticksRow}>
          <Text style={styles.sticksLabel}>供託</Text>
          <Text style={styles.sticksValue}>{riichiBets} 本</Text>
          <Text style={styles.sticksPoints}>({(riichiBets * 1000).toLocaleString()} pts)</Text>
        </View>
      </ScrollView>

      {/* Footer actions */}
      <View style={styles.footer}>
        <Pressable onPress={() => setRoundModalVisible(true)} style={styles.primaryBtn}>
          <LinearGradient
            colors={GoldGradient}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 0 }}
            style={styles.primaryGradient}
          >
            <Text style={styles.primaryText}>＋ 次の局</Text>
          </LinearGradient>
        </Pressable>

        <View style={styles.secondaryRow}>
          <Pressable
            onPress={() => setDrawModalVisible(true)}
            style={styles.secondaryBtn}
          >
            <Text style={styles.secondaryText}>引き分け DRAW</Text>
          </Pressable>
          <Pressable onPress={handleEnd} style={styles.secondaryBtn}>
            <Text style={[styles.secondaryText, { color: Colors.accentRedLight }]}>
              終了 END
            </Text>
          </Pressable>
        </View>
      </View>

      <RoundModal
        visible={roundModalVisible}
        onClose={() => {
          // Update last scores after round is recorded
          lastScores.current = players.map(p => p.score);
          setRoundModalVisible(false);
        }}
      />

      <DrawModal
        visible={drawModalVisible}
        onClose={() => {
          lastScores.current = players.map(p => p.score);
          setDrawModalVisible(false);
        }}
      />

      <HistoryModal
        visible={historyModalVisible}
        onClose={() => setHistoryModalVisible(false)}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: {
    flex: 1,
    backgroundColor: Colors.bgDeep,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    paddingHorizontal: Spacing.lg,
    paddingTop: Spacing.md,
    paddingBottom: Spacing.sm,
  },
  roundLabel: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.xl,
    color: Colors.accentGold,
  },
  roundSub: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
    letterSpacing: 1,
    marginTop: 2,
  },
  historyBtn: {
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs,
  },
  historyText: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.sm,
    color: Colors.accentGold,
  },
  divider: {
    height: 1,
    backgroundColor: Colors.borderGlow,
    marginHorizontal: Spacing.lg,
  },
  scroll: {
    padding: Spacing.lg,
    paddingBottom: Spacing.sm,
  },
  watermark: {
    position: 'absolute',
    top: -30,
    right: 0,
    fontSize: 200,
    color: 'rgba(201,168,76,0.03)',
    fontFamily: Fonts.serif,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.sm,
  },
  cardWrapper: {
    width: '48%',
  },
  sticksRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.sm,
    marginTop: Spacing.md,
    paddingHorizontal: Spacing.xs,
  },
  sticksLabel: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
  },
  sticksValue: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.sm,
    color: Colors.accentGold,
  },
  sticksPoints: {
    fontFamily: Fonts.sans,
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
  },
  footer: {
    padding: Spacing.lg,
    paddingTop: Spacing.sm,
    gap: Spacing.sm,
  },
  primaryBtn: {
    borderRadius: Radius.button,
    overflow: 'hidden',
  },
  primaryGradient: {
    paddingVertical: Spacing.md,
    alignItems: 'center',
  },
  primaryText: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.lg,
    color: Colors.bgDeep,
  },
  secondaryRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
  },
  secondaryBtn: {
    flex: 1,
    paddingVertical: Spacing.sm,
    borderRadius: Radius.button,
    borderWidth: 1,
    borderColor: Colors.borderGlow,
    alignItems: 'center',
  },
  secondaryText: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.sm,
    color: Colors.accentGold,
  },
});
