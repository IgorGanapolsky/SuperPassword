import { AES, enc } from "crypto-js";

// In a production environment, we'd use a more sophisticated encryption setup
// possibly involving a hardware security module (HSM) for key management
export function encrypt(text: string, key: string): string {
  return AES.encrypt(text, key).toString();
}

export function decrypt(ciphertext: string, key: string): string {
  const bytes = AES.decrypt(ciphertext, key);
  return bytes.toString(enc.Utf8);
}
