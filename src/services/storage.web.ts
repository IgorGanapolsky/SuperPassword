// Web-specific storage implementation using localStorage
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
  private static getItem(key: string): string | null {
    return localStorage.getItem(key);
  }

  private static setItem(key: string, value: string): void {
    localStorage.setItem(key, value);
  }

  private static removeItem(key: string): void {
    localStorage.removeItem(key);
  }

  // Password History
  static async getPasswordHistory(): Promise<PasswordEntry[]> {
    try {
      const data = this.getItem(STORAGE_KEYS.PASSWORD_HISTORY);
      if (data) {
        const history = JSON.parse(data);
        return history.map((entry: any) => ({
          ...entry,
          timestamp: new Date(entry.timestamp),
        }));
      }
      return [];
    } catch (error) {
      console.error("Error loading password history:", error);
      return [];
    }
  }

  static async savePasswordHistory(history: PasswordEntry[]): Promise<void> {
    try {
      this.setItem(STORAGE_KEYS.PASSWORD_HISTORY, JSON.stringify(history));
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
      if (history.length > maxCount) {
        history.splice(maxCount);
      }
      await this.savePasswordHistory(history);
    } catch (error) {
      console.error("Error adding password to history:", error);
      throw error;
    }
  }

  // User Preferences
  static async getUserPreferences(): Promise<UserPreferences | null> {
    try {
      const data = this.getItem(STORAGE_KEYS.USER_PREFERENCES);
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
      this.setItem(STORAGE_KEYS.USER_PREFERENCES, JSON.stringify(preferences));
    } catch (error) {
      console.error("Error saving user preferences:", error);
      throw error;
    }
  }

  // First Launch
  static async isFirstLaunch(): Promise<boolean> {
    try {
      const hasLaunched = this.getItem(STORAGE_KEYS.FIRST_LAUNCH);
      return hasLaunched === null;
    } catch (error) {
      console.error("Error checking first launch:", error);
      return false;
    }
  }

  static async setFirstLaunchComplete(): Promise<void> {
    try {
      this.setItem(STORAGE_KEYS.FIRST_LAUNCH, "true");
    } catch (error) {
      console.error("Error setting first launch complete:", error);
      throw error;
    }
  }

  // Ad Config
  static async saveAdConfig(config: AdConfig): Promise<void> {
    try {
      this.setItem(STORAGE_KEYS.AD_CONFIG, JSON.stringify(config));
    } catch (error) {
      console.error("Error saving ad config:", error);
      throw error;
    }
  }

  // Premium Status
  static async getPremiumStatus(): Promise<boolean> {
    return false; // Web version is always free
  }

  static async clearAllData(): Promise<void> {
    try {
      Object.values(STORAGE_KEYS).forEach((key) => this.removeItem(key));
    } catch (error) {
      console.error("Error clearing all data:", error);
      throw error;
    }
  }
}
