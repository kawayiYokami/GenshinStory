import { defineStore } from 'pinia'
import { ref } from 'vue'

export type Game = 'hsr' | 'gi';

export const useAppStore = defineStore('app', () => {
  // --- State ---
  const currentGame = ref<Game>('hsr');

  // --- Actions ---
  function setCurrentGame(game: Game) {
    if (['hsr', 'gi'].includes(game)) {
      currentGame.value = game;
    } else {
      console.warn(`Invalid game specified: ${game}. Defaulting to 'hsr'.`);
      currentGame.value = 'hsr';
    }
  }

  return {
    currentGame,
    setCurrentGame,
  }
})