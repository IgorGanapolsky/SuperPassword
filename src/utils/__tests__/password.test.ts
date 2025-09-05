import { generatePassword, calculatePasswordStrength } from "../password";

describe("Password Utils", () => {
  describe("generatePassword", () => {
    it("generates password of specified length", () => {
      const password = generatePassword(16);
      expect(password.length).toBe(16);
    });

    it("uses default length when no length specified", () => {
      const password = generatePassword();
      expect(password.length).toBe(12);
    });
  });

  describe("calculatePasswordStrength", () => {
    it("gives high score for strong password", () => {
      const strength = calculatePasswordStrength("Str0ng!P@ssw0rd");
      expect(strength).toBe(6); // Max score
    });

    it("gives low score for weak password", () => {
      const strength = calculatePasswordStrength("password");
      expect(strength).toBe(2); // Length + lowercase
    });

    it("handles empty password", () => {
      const strength = calculatePasswordStrength("");
      expect(strength).toBe(0);
    });
  });
});
