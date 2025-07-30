import { defineStore } from 'pinia';
import { ref } from 'vue';
export const useAppStore = defineStore('app', () => {
    // --- State ---
    const currentGame = ref('hsr');
    // --- Actions ---
    function setCurrentGame(game) {
        if (['hsr', 'gi'].includes(game)) {
            currentGame.value = game;
        }
        else {
            console.warn(`Invalid game specified: ${game}. Defaulting to 'hsr'.`);
            currentGame.value = 'hsr';
        }
    }
    return {
        currentGame,
        setCurrentGame,
    };
});
//# sourceMappingURL=app.js.map