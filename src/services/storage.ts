import AsyncStorage from "@react-native-async-storage/async-storage";

import { PasswordEntry, UserPreferences, User, AdConfig } from "@/types";

const STORAGE_KEYS = {
  PASSWORD_HISTORY: "@SecurePass:passwordHistory",
  USER_PREFERENCES: "@SecurePass:userPreferences",
  USER_DATA: "@SecurePass:userData",
  AD_CONFIG: "@SecurePass:adConfig",
  FIRST_LAUNCH: "@SecurePass:firstLaunch",
  PREMIUM_STATUS: "@SecurePass:premiumStatus",
  LAST_SYNC: "@SecurePass:lastSync",
};

export class StorageService {
  // Password History
  static async getPasswordHistory(): Promise<PasswordEntry[]> {
    try {
      const data = await AsyncStorage.getItem(STORAGE_KEYS.PASSWORD_HISTORY);
      if (data) {
        const history = JSON.parse(data);
        // Convert timestamp strings back to Date objects
        return history.map(
          (entry: PasswordEntry & { timestamp: string | Date }) => ({
            ...entry,
            timestamp: new Date(entry.timestamp),
          }),
        );
      }
      return [];
    } catch (error) {
      console.error("Error loading password history:", error);
      return [];
    }
  }

  static async savePasswordHistory(history: PasswordEntry[]): Promise<void> {
    try {
      await AsyncStorage.setItem(
        STORAGE_KEYS.PASSWORD_HISTORY,
        JSON.stringify(history),
      );
    } catch (error) {
      console.error("Error saving password history:", error);
      throw error;
    }
  }

  static async addPasswordToHistory(
    entry: PasswordEntry,
    maxCount: number = 10,
  ): Promise<void> {
    try {
      const history = await this.getPasswordHistory();
      history.unshift(entry);

      // Limit history size for free users
      if (history.length > maxCount) {
        history.splice(maxCount);
      }

      await this.savePasswordHistory(history);
    } catch (error) {
      console.error("Error adding password to history:", error);
      throw error;
    }
  }

  static async removePasswordFromHistory(id: string): Promise<void> {
    try {
      const history = await this.getPasswordHistory();
      const filtered = history.filter((entry) => entry.id !== id);
      await this.savePasswordHistory(filtered);
    } catch (error) {
      console.error("Error removing password from history:", error);
      throw error;
    }
  }

  static async clearPasswordHistory(): Promise<void> {
    try {
      await AsyncStorage.removeItem(STORAGE_KEYS.PASSWORD_HISTORY);
    } catch (error) {
      console.error("Error clearing password history:", error);
      throw error;
    }
  }

  // User Preferences
  static async getUserPreferences(): Promise<UserPreferences | null> {
    try {
      const data = await AsyncStorage.getItem(STORAGE_KEYS.USER_PREFERENCES);
      return data ? JSON.parse(data) : null;
    } catch (error) {
      console.error("Error loading user preferences:", error);
      return null;
    }
  }

  static async saveUserPreferences(
    preferences: UserPreferences,
  ): Promise<void> {
    try {
      await AsyncStorage.setItem(
        STORAGE_KEYS.USER_PREFERENCES,
        JSON.stringify(preferences),
      );
    } catch (error) {
      console.error("Error saving user preferences:", error);
      throw error;
    }
  }

  // User Data
  static async getUserData(): Promise<User | null> {
    try {
      const data = await AsyncStorage.getItem(STORAGE_KEYS.USER_DATA);
      if (data) {
        const user = JSON.parse(data);
        // Convert date strings back to Date objects
        return {
          ...user,
          createdAt: new Date(user.createdAt),
          lastSyncAt: user.lastSyncAt ? new Date(user.lastSyncAt) : undefined,
          premiumExpiresAt: user.premiumExpiresAt
            ? new Date(user.premiumExpiresAt)
            : undefined,
        };
      }
      return null;
    } catch (error) {
      console.error("Error loading user data:", error);
      return null;
    }
  }

