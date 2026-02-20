export const Colors = {
  // Backgrounds
  bgDeep: '#0A0E1A',
  bgSurface: '#111827',
  bgSurface2: '#1C2333',

  // Accents
  accentGold: '#C9A84C',
  accentGoldLight: '#F0D080',
  accentRed: '#B33040',
  accentRedLight: '#E05060',
  accentTeal: '#2DD4BF',

  // Text
  textPrimary: '#EDE8DA',
  textSecondary: '#8A8F9E',
  textKanji: '#C9A84C',

  // Borders / decorative
  borderGlow: 'rgba(201,168,76,0.25)',
  tileBg: '#F5EDD5',
  tileBorder: '#8B7355',

  // Utility
  white: '#FFFFFF',
  transparent: 'transparent',
};

export const Fonts = {
  serif: 'NotoSerifJP_700Bold',
  score: 'BebasNeue_400Regular',
  sans: 'NotoSansJP_400Regular',
  sansBold: 'NotoSansJP_600SemiBold',
};

export const Radius = {
  card: 12,
  icon: 28,
  modal: 20,
  button: 10,
  tile: 6,
  badge: 4,
};

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 12,
  lg: 16,
  xl: 24,
  xxl: 32,
};

export const FontSize = {
  xs: 10,
  sm: 12,
  md: 14,
  lg: 16,
  xl: 20,
  xxl: 28,
  score: 36,
  scoreXL: 48,
};

// Gold gradient colours for LinearGradient
export const GoldGradient = ['#A07830', '#E0C060'] as const;

// Divider style helper
export const Divider = {
  height: 1,
  backgroundColor: 'rgba(201,168,76,0.3)',
  marginVertical: Spacing.md,
};
