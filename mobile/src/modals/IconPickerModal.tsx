import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Modal,
  ScrollView,
  Pressable,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Colors, Fonts, Spacing, FontSize, Radius, GoldGradient } from '../constants/theme';
import { PLAYER_ICONS, ICON_CATEGORIES } from '../constants/icons';
import PlayerIcon from '../components/PlayerIcon';

interface Props {
  playerName: string;
  currentIconId: string;
  takenIconIds: string[];
  onConfirm: (iconId: string) => void;
  onClose: () => void;
}

export default function IconPickerModal({
  playerName,
  currentIconId,
  takenIconIds,
  onConfirm,
  onClose,
}: Props) {
  const [selected, setSelected] = useState(currentIconId);

  return (
    <Modal visible transparent animationType="slide" onRequestClose={onClose}>
      <View style={styles.overlay}>
        <View style={styles.sheet}>
          {/* Handle */}
          <View style={styles.handle} />

          {/* Header */}
          <Text style={styles.titleJP}>アイコン選択</Text>
          <Text style={styles.titleEN}>CHOOSE ICON</Text>
          <Text style={styles.playerName}>{playerName}</Text>
          <View style={styles.divider} />

          <ScrollView style={styles.scroll} showsVerticalScrollIndicator={false}>
            {ICON_CATEGORIES.map(cat => {
              const catIcons = PLAYER_ICONS.filter(ic => ic.category === cat.key);
              return (
                <View key={cat.key} style={styles.category}>
                  <Text style={styles.catLabel}>
                    {cat.labelJP}{'  '}
                    <Text style={styles.catLabelEN}>{cat.labelEN}</Text>
                  </Text>
                  <View style={styles.iconRow}>
                    {catIcons.map(icon => {
                      const isTaken = takenIconIds.includes(icon.id);
                      const isSelected = selected === icon.id;
                      return (
                        <View key={icon.id} style={styles.iconWrapper}>
                          <PlayerIcon
                            iconId={icon.id}
                            size={60}
                            selected={isSelected}
                            onPress={() => setSelected(icon.id)}
                          />
                          {isTaken && !isSelected && (
                            <View style={styles.takenOverlay}>
                              <Text style={styles.takenText}>✕</Text>
                            </View>
                          )}
                        </View>
                      );
                    })}
                  </View>
                </View>
              );
            })}
            <View style={{ height: Spacing.xxl }} />
          </ScrollView>

          {/* Confirm */}
          <View style={styles.footer}>
            <View style={styles.divider} />
            <Pressable onPress={() => onConfirm(selected)} style={styles.confirmBtn}>
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
  titleJP: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.xl,
    color: Colors.textPrimary,
    textAlign: 'center',
  },
  titleEN: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
    textAlign: 'center',
    letterSpacing: 2,
    marginTop: 2,
  },
  playerName: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.md,
    color: Colors.accentGold,
    textAlign: 'center',
    marginTop: Spacing.xs,
  },
  divider: {
    height: 1,
    backgroundColor: Colors.borderGlow,
    marginHorizontal: Spacing.lg,
    marginVertical: Spacing.md,
  },
  scroll: {
    paddingHorizontal: Spacing.lg,
  },
  category: {
    marginBottom: Spacing.lg,
  },
  catLabel: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.sm,
    color: Colors.accentGold,
    marginBottom: Spacing.sm,
  },
  catLabelEN: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
    letterSpacing: 2,
  },
  iconRow: {
    flexDirection: 'row',
    gap: Spacing.md,
    flexWrap: 'wrap',
  },
  iconWrapper: {
    position: 'relative',
  },
  takenOverlay: {
    position: 'absolute',
    inset: 0,
    backgroundColor: 'rgba(10,14,26,0.6)',
    borderRadius: 30,
    alignItems: 'center',
    justifyContent: 'center',
  },
  takenText: {
    color: Colors.textSecondary,
    fontSize: FontSize.lg,
  },
  footer: {
    paddingHorizontal: Spacing.lg,
    paddingBottom: Spacing.xl,
  },
  confirmBtn: {
    borderRadius: Radius.button,
    overflow: 'hidden',
  },
  confirmGradient: {
    paddingVertical: Spacing.md,
    alignItems: 'center',
  },
  confirmJP: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.lg,
    color: Colors.bgDeep,
  },
  confirmEN: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.bgDeep,
    letterSpacing: 3,
  },
});
