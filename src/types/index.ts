export interface PasswordOptions {
  length: number;
  includeUppercase: boolean;
  includeLowercase: boolean;
  includeNumbers: boolean;
  includeSymbols: boolean;
  excludeAmbiguous: boolean;
  customCharacters?: string;
  excludeCharacters?: string;
  passwordType: "numeric" | "alphanumeric" | "alphabetical";
}

export interface PasswordEntry {
  id: string;
  password: string;
  timestamp: Date;
  strength: PasswordStrength;
  options: PasswordOptions;
  isFavorite?: boolean;
}

// eslint-disable-next-line no-unused-vars
export enum PasswordStrength {
  VeryWeak = 0,
  Weak = 1,
  Fair = 2,
  Good = 3,
  Strong = 4,
  VeryStrong = 5,
}

export interface User {
  id: string;
  email: string;
  displayName?: string;
  isPremium: boolean;
  premiumExpiresAt?: Date;
  trialUsed: boolean;
  passwordCount: number;
  createdAt: Date;
  lastSyncAt?: Date;
}

export interface UserPreferences {
  theme: "light" | "dark" | "system";
  defaultOptions: PasswordOptions;
  autoSave: boolean;
  hapticFeedback: boolean;
  showPasswordStrength: boolean;
  quickCopyEnabled: boolean;
}

export interface AdConfig {
  showBanner: boolean;
  interstitialFrequency: number;
  lastInterstitialShown?: Date;
  passwordsGeneratedSinceAd: number;
}

export interface PricingTier {
  id: string;
  price: number;
  currency: string;
  features: string[];
  isActive: boolean;
}

export interface AppState {
  user: User | null;
  preferences: UserPreferences;
  passwordHistory: PasswordEntry[];
  isLoading: boolean;
  error: string | null;
  adConfig: AdConfig;
  currentPricingTier?: PricingTier;
}

export interface ThemeColors {
  primary: string;
  primaryDark: string;
  accent: string;
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  error: string;
  success: string;
  warning: string;
  info: string;
  divider: string;
  gradient: {
    start: string;
    end: string;
  };
}

export type NavigationParamList = {
  Home: undefined;
  History: undefined;
  Settings: undefined;
  Premium:
    | {
        source?: "menu" | "limit" | "feature";
      }
    | undefined;
  About: undefined;
  PrivacyPolicy: undefined;
  TermsOfService: undefined;
  MainTabs: undefined;
};

// Narrowed navigator param lists for specific navigators
export type BottomTabParamList = {
  Home: undefined;
  History: undefined;
  Settings: undefined;
  Premium: { source?: "menu" | "limit" | "feature" } | undefined;
};

export type RootStackParamList = {
  MainTabs: undefined;
};