  static async saveUserData(user: User): Promise<void> {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.USER_DATA, JSON.stringify(user));
    } catch (error) {
      console.error("Error saving user data:", error);
      throw error;
    }
  }

  static async clearUserData(): Promise<void> {
    try {
      await AsyncStorage.removeItem(STORAGE_KEYS.USER_DATA);
    } catch (error) {
      console.error("Error clearing user data:", error);
      throw error;
    }
  }

  // Ad Configuration
  static async getAdConfig(): Promise<AdConfig | null> {
    try {
      const data = await AsyncStorage.getItem(STORAGE_KEYS.AD_CONFIG);
      if (data) {
        const config = JSON.parse(data);
        return {
          ...config,
          lastInterstitialShown: config.lastInterstitialShown
            ? new Date(config.lastInterstitialShown)
            : undefined,
        };
      }
      return null;
    } catch (error) {
      console.error("Error loading ad config:", error);
      return null;
    }
  }

  static async saveAdConfig(config: AdConfig): Promise<void> {
    try {
      await AsyncStorage.setItem(
        STORAGE_KEYS.AD_CONFIG,
        JSON.stringify(config),
      );
    } catch (error) {
      console.error("Error saving ad config:", error);
      throw error;
    }
  }

  // Premium Status
  static async getPremiumStatus(): Promise<boolean> {
    try {
      const user = await this.getUserData();
      if (!user) return false;

      if (user.isPremium) {
        // Check if premium has expired
        if (user.premiumExpiresAt) {
          return new Date() < new Date(user.premiumExpiresAt);
        }
        return true; // Lifetime premium
      }
      return false;
    } catch (error) {
      console.error("Error checking premium status:", error);
      return false;
    }
  }

  static async setPremiumStatus(
    isPremium: boolean,
    expiresAt?: Date,
  ): Promise<void> {
    try {
      const user = await this.getUserData();
      if (user) {
        user.isPremium = isPremium;
        user.premiumExpiresAt = expiresAt;
        await this.saveUserData(user);
      }
    } catch (error) {
      console.error("Error setting premium status:", error);
      throw error;
    }
  }

  // First Launch
  static async isFirstLaunch(): Promise<boolean> {
    try {
      const hasLaunched = await AsyncStorage.getItem(STORAGE_KEYS.FIRST_LAUNCH);
      return hasLaunched === null;
    } catch (error) {
      console.error("Error checking first launch:", error);
      return false;
    }
  }

  static async setFirstLaunchComplete(): Promise<void> {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.FIRST_LAUNCH, "true");
    } catch (error) {
      console.error("Error setting first launch complete:", error);
      throw error;
    }
  }

  // Last Sync
  static async getLastSyncTime(): Promise<Date | null> {
    try {
      const data = await AsyncStorage.getItem(STORAGE_KEYS.LAST_SYNC);
      return data ? new Date(data) : null;
    } catch (error) {
      console.error("Error getting last sync time:", error);
      return null;
    }
  }

  static async setLastSyncTime(date: Date): Promise<void> {
    try {
      await AsyncStorage.setItem(STORAGE_KEYS.LAST_SYNC, date.toISOString());
    } catch (error) {
      console.error("Error setting last sync time:", error);
      throw error;
    }
  }

  // Clear All Data
  static async clearAllData(): Promise<void> {
    try {
      const keys = Object.values(STORAGE_KEYS);
      await AsyncStorage.multiRemove(keys);
    } catch (error) {
      console.error("Error clearing all data:", error);
      throw error;
    }
  }

  // Export/Import for backup
  static async exportData(): Promise<string> {
    try {
      const data = {
        passwordHistory: await this.getPasswordHistory(),
        userPreferences: await this.getUserPreferences(),
        userData: await this.getUserData(),
        adConfig: await this.getAdConfig(),
      };
      return JSON.stringify(data);
    } catch (error) {
      console.error("Error exporting data:", error);
      throw error;
    }
  }

  static async importData(jsonData: string): Promise<void> {
    try {
      const data = JSON.parse(jsonData);

      if (data.passwordHistory) {
        await this.savePasswordHistory(data.passwordHistory);
      }
      if (data.userPreferences) {
        await this.saveUserPreferences(data.userPreferences);
      }
      if (data.userData) {
        await this.saveUserData(data.userData);
      }
      if (data.adConfig) {
        await this.saveAdConfig(data.adConfig);
      }
    } catch (error) {
      console.error("Error importing data:", error);
      throw error;
    }
  }
}
