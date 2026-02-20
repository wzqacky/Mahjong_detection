import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { Colors, Fonts, Spacing, FontSize } from '../constants/theme';
import { YakuItem } from '../types';

interface Props {
  yaku: YakuItem[];
}

function YakuRow({ item, delay }: { item: YakuItem; delay: number }) {
  const opacity = useRef(new Animated.Value(0)).current;
  const translateX = useRef(new Animated.Value(-20)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(opacity, {
        toValue: 1,
        duration: 250,
        delay,
        useNativeDriver: true,
      }),
      Animated.timing(translateX, {
        toValue: 0,
        duration: 250,
        delay,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  return (
    <Animated.View
      style={[styles.row, { opacity, transform: [{ translateX }] }]}
    >
      <View style={styles.nameBlock}>
        <Text style={styles.nameZH}>{item.name_zh}</Text>
        <Text style={styles.nameEN}>{item.name_en}</Text>
      </View>
      {item.is_yakuman ? (
        <Text style={styles.yakuman}>役満</Text>
      ) : (
        <Text style={styles.han}>{item.han}翻</Text>
      )}
    </Animated.View>
  );
}

export default function YakuList({ yaku }: Props) {
  return (
    <View style={styles.container}>
      {yaku.map((item, i) => (
        <YakuRow key={item.code} item={item} delay={i * 150} />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 6,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: Spacing.xs,
  },
  nameBlock: {
    flexDirection: 'row',
    alignItems: 'baseline',
    gap: Spacing.sm,
    flex: 1,
  },
  nameZH: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.md,
    color: Colors.textPrimary,
  },
  nameEN: {
    fontFamily: Fonts.sans,
    fontSize: FontSize.xs,
    color: Colors.textSecondary,
  },
  han: {
    fontFamily: Fonts.sansBold,
    fontSize: FontSize.sm,
    color: Colors.accentGold,
  },
  yakuman: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.sm,
    color: Colors.accentRedLight,
  },
});
