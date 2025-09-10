import React, {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  useCallback,
} from "react";
import { useColorScheme } from "react-native";

import { lightTheme, darkTheme } from "@/constants/theme";
import { StorageService } from "@/services/storage";
import { ThemeColors } from "@/types";

export type ThemeMode = "light" | "dark" | "system";

type ThemeContextValue = {
  theme: ThemeColors;
  themeMode: ThemeMode;
  isDark: boolean;
  toggleTheme: (_mode: ThemeMode) => Promise<void> | void;
};

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const systemColorScheme = useColorScheme();
  const [themeMode, setThemeMode] = useState<ThemeMode>("system");

  useEffect(() => {
    const load = async () => {
      const preferences = await StorageService.getUserPreferences();
      if (preferences?.theme) {
        setThemeMode(preferences.theme);
      }
    };
    load();
  }, []);

  const isDark = useMemo(() => {
    if (themeMode === "system") {
      return systemColorScheme === "dark";
    }
    return themeMode === "dark";
  }, [themeMode, systemColorScheme]);

  const theme = useMemo<ThemeColors>(
    () => (isDark ? darkTheme : lightTheme),
    [isDark],
  );

  const toggleTheme = useCallback(async (_mode: ThemeMode) => {
    setThemeMode(_mode);
    const preferences = await StorageService.getUserPreferences();
    if (preferences) {
      preferences.theme = _mode;
      await StorageService.saveUserPreferences(preferences);
    }
  }, []);

  const value = useMemo(
    () => ({ theme, themeMode, isDark, toggleTheme }),
    [theme, themeMode, isDark, toggleTheme],
  );

  return (
    <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextValue => {
  const ctx = useContext(ThemeContext);
  if (!ctx) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return ctx;
};
