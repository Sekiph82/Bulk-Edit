const STORAGE_KEY = "bulk-edit-sound-enabled";

export function isSoundEnabled(): boolean {
  if (typeof window === "undefined") return false;
  return localStorage.getItem(STORAGE_KEY) === "true";
}

export function setSoundEnabled(enabled: boolean): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, String(enabled));
}

export function playSuccessSound(): void {
  if (!isSoundEnabled()) return;
  try {
    const audio = new Audio("/sounds/cha-ching.mp3");
    audio.play().catch(() => {});
  } catch {
    // fail silently
  }
}
