import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated, Pressable } from 'react-native';
import { Colors, Fonts, Radius } from '../constants/theme';
import { getIconById } from '../constants/icons';

interface Props {
  iconId: string;
  size?: number;
  selected?: boolean;
  onPress?: () => void;
  disabled?: boolean;
}

export default function PlayerIcon({
  iconId,
  size = 56,
  selected = false,
  onPress,
  disabled = false,
}: Props) {
  const icon = getIconById(iconId);
  const pulseAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    if (selected) {
      const pulse = Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, {
            toValue: 1.15,
            duration: 700,
            useNativeDriver: true,
          }),
          Animated.timing(pulseAnim, {
            toValue: 1,
            duration: 700,
            useNativeDriver: true,
          }),
        ]),
      );
      pulse.start();
      return () => pulse.stop();
    } else {
      pulseAnim.setValue(1);
    }
  }, [selected]);

  const borderRadius = size / 2;
  const fontSize = size * 0.52;
  // Kanji icons are drawn differently — make them slightly smaller
  const isKanji = ['中', '發', '白', '東'].includes(icon.emoji);

  const inner = (
    <Animated.View
      style={[
        styles.container,
        {
          width: size,
          height: size,
          borderRadius,
          transform: [{ scale: pulseAnim }],
          borderColor: selected ? Colors.accentGold : Colors.borderGlow,
          borderWidth: selected ? 2 : 1.5,
        },
      ]}
    >
      <Text
        style={[
          styles.emoji,
          {
            fontSize: isKanji ? fontSize * 0.8 : fontSize,
            fontFamily: isKanji ? Fonts.serif : undefined,
            color: isKanji ? Colors.accentGold : undefined,
          },
        ]}
      >
        {icon.emoji}
      </Text>
    </Animated.View>
  );

  if (onPress) {
    return (
      <Pressable onPress={onPress} disabled={disabled}>
        {inner}
      </Pressable>
    );
  }
  return inner;
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.bgSurface2,
    alignItems: 'center',
    justifyContent: 'center',
    overflow: 'hidden',
  },
  emoji: {
    textAlign: 'center',
    includeFontPadding: false,
  },
});
