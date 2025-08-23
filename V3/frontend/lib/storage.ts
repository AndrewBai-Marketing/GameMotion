export function getStoredValue<T>(key: string, defaultValue: T): T {
  if (typeof window === "undefined") return defaultValue

  try {
    const item = window.localStorage.getItem(key)
    return item ? JSON.parse(item) : defaultValue
  } catch (error) {
    console.warn(`Failed to get stored value for ${key}:`, error)
    return defaultValue
  }
}

export function setStoredValue<T>(key: string, value: T): void {
  if (typeof window === "undefined") return

  try {
    window.localStorage.setItem(key, JSON.stringify(value))
  } catch (error) {
    console.warn(`Failed to store value for ${key}:`, error)
  }
}

export function removeStoredValue(key: string): void {
  if (typeof window === "undefined") return

  try {
    window.localStorage.removeItem(key)
  } catch (error) {
    console.warn(`Failed to remove stored value for ${key}:`, error)
  }
}

// Storage keys
export const STORAGE_KEYS = {
  SELECTED_PROFILE: "gamemotion_selected_profile",
  SELECTED_EXE: "gamemotion_selected_exe",
  CAMERA_SETTINGS: "gamemotion_camera_settings",
} as const
