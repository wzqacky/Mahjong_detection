import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  Pressable,
  ScrollView,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Colors, Fonts, Spacing, FontSize, Radius, GoldGradient } from '../constants/theme';
import { ScoreResponse, MeldEntry } from '../types';
import { useGameStore } from '../store/gameStore';
import PlayerIcon from '../components/PlayerIcon';
import HandInputScreen from './HandInputScreen';
import ScoreModal from './ScoreModal';

interface Props {
  visible: boolean;
  onClose: () => void;
}

type Step = 'select' | 'hand' | 'score';

export default function RoundModal({ visible, onClose }: Props) {
  const players = useGameStore(s => s.players);
  const recordWin = useGameStore(s => s.recordWin);

  const [step, setStep] = useState<Step>('select');
  const [winnerId, setWinnerId] = useState<string | null>(null);
  const [loserId, setLoserId] = useState<string | null>(null);
  const [isTsumo, setIsTsumo] = useState(true);
  const [scoreResponse, setScoreResponse] = useState<ScoreResponse | null>(null);
  const [meldsDone, setMeldsDone] = useState<MeldEntry[]>([]);

  const handleClose = () => {
    setStep('select');
    setWinnerId(null);
    setLoserId(null);
    setIsTsumo(true);
    setScoreResponse(null);
    setMeldsDone([]);
    onClose();
  };

  const handleResult = (response: ScoreResponse, melds: MeldEntry[]) => {
    setScoreResponse(response);
    setMeldsDone(melds);
    setStep('score');
  };

  const handleNext = (payments: Record<string, number>) => {
    if (!winnerId || !scoreResponse) return;
    recordWin({
      winnerId,
      loserId: isTsumo ? null : loserId,
      isTsumo,
      isDraw: false,
      tenpaiPlayerIds: [],
      yakuList: scoreResponse.yaku,
      han: scoreResponse.han,
      fu: scoreResponse.fu,
      payments,
    });
    handleClose();
  };

  const canProceed =
    winnerId !== null && (isTsumo || loserId !== null);

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={handleClose}>
      <View style={styles.overlay}>
        {step === 'hand' && winnerId ? (
          <View style={styles.fullSheet}>
            <HandInputScreen
              winnerId={winnerId}
              loserId={loserId}
              isTsumo={isTsumo}
              onBack={() => setStep('select')}
              onResult={handleResult}
            />
          </View>
        ) : step === 'score' && scoreResponse ? (
          <ScoreModal
            response={scoreResponse}
            winnerId={winnerId!}
            loserId={isTsumo ? null : loserId}
            isTsumo={isTsumo}
            onNext={handleNext}
            onClose={handleClose}
          />
        ) : (
          <View style={styles.sheet}>
            {/* Handle */}
            <View style={styles.handle} />

            {/* Title */}
            <Text style={styles.title}>和了 HU / WIN</Text>
            <View style={styles.divider} />

            <ScrollView style={styles.scroll} showsVerticalScrollIndicator={false}>
              {/* Winner selection */}
              <Text style={styles.sectionLabel}>誰が和了?  WHO WON?</Text>
              <View style={styles.chipRow}>
                {players.map(player => (
                  <Pressable
                    key={player.id}
                    onPress={() => setWinnerId(player.id)}
                    style={[
                      styles.chip,
                      winnerId === player.id && styles.chipActive,
                    ]}
                  >
                    <PlayerIcon iconId={player.iconId} size={32} />
                    <Text
                      style={[styles.chipText, winnerId === player.id && styles.chipTextActive]}
                      numberOfLines={1}
                    >
                      {player.name}
                    </Text>
                  </Pressable>
                ))}
              </View>

              {/* Tsumo / Ron toggle */}
              <Text style={[styles.sectionLabel, { marginTop: Spacing.lg }]}>
                どうやって?  HOW?
              </Text>
              <View style={styles.toggleRow}>
                <Pressable
                  onPress={() => setIsTsumo(true)}
                  style={[styles.toggle, isTsumo && styles.toggleTsumo]}
                >
                  <Text style={[styles.toggleText, isTsumo && styles.toggleTextTsumo]}>
                    自摸 TSUMO
                  </Text>
                </Pressable>
                <Pressable
                  onPress={() => setIsTsumo(false)}
                  style={[styles.toggle, !isTsumo && styles.toggleRon]}
                >
                  <Text style={[styles.toggleText, !isTsumo && styles.toggleTextRon]}>
                    榮 RON
                  </Text>
                </Pressable>
              </View>

              {/* Loser selection (Ron only) */}
              {!isTsumo && (
                <>
                  <Text style={[styles.sectionLabel, { marginTop: Spacing.lg }]}>
                    誰から?  FROM WHOM?
                  </Text>
                  <View style={styles.chipRow}>
                    {players
                      .filter(p => p.id !== winnerId)
                      .map(player => (
                        <Pressable
                          key={player.id}
                          onPress={() => setLoserId(player.id)}
                          style={[
                            styles.chip,
                            loserId === player.id && styles.chipRon,
                          ]}
                        >
                          <PlayerIcon iconId={player.iconId} size={32} />
                          <Text
                            style={[
                              styles.chipText,
                              loserId === player.id && styles.chipTextRon,
                            ]}
                            numberOfLines={1}
                          >
                            {player.name}
                          </Text>
                        </Pressable>
                      ))}
                  </View>
                </>
              )}

              <View style={{ height: Spacing.xxl }} />
            </ScrollView>

            {/* Enter hand button */}
            <View style={styles.footer}>
              <Pressable
                onPress={() => canProceed && setStep('hand')}
                disabled={!canProceed}
                style={[styles.enterBtn, !canProceed && styles.enterBtnDisabled]}
              >
                <LinearGradient
                  colors={canProceed ? GoldGradient : ['#555', '#555']}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={styles.enterGradient}
                >
                  <Text style={styles.enterJP}>手牌を入力</Text>
                  <Text style={styles.enterEN}>ENTER HAND</Text>
                </LinearGradient>
              </Pressable>
            </View>
          </View>
        )}
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.7)',
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: Colors.bgSurface,
    borderTopLeftRadius: Radius.modal,
    borderTopRightRadius: Radius.modal,
    borderTopWidth: 1,
    borderColor: Colors.borderGlow,
    maxHeight: '80%',
    paddingTop: Spacing.md,
  },
  fullSheet: {
    flex: 1,
    backgroundColor: Colors.bgSurface,
    marginTop: 60,
    borderTopLeftRadius: Radius.modal,
    borderTopRightRadius: Radius.modal,
  },
  handle: {
    width: 40,
    height: 4,
    backgroundColor: Colors.borderGlow,
    borderRadius: 2,
    alignSelf: 'center',
    marginBottom: Spacing.md,
  },
  title: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.xl,
    color: Colors.textPrimary,
    textAlign: 'center',
    marginBottom: Spacing.sm,
  },
  divider: {
    height: 1,
    backgroundColor: Colors.borderGlow,
    marginHorizontal: Spacing.lg,
    marginBottom: Spacing.md,
  },
  scroll: {
    paddingHorizontal: Spacing.lg,
  },
  sectionLabel: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
    letterSpacing: 1,
    marginBottom: Spacing.sm,
  },
  chipRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.sm,
  },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: Spacing.xs,
    paddingHorizontal: Spacing.sm,
    paddingVertical: Spacing.xs,
    borderRadius: Radius.button,
    borderWidth: 1,
    borderColor: Colors.borderGlow,
    backgroundColor: Colors.bgSurface2,
    maxWidth: '48%',
  },
  chipActive: {
    borderColor: Colors.accentGold,
    backgroundColor: 'rgba(201,168,76,0.15)',
  },
  chipRon: {
    borderColor: Colors.accentRed,
    backgroundColor: 'rgba(179,48,64,0.15)',
  },
  chipText: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
    flexShrink: 1,
  },
  chipTextActive: {
    color: Colors.accentGold,
  },
  chipTextRon: {
    color: Colors.accentRedLight,
  },
  toggleRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
  },
  toggle: {
    flex: 1,
    paddingVertical: Spacing.sm,
    borderRadius: Radius.button,
    borderWidth: 1,
    borderColor: Colors.borderGlow,
    alignItems: 'center',
  },
  toggleTsumo: {
    borderColor: Colors.accentTeal,
    backgroundColor: 'rgba(45,212,191,0.15)',
  },
  toggleRon: {
    borderColor: Colors.accentRed,
    backgroundColor: 'rgba(179,48,64,0.15)',
  },
  toggleText: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
  },
  toggleTextTsumo: {
    color: Colors.accentTeal,
  },
  toggleTextRon: {
    color: Colors.accentRedLight,
  },
  footer: {
    padding: Spacing.lg,
    paddingTop: Spacing.sm,
  },
  enterBtn: {
    borderRadius: Radius.button,
    overflow: 'hidden',
  },
  enterBtnDisabled: {
    opacity: 0.5,
  },
  enterGradient: {
    paddingVertical: Spacing.md,
    alignItems: 'center',
  },
  enterJP: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.lg,
    color: Colors.bgDeep,
  },
  enterEN: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.bgDeep,
    letterSpacing: 3,
  },
});
