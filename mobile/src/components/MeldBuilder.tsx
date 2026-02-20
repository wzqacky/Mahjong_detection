import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  Pressable,
  Modal,
  ScrollView,
  Switch,
} from 'react-native';
import { Colors, Fonts, Spacing, FontSize, Radius } from '../constants/theme';
import { MeldEntry } from '../types';
import TilePicker from './TilePicker';

interface Props {
  melds: MeldEntry[];
  onAdd: (meld: MeldEntry) => void;
  onRemove: (index: number) => void;
}

const TILE_DISPLAY: Record<string, string> = {
  EW: '東', SW: '南', WW: '西', NW: '北',
  WD: '白', GD: '發', RD: '中',
};

function tileLabel(t: string): string {
  if (TILE_DISPLAY[t]) return TILE_DISPLAY[t];
  const suitMap: Record<string, string> = { D: '萬', B: '筒', C: '索' };
  return `${t.slice(0, -1)}${suitMap[t.slice(-1)] ?? ''}`;
}

export default function MeldBuilder({ melds, onAdd, onRemove }: Props) {
  const [addingMeld, setAddingMeld] = useState(false);
  const [meldCounts, setMeldCounts] = useState<Record<string, number>>({});
  const [meldRed, setMeldRed] = useState<Record<string, boolean>>({});
  const [isOpen, setIsOpen] = useState(true);

  const meldTotal = Object.values(meldCounts).reduce((a, b) => a + b, 0);

  const handleTilePress = (tile: string) => {
    const cur = meldCounts[tile] ?? 0;
    if (meldTotal >= 4 || cur >= 4) return;
    setMeldCounts(prev => ({ ...prev, [tile]: cur + 1 }));
  };

  const handleToggleRed = (tile: string) => {
    setMeldRed(prev => ({ ...prev, [tile]: !prev[tile] }));
  };

  const handleConfirmMeld = () => {
    const tiles: string[] = [];
    Object.entries(meldCounts).forEach(([tile, count]) => {
      for (let i = 0; i < count; i++) tiles.push(tile);
    });
    if (tiles.length < 3) return;
    onAdd({ tiles, isOpen });
    setMeldCounts({});
    setMeldRed({});
    setIsOpen(true);
    setAddingMeld(false);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.sectionLabel}>── MELDS ──</Text>

      {melds.map((meld, idx) => (
        <View key={idx} style={styles.meldRow}>
          <Text style={styles.meldTiles}>
            {meld.tiles.map(tileLabel).join(' ')}
          </Text>
          <Text style={styles.meldType}>{meld.isOpen ? 'Open' : 'Closed'}</Text>
          <Pressable onPress={() => onRemove(idx)} style={styles.removeBtn}>
            <Text style={styles.removeBtnText}>✕</Text>
          </Pressable>
        </View>
      ))}

      <Pressable onPress={() => setAddingMeld(true)} style={styles.addBtn}>
        <Text style={styles.addBtnText}>＋ Add Meld</Text>
      </Pressable>

      {/* Meld input modal */}
      <Modal
        visible={addingMeld}
        transparent
        animationType="slide"
        onRequestClose={() => setAddingMeld(false)}
      >
        <View style={styles.overlay}>
          <View style={styles.sheet}>
            <View style={styles.handle} />
            <Text style={styles.sheetTitle}>Add Meld (3–4 tiles)</Text>

            <View style={styles.openRow}>
              <Text style={styles.openLabel}>Open meld</Text>
              <Switch
                value={isOpen}
                onValueChange={setIsOpen}
                trackColor={{ true: Colors.accentGold }}
                thumbColor={Colors.textPrimary}
              />
            </View>

            <View style={styles.pickerContainer}>
              <TilePicker
                counts={meldCounts}
                redFlags={meldRed}
                totalSelected={meldTotal}
                maxTiles={4}
                onTilePress={handleTilePress}
                onToggleRed={handleToggleRed}
              />
            </View>

            <View style={styles.actionRow}>
              <Pressable onPress={() => setAddingMeld(false)} style={styles.cancelBtn}>
                <Text style={styles.cancelText}>Cancel</Text>
              </Pressable>
              <Pressable
                onPress={handleConfirmMeld}
                style={[styles.confirmBtn, meldTotal < 3 && styles.confirmBtnDisabled]}
                disabled={meldTotal < 3}
              >
                <Text style={styles.confirmText}>Confirm ({meldTotal} tiles)</Text>
              </Pressable>
            </View>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: Spacing.sm,
  },
  sectionLabel: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
    letterSpacing: 2,
    marginBottom: Spacing.sm,
  },
  meldRow: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.bgSurface2,
    borderRadius: Radius.badge,
    padding: Spacing.sm,
    marginBottom: Spacing.xs,
    gap: Spacing.sm,
  },
  meldTiles: {
    flex: 1,
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.sm,
    color: Colors.accentTeal,
  },
  meldType: {
    fontFamily: Fonts.sans,
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
  },
  removeBtn: {
    padding: Spacing.xs,
  },
  removeBtnText: {
    color: Colors.accentRedLight,
    fontSize: FontSize.sm,
  },
  addBtn: {
    borderWidth: 1,
    borderColor: Colors.borderGlow,
    borderStyle: 'dashed',
    borderRadius: Radius.button,
    paddingVertical: Spacing.sm,
    alignItems: 'center',
    marginTop: Spacing.xs,
  },
  addBtnText: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.sm,
    color: Colors.accentGold,
  },
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
    padding: Spacing.lg,
    maxHeight: '70%',
  },
  handle: {
    width: 40,
    height: 4,
    backgroundColor: Colors.borderGlow,
    borderRadius: 2,
    alignSelf: 'center',
    marginBottom: Spacing.md,
  },
  sheetTitle: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.lg,
    color: Colors.textPrimary,
    marginBottom: Spacing.md,
    textAlign: 'center',
  },
  openRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: Spacing.md,
  },
  openLabel: {
    fontFamily: Fonts.sans,
    fontSize: FontSize.md,
    color: Colors.textPrimary,
  },
  pickerContainer: {
    maxHeight: 250,
  },
  actionRow: {
    flexDirection: 'row',
    gap: Spacing.sm,
    marginTop: Spacing.md,
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
    paddingVertical: Spacing.sm,
    borderRadius: Radius.button,
    backgroundColor: Colors.accentGold,
    alignItems: 'center',
  },
  confirmBtnDisabled: {
    opacity: 0.4,
  },
  confirmText: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.sm,
    color: Colors.bgDeep,
  },
});
