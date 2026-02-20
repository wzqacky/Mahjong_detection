import React from 'react';
import { View, Text, StyleSheet, Pressable } from 'react-native';
import { Colors, Fonts, Radius, FontSize } from '../constants/theme';

interface Props {
  wind: 'East' | 'South' | 'West' | 'North';
  isDealer?: boolean;
  onPress?: () => void;
  size?: 'sm' | 'md';
}

const WIND_KANJI: Record<string, string> = {
  East: '東',
  South: '南',
  West: '西',
  North: '北',
};

export default function WindBadge({ wind, isDealer = false, onPress, size = 'md' }: Props) {
  const isSmall = size === 'sm';

  const badge = (
    <View
      style={[
        styles.badge,
        isDealer ? styles.dealerBadge : styles.normalBadge,
        isSmall && styles.badgeSm,
      ]}
    >
      {isDealer && <Text style={[styles.dealerDot, isSmall && styles.dotSm]}>◆</Text>}
      <Text
        style={[
          styles.windText,
          isDealer ? styles.dealerText : styles.normalText,
          isSmall && styles.textSm,
        ]}
      >
        {WIND_KANJI[wind]}
      </Text>
    </View>
  );

  if (onPress) {
    return <Pressable onPress={onPress}>{badge}</Pressable>;
  }
  return badge;
}

const styles = StyleSheet.create({
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 6,
    paddingVertical: 3,
    borderRadius: Radius.badge,
    gap: 2,
  },
  dealerBadge: {
    backgroundColor: 'rgba(179,48,64,0.2)',
    borderWidth: 1,
    borderColor: Colors.accentRed,
  },
  normalBadge: {
    backgroundColor: 'rgba(201,168,76,0.1)',
    borderWidth: 1,
    borderColor: Colors.borderGlow,
  },
  badgeSm: {
    paddingHorizontal: 4,
    paddingVertical: 2,
  },
  dealerDot: {
    color: Colors.accentRed,
    fontSize: FontSize.xs,
  },
  dotSm: {
    fontSize: 8,
  },
  windText: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.sm,
  },
  dealerText: {
    color: Colors.accentRed,
  },
  normalText: {
    color: Colors.accentGold,
  },
  textSm: {
    fontSize: FontSize.xs,
  },
});
