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
import { useGameStore } from '../store/gameStore';
import PlayerIcon from '../components/PlayerIcon';

interface Props {
  visible: boolean;
  onClose: () => void;
}

export default function DrawModal({ visible, onClose }: Props) {
  const players = useGameStore(s => s.players);
  const recordDraw = useGameStore(s => s.recordDraw);
  const [tenpaiIds, setTenpaiIds] = useState<Set<string>>(new Set());

  const togglePlayer = (id: string) => {
    setTenpaiIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleConfirm = () => {
    recordDraw([...tenpaiIds]);
    setTenpaiIds(new Set());
    onClose();
  };

  const handleClose = () => {
    setTenpaiIds(new Set());
    onClose();
  };

  // Compute preview payments
  const tenpaiCount = tenpaiIds.size;
  const notenCount = players.length - tenpaiCount;
  let receivePerTenpai = 0;
  let payPerNoten = 0;
  if (tenpaiCount > 0 && tenpaiCount < players.length) {
    receivePerTenpai = Math.floor(3000 / tenpaiCount);
    payPerNoten = Math.floor(3000 / notenCount);
  }

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={handleClose}>
      <View style={styles.overlay}>
        <View style={styles.sheet}>
          <View style={styles.handle} />
          <Text style={styles.title}>流局 DRAW / RYUUKYOKU</Text>
          <View style={styles.divider} />

          <ScrollView showsVerticalScrollIndicator={false} style={styles.scroll}>
            <Text style={styles.sectionLabel}>誰が聴牌?  WHO IS TENPAI?</Text>

            <View style={styles.grid}>
              {players.map(player => {
                const isTenpai = tenpaiIds.has(player.id);
                return (
                  <Pressable
                    key={player.id}
                    onPress={() => togglePlayer(player.id)}
                    style={[styles.playerCard, isTenpai && styles.playerCardActive]}
                  >
                    <PlayerIcon iconId={player.iconId} size={44} />
                    <Text
                      style={[styles.playerName, isTenpai && styles.playerNameActive]}
                      numberOfLines={1}
                    >
                      {player.name}
                    </Text>
                    <View style={[styles.checkbox, isTenpai && styles.checkboxActive]}>
                      {isTenpai && <Text style={styles.checkmark}>✓</Text>}
                    </View>
                  </Pressable>
                );
              })}
            </View>

            {/* Payment preview */}
            <View style={styles.previewBlock}>
              <Text style={styles.previewLabel}>── PAYMENT PREVIEW ──</Text>
              {tenpaiCount === 0 || tenpaiCount === players.length ? (
                <Text style={styles.previewText}>No exchange</Text>
              ) : (
                <>
                  <View style={styles.previewRow}>
                    <Text style={styles.previewDesc}>
                      Tenpai ({tenpaiCount}) receive:
                    </Text>
                    <Text style={[styles.previewAmount, { color: Colors.accentTeal }]}>
                      +{receivePerTenpai.toLocaleString()}
                    </Text>
                  </View>
                  <View style={styles.previewRow}>
                    <Text style={styles.previewDesc}>
                      Noten ({notenCount}) pay:
                    </Text>
                    <Text style={[styles.previewAmount, { color: Colors.accentRedLight }]}>
                      -{payPerNoten.toLocaleString()}
                    </Text>
                  </View>
                </>
              )}
            </View>

            <View style={{ height: 80 }} />
          </ScrollView>

          <View style={styles.footer}>
            <View style={styles.btnRow}>
              <Pressable onPress={handleClose} style={styles.cancelBtn}>
                <Text style={styles.cancelText}>キャンセル</Text>
              </Pressable>
              <Pressable onPress={handleConfirm} style={styles.confirmBtn}>
                <LinearGradient
                  colors={GoldGradient}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={styles.confirmGradient}
                >
                  <Text style={styles.confirmJP}>確認</Text>
                  <Text style={styles.confirmEN}>CONFIRM</Text>
                </LinearGradient>
              </Pressable>
            </View>
          </View>
        </View>
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
    marginBottom: Spacing.md,
  },
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: Spacing.sm,
    marginBottom: Spacing.lg,
  },
  playerCard: {
    width: '47%',
    backgroundColor: Colors.bgSurface2,
    borderRadius: Radius.card,
    borderWidth: 1,
    borderColor: Colors.borderGlow,
    padding: Spacing.md,
    alignItems: 'center',
    gap: Spacing.xs,
  },
  playerCardActive: {
    borderColor: Colors.accentTeal,
    backgroundColor: 'rgba(45,212,191,0.1)',
  },
  playerName: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
  },
  playerNameActive: {
    color: Colors.accentTeal,
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 1.5,
    borderColor: Colors.textSecondary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxActive: {
    borderColor: Colors.accentTeal,
    backgroundColor: Colors.accentTeal,
  },
  checkmark: {
    color: Colors.bgDeep,
    fontSize: FontSize.xs,
    fontWeight: 'bold',
  },
  previewBlock: {
    backgroundColor: Colors.bgSurface2,
    borderRadius: Radius.card,
    padding: Spacing.md,
    borderWidth: 1,
    borderColor: Colors.borderGlow,
    gap: Spacing.sm,
  },
  previewLabel: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
    letterSpacing: 2,
    textAlign: 'center',
    marginBottom: Spacing.xs,
  },
  previewText: {
    fontFamily: Fonts.sans,
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  previewRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  previewDesc: {
    fontFamily: Fonts.sans,
    fontSize: FontSize.sm,
    color: Colors.textPrimary,
  },
  previewAmount: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.md,
  },
  footer: {
    padding: Spacing.lg,
    paddingTop: Spacing.sm,
    borderTopWidth: 1,
    borderTopColor: Colors.borderGlow,
  },
  btnRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
  },
  cancelBtn: {
    flex: 1,
    paddingVertical: Spacing.sm,
    borderRadius: Radius.button,
    borderWidth: 1,
    borderColor: Colors.borderGlow,
    alignItems: 'center',
  },
  cancelText: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.sm,
    color: Colors.textSecondary,
  },
  confirmBtn: {
    flex: 2,
    borderRadius: Radius.button,
    overflow: 'hidden',
  },
  confirmGradient: {
    paddingVertical: Spacing.sm,
    alignItems: 'center',
  },
  confirmJP: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.md,
    color: Colors.bgDeep,
  },
  confirmEN: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.bgDeep,
    letterSpacing: 3,
  },
});
