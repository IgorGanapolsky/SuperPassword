export const generatePassword = (length: number = 12): string => {
  const charset =
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()_+-=[]{}|;:,.<>?";
  let password = "";
  for (let i = 0; i < length; i++) {
    const randomIndex = Math.floor(Math.random() * charset.length);
    password += charset[randomIndex];
  }
  return password;
};

export const calculatePasswordStrength = (password: string): number => {
  let score = 0;

  // Length
  if (password.length >= 12) score += 2;
  else if (password.length >= 8) score += 1;

  // Uppercase
  if (/[A-Z]/.test(password)) score += 1;

  // Lowercase
  if (/[a-z]/.test(password)) score += 1;

  // Numbers
  if (/[0-9]/.test(password)) score += 1;

  // Special characters
  if (/[^A-Za-z0-9]/.test(password)) score += 1;

  return score;
};
