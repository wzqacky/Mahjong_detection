import React, { useEffect, useRef } from 'react';
import { View, Text, Animated, StyleSheet } from 'react-native';
import { Colors, Fonts, FontSize, Radius } from '../constants/theme';

interface Props {
  visible: boolean;
}

export default function RiichiBadge({ visible }: Props) {
  const opacity = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(opacity, {
      toValue: visible ? 1 : 0,
      duration: 200,
      useNativeDriver: true,
    }).start();
  }, [visible]);

  return (
    <Animated.View style={[styles.badge, { opacity }]}>
      <Text style={styles.text}>立直</Text>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  badge: {
    backgroundColor: 'rgba(45,212,191,0.15)',
    borderWidth: 1,
    borderColor: Colors.accentTeal,
    borderRadius: Radius.badge,
    paddingHorizontal: 6,
    paddingVertical: 2,
    alignSelf: 'flex-start',
  },
  text: {
    fontFamily: Fonts.serif,
    fontSize: FontSize.xs,
    color: Colors.accentTeal,
  },
});
