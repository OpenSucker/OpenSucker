'use client';

import { LEEK_CHARACTERS, LeekPersona } from './leek-lore';

/**
 * CharacterStore: Manages the lifecycle and storage of individual leek JSONs.
 * Uses localStorage to persist character states including their personas and story progress.
 */

export interface CharacterState {
  persona: LeekPersona;
  lastUpdated: string;
  storyProgress: number; // 0 to 100
  isActive: boolean;
}

const STORAGE_KEY = 'open-sucker-characters';

export function getCharacterStore(): Record<string, CharacterState> {
  if (typeof window === 'undefined') return {};
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) {
    try {
      return JSON.parse(stored);
    } catch (e) {
      console.error('Failed to parse character store', e);
    }
  }

  // Initialize with the 5 master characters
  const initialStore: Record<string, CharacterState> = {};
  LEEK_CHARACTERS.forEach(char => {
    initialStore[char.id] = {
      persona: char,
      lastUpdated: new Date().toISOString(),
      storyProgress: 10,
      isActive: false
    };
  });
  
  saveCharacterStore(initialStore);
  return initialStore;
}

export function saveCharacterStore(store: Record<string, CharacterState>) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(store));
}

export function updateCharacterStory(id: string, progress: number) {
  const store = getCharacterStore();
  if (store[id]) {
    store[id].storyProgress = progress;
    store[id].lastUpdated = new Date().toISOString();
    saveCharacterStore(store);
  }
}

export function getCharacterById(id: string): CharacterState | undefined {
  const store = getCharacterStore();
  return store[id];
}
