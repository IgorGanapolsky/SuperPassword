import AsyncStorage from "@react-native-async-storage/async-storage";
import { StorageService } from "../storage";
import { PasswordEntry, UserPreferences, User, AdConfig } from "@/types";

// Mock AsyncStorage
jest.mock("@react-native-async-storage/async-storage", () => ({
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  multiRemove: jest.fn(),
}));

describe("StorageService", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe("Password History", () => {
    const mockEntry: PasswordEntry = {
      id: "123",
      password: "testPass123",
      timestamp: new Date("2025-01-01"),
      label: "Test Password",
    };

    it("gets password history", async () => {
      const mockData = [
        { ...mockEntry, timestamp: mockEntry.timestamp.toISOString() },
      ];
      (AsyncStorage.getItem as jest.Mock).mockResolvedValueOnce(
        JSON.stringify(mockData),
      );

      const result = await StorageService.getPasswordHistory();
      expect(result).toEqual([mockEntry]);
      expect(AsyncStorage.getItem).toHaveBeenCalledWith(
        "@SecurePass:passwordHistory",
      );
    });

    it("returns empty array when no history exists", async () => {
      (AsyncStorage.getItem as jest.Mock).mockResolvedValueOnce(null);

      const result = await StorageService.getPasswordHistory();
      expect(result).toEqual([]);
    });

    it("saves password history", async () => {
      await StorageService.savePasswordHistory([mockEntry]);
      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        "@SecurePass:passwordHistory",
        JSON.stringify([mockEntry]),
      );
    });

    it("adds password to history with limit", async () => {
      const existingHistory = Array(10)
        .fill(mockEntry)
        .map((entry, i) => ({
          ...entry,
          id: `${i}`,
        }));
      (AsyncStorage.getItem as jest.Mock).mockResolvedValueOnce(
        JSON.stringify(existingHistory),
      );

      const newEntry = { ...mockEntry, id: "new" };
      await StorageService.addPasswordToHistory(newEntry, 10);

      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        "@SecurePass:passwordHistory",
        expect.any(String),
      );
      const savedData = JSON.parse(
        (AsyncStorage.setItem as jest.Mock).mock.calls[0][1],
      );
      expect(savedData).toHaveLength(10);
      expect(savedData[0].id).toBe("new");
    });

    it("removes password from history", async () => {
      const history = [
        { ...mockEntry, id: "1" },
        { ...mockEntry, id: "2" },
      ];
      (AsyncStorage.getItem as jest.Mock).mockResolvedValueOnce(
        JSON.stringify(history),
      );

      await StorageService.removePasswordFromHistory("1");

      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        "@SecurePass:passwordHistory",
        expect.any(String),
      );
      const savedData = JSON.parse(
        (AsyncStorage.setItem as jest.Mock).mock.calls[0][1],
      );
      expect(savedData).toHaveLength(1);
      expect(savedData[0].id).toBe("2");
    });

    it("clears password history", async () => {
      await StorageService.clearPasswordHistory();
      expect(AsyncStorage.removeItem).toHaveBeenCalledWith(
        "@SecurePass:passwordHistory",
      );
    });
  });

  describe("User Preferences", () => {
    const mockPreferences: UserPreferences = {
      theme: "dark",
      defaultLength: 12,
      useLowercase: true,
      useUppercase: true,
      useNumbers: true,
      useSymbols: true,
    };

    it("gets user preferences", async () => {
      (AsyncStorage.getItem as jest.Mock).mockResolvedValueOnce(
        JSON.stringify(mockPreferences),
      );

      const result = await StorageService.getUserPreferences();
      expect(result).toEqual(mockPreferences);
    });

    it("returns null when no preferences exist", async () => {
      (AsyncStorage.getItem as jest.Mock).mockResolvedValueOnce(null);

      const result = await StorageService.getUserPreferences();
      expect(result).toBeNull();
    });

    it("saves user preferences", async () => {
      await StorageService.saveUserPreferences(mockPreferences);
      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        "@SecurePass:userPreferences",
        JSON.stringify(mockPreferences),
      );
    });
  });

  describe("User Data", () => {
    const mockUser: User = {
      id: "123",
      email: "test@example.com",
      isPremium: false,
      createdAt: new Date("2025-01-01"),
    };

    it("gets user data", async () => {
      const storedUser = {
        ...mockUser,
        createdAt: mockUser.createdAt.toISOString(),
      };
      (AsyncStorage.getItem as jest.Mock).mockResolvedValueOnce(
        JSON.stringify(storedUser),
      );

      const result = await StorageService.getUserData();
      expect(result).toEqual(mockUser);
    });

    it("returns null when no user data exists", async () => {
      (AsyncStorage.getItem as jest.Mock).mockResolvedValueOnce(null);

      const result = await StorageService.getUserData();
      expect(result).toBeNull();
    });

    it("saves user data", async () => {
      await StorageService.saveUserData(mockUser);
      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        "@SecurePass:userData",
        JSON.stringify(mockUser),
      );
    });

    it("clears user data", async () => {
      await StorageService.clearUserData();
      expect(AsyncStorage.removeItem).toHaveBeenCalledWith(
        "@SecurePass:userData",
      );
    });
  });

  describe("Premium Status", () => {
    const mockUser: User = {
      id: "123",
      email: "test@example.com",
      isPremium: true,
      createdAt: new Date("2025-01-01"),
    };

    it("returns true for lifetime premium user", async () => {
      (AsyncStorage.getItem as jest.Mock).mockResolvedValueOnce(
        JSON.stringify(mockUser),
      );

      const result = await StorageService.getPremiumStatus();
      expect(result).toBe(true);
    });

    it("returns false for expired premium", async () => {
      const expiredUser = {
        ...mockUser,
        premiumExpiresAt: new Date("2024-01-01"),
      };
      (AsyncStorage.getItem as jest.Mock).mockResolvedValueOnce(
        JSON.stringify(expiredUser),
      );

      const result = await StorageService.getPremiumStatus();
      expect(result).toBe(false);
    });

    it("sets premium status", async () => {
      (AsyncStorage.getItem as jest.Mock).mockResolvedValueOnce(
        JSON.stringify(mockUser),
      );
      const expiryDate = new Date("2026-01-01");

      await StorageService.setPremiumStatus(true, expiryDate);

      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        "@SecurePass:userData",
        expect.any(String),
      );
      const savedData = JSON.parse(
        (AsyncStorage.setItem as jest.Mock).mock.calls[0][1],
      );
      expect(savedData.isPremium).toBe(true);
      expect(savedData.premiumExpiresAt).toBe(expiryDate.toISOString());
    });
  });

  describe("First Launch", () => {
    it("returns true on first launch", async () => {
      (AsyncStorage.getItem as jest.Mock).mockResolvedValueOnce(null);

      const result = await StorageService.isFirstLaunch();
      expect(result).toBe(true);
    });

    it("returns false after first launch", async () => {
      (AsyncStorage.getItem as jest.Mock).mockResolvedValueOnce("true");

      const result = await StorageService.isFirstLaunch();
      expect(result).toBe(false);
    });

    it("sets first launch complete", async () => {
      await StorageService.setFirstLaunchComplete();
      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        "@SecurePass:firstLaunch",
        "true",
      );
    });
  });

  describe("Data Import/Export", () => {
    const mockData = {
      passwordHistory: [
        {
          id: "123",
          password: "test123",
          timestamp: new Date("2025-01-01").toISOString(),
        },
      ],
      userPreferences: {
        theme: "dark",
        defaultLength: 12,
      },
      userData: {
        id: "123",
        email: "test@example.com",
        isPremium: true,
        createdAt: new Date("2025-01-01").toISOString(),
      },
      adConfig: {
        lastInterstitialShown: new Date("2025-01-01").toISOString(),
      },
    };

    it("exports data correctly", async () => {
      (AsyncStorage.getItem as jest.Mock)
        .mockResolvedValueOnce(JSON.stringify(mockData.passwordHistory))
        .mockResolvedValueOnce(JSON.stringify(mockData.userPreferences))
        .mockResolvedValueOnce(JSON.stringify(mockData.userData))
        .mockResolvedValueOnce(JSON.stringify(mockData.adConfig));

      const result = await StorageService.exportData();
      const exported = JSON.parse(result);

      expect(exported).toEqual(mockData);
    });

    it("imports data correctly", async () => {
      await StorageService.importData(JSON.stringify(mockData));

      expect(AsyncStorage.setItem).toHaveBeenCalledTimes(4);
      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        "@SecurePass:passwordHistory",
        expect.any(String),
      );
      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        "@SecurePass:userPreferences",
        expect.any(String),
      );
      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        "@SecurePass:userData",
        expect.any(String),
      );
      expect(AsyncStorage.setItem).toHaveBeenCalledWith(
        "@SecurePass:adConfig",
        expect.any(String),
      );
    });
  });

  describe("Clear All Data", () => {
    it("removes all storage keys", async () => {
      await StorageService.clearAllData();
      expect(AsyncStorage.multiRemove).toHaveBeenCalledWith([
        "@SecurePass:passwordHistory",
        "@SecurePass:userPreferences",
        "@SecurePass:userData",
        "@SecurePass:adConfig",
        "@SecurePass:firstLaunch",
        "@SecurePass:premiumStatus",
        "@SecurePass:lastSync",
      ]);
    });
  });
});
