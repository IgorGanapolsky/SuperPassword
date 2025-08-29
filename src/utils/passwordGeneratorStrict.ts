import { PasswordOptions, PasswordStrength } from "@/types";

const CHAR_SETS = {
  UPPERCASE: "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
  LOWERCASE: "abcdefghijklmnopqrstuvwxyz",
  NUMBERS: "0123456789",
  SYMBOLS: "!@#$%^&*()_+-=[]{}|;:,.<>?",
  AMBIGUOUS: "il1Lo0O"
} as const;

class PasswordGenerator {
  private getRandomChar(chars: string): string {
    return chars[Math.floor(Math.random() * chars.length)] ?? chars[0];
  }

  private shuffleString(str: string): string {
    const chars = str.split("");
    for (let i = chars.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      if (chars[i] && chars[j]) {
        const temp = chars[i];
        chars[i] = chars[j];
        chars[j] = temp;
      }
    }
    return chars.join("");
  }

  private escapeRegExp(str: string): string {
    return str.replace(/[.*+?^${}()|[\\]\\]/g, "\\$&");
  }

  private getAvailableChars(options: PasswordOptions): string {
    let chars = "";

    if (options.includeLowercase) chars += CHAR_SETS.LOWERCASE;
    if (options.includeUppercase) chars += CHAR_SETS.UPPERCASE;
    if (options.includeNumbers) chars += CHAR_SETS.NUMBERS;
    if (options.includeSymbols) chars += CHAR_SETS.SYMBOLS;
    if (options.customCharacters) chars += options.customCharacters;

    if (options.excludeCharacters) {
      const excludePattern = new RegExp(
        `[${this.escapeRegExp(options.excludeCharacters)}]`,
        "g"
      );
      chars = chars.replace(excludePattern, "");
    }

    if (options.excludeAmbiguous) {
      const ambiguousPattern = new RegExp(
        `[${this.escapeRegExp(CHAR_SETS.AMBIGUOUS)}]`,
        "g"
      );
      chars = chars.replace(ambiguousPattern, "");
    }

    return chars || CHAR_SETS.LOWERCASE + CHAR_SETS.UPPERCASE + CHAR_SETS.NUMBERS;
  }

  private getRequiredChars(options: PasswordOptions): string[] {
    const chars: string[] = [];

    if (options.includeLowercase) {
      chars.push(this.getRandomChar(CHAR_SETS.LOWERCASE));
    }
    if (options.includeUppercase) {
      chars.push(this.getRandomChar(CHAR_SETS.UPPERCASE));
    }
    if (options.includeNumbers) {
      chars.push(this.getRandomChar(CHAR_SETS.NUMBERS));
    }
    if (options.includeSymbols) {
      chars.push(this.getRandomChar(CHAR_SETS.SYMBOLS));
    }

    return chars;
  }

  generatePassword(options: PasswordOptions): string {
    const availableChars = this.getAvailableChars(options);
    const requiredChars = this.getRequiredChars(options);

    let password = "";
    for (let i = 0; i < options.length; i++) {
      password += this.getRandomChar(availableChars);
    }

    if (options.length >= requiredChars.length && requiredChars.length > 0) {
      const passwordChars = password.split("");
      requiredChars.forEach((char, index) => {
        if (passwordChars[index]) {
          passwordChars[index] = char;
        }
      });
      password = this.shuffleString(passwordChars.join(""));
    }

    return password;
  }

  calculatePasswordStrength(password: string): PasswordStrength {
    if (!password) return PasswordStrength.VeryWeak;

    let strength = 0;
    const length = password.length;

    // Length criteria
    if (length >= 8) strength++;
    if (length >= 12) strength++;
    if (length >= 16) strength++;

    // Character diversity
    if (/[a-z]/.test(password)) strength++;
    if (/[A-Z]/.test(password)) strength++;
    if (/[0-9]/.test(password)) strength++;
    if (/[^a-zA-Z0-9]/.test(password)) strength++;

    // Pattern detection
    if (/(.)\\1{2,}/.test(password)) strength--; // Repeated characters
    if (/^[a-zA-Z]+$/.test(password)) strength--; // Only letters
    if (/^[0-9]+$/.test(password)) strength--; // Only numbers
    if (/^(123|abc|qwerty|password)/i.test(password)) strength -= 2;

    // Calculate entropy-based score
    const charsetSize = this.getCharsetSize(password);
    const entropy = length * Math.log2(charsetSize);

    if (entropy >= 60) strength++;
    if (entropy >= 80) strength++;

    const normalizedStrength = Math.max(0, Math.min(5, Math.floor(strength / 2)));
    return normalizedStrength as PasswordStrength;
  }

  private getCharsetSize(password: string): number {
    let size = 0;
    if (/[a-z]/.test(password)) size += 26;
    if (/[A-Z]/.test(password)) size += 26;
    if (/[0-9]/.test(password)) size += 10;
    if (/[^a-zA-Z0-9]/.test(password)) size += 32;
    return size || 26;
  }

  getPasswordStrengthLabel(strength: PasswordStrength): string {
    const labels: Record<PasswordStrength, string> = {
      [PasswordStrength.VeryWeak]: "Very Weak",
      [PasswordStrength.Weak]: "Weak",
      [PasswordStrength.Fair]: "Fair",
      [PasswordStrength.Good]: "Good",
      [PasswordStrength.Strong]: "Strong",
      [PasswordStrength.VeryStrong]: "Very Strong",
    };
    return labels[strength];
  }

  estimateCrackTime(password: string): string {
    const charsetSize = this.getCharsetSize(password);
    const possibilities = Math.pow(charsetSize, password.length);
    const guessesPerSecond = 1e9; // 1 billion guesses per second

    const seconds = possibilities / (2 * guessesPerSecond);

    if (seconds < 1) return "Instantly";
    if (seconds < 60) return `${Math.floor(seconds)} seconds`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours`;
    if (seconds < 31536000) return `${Math.floor(seconds / 86400)} days`;
    if (seconds < 3153600000) return `${Math.floor(seconds / 31536000)} years`;

    return "Centuries";
  }

  generateMultiplePasswords(options: PasswordOptions, count: number): string[] {
    return Array.from({ length: count }, () => this.generatePassword(options));
  }

  validatePasswordOptions(options: PasswordOptions): boolean {
    const hasCharType =
      options.includeUppercase === true ||
      options.includeLowercase === true ||
      options.includeNumbers === true ||
      options.includeSymbols === true ||
      (typeof options.customCharacters === "string" &&
        options.customCharacters.length > 0);

    const validLength = options.length >= 4 && options.length <= 128;

    return hasCharType && validLength;
  }
}

export const passwordGenerator = new PasswordGenerator();
export const {
  generatePassword,
  calculatePasswordStrength,
  getPasswordStrengthLabel,
  estimateCrackTime,
  generateMultiplePasswords,
  validatePasswordOptions,
} = passwordGenerator;
