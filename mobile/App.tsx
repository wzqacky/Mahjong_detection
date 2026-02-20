import 'react-native-gesture-handler';
import React from 'react';
import { StatusBar } from 'expo-status-bar';
import { GestureHandlerRootView } from 'react-native-gesture-handler';
import { BottomSheetModalProvider } from '@gorhom/bottom-sheet';
import { StyleSheet } from 'react-native';
import {
  useFonts,
  NotoSerifJP_700Bold,
} from '@expo-google-fonts/noto-serif-jp';
import {
  BebasNeue_400Regular,
} from '@expo-google-fonts/bebas-neue';
import {
  NotoSansJP_400Regular,
  NotoSansJP_600SemiBold,
} from '@expo-google-fonts/noto-sans-jp';

import AppNavigator from './src/navigation/AppNavigator';
import { Colors } from './src/constants/theme';

export default function App() {
  const [fontsLoaded] = useFonts({
    NotoSerifJP_700Bold,
    BebasNeue_400Regular,
    NotoSansJP_400Regular,
    NotoSansJP_600SemiBold,
  });

  if (!fontsLoaded) {
    return null;
  }

  return (
    <GestureHandlerRootView style={styles.root}>
      <BottomSheetModalProvider>
        <StatusBar style="light" backgroundColor={Colors.bgDeep} />
        <AppNavigator />
      </BottomSheetModalProvider>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  root: {
    flex: 1,
    backgroundColor: Colors.bgDeep,
  },
});
