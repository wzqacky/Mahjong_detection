import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Player, Round } from '../types';

// ─── Seat wind helpers ──────────────────────────────────────────────────────────
const WINDS: Array<'East' | 'South' | 'West' | 'North'> = ['East', 'South', 'West', 'North'];

/** Given the current dealerIndex (in the original player array) and a player
 *  at index i, return their current seat wind. */
function seatWindOf(playerIdx: number, dealerIdx: number, count: number): 'East' | 'South' | 'West' | 'North' {
  const offset = (playerIdx - dealerIdx + count) % count;
  return WINDS[offset];
}

// ─── Draw payment calculator ────────────────────────────────────────────────────
function computeDrawPayments(
  players: Player[],
  tenpaiPlayerIds: string[],
): Record<string, number> {
  const payments: Record<string, number> = {};
  players.forEach(p => { payments[p.id] = 0; });

  const tenpaiCount = tenpaiPlayerIds.length;
  const playerCount = players.length;
  const notenIds = players.map(p => p.id).filter(id => !tenpaiPlayerIds.includes(id));
  const notenCount = notenIds.length;

  if (tenpaiCount === 0 || tenpaiCount === playerCount) {
    return payments; // no exchange
  }

  const receivePerTenpai = Math.floor(3000 / tenpaiCount);
  const payPerNoten = Math.floor(3000 / notenCount);

  tenpaiPlayerIds.forEach(id => { payments[id] = receivePerTenpai; });
  notenIds.forEach(id => { payments[id] = -payPerNoten; });

  return payments;
}

// ─── Tsumo payment calculator ───────────────────────────────────────────────────
function computeTsumoPayments(
  players: Player[],
  winnerId: string,
  dealerPayment: number,
  nonDealerPayment: number,
  totalPoints: number,
): Record<string, number> {
  const payments: Record<string, number> = {};
  players.forEach(p => { payments[p.id] = 0; });

  const winner = players.find(p => p.id === winnerId)!;
  const winnerIsDealer = winner.isDealer;

  let collected = 0;
  players.forEach(p => {
    if (p.id === winnerId) return;
    if (winnerIsDealer) {
      payments[p.id] = -dealerPayment;
      collected += dealerPayment;
    } else {
      const pays = p.isDealer ? dealerPayment : nonDealerPayment;
      payments[p.id] = -pays;
      collected += pays;
    }
  });
  payments[winnerId] = collected;
  return payments;
}

// ─── Store interface ─────────────────────────────────────────────────────────────
interface GameStore {
  phase: 'setup' | 'playing' | 'finished';
  players: Player[];
  startingScore: number;
  rounds: Round[];
  currentRoundNumber: number;
  currentRoundWind: 'East' | 'South';
  honba: number;
  riichiBets: number;
  playerRiichi: boolean[];
  dealerIndex: number; // index into players[]

  // Actions
  initGame(players: Player[], startingScore: number): void;
  declareRiichi(playerIndex: number): void;
  undoRiichi(playerIndex: number): void;
  recordWin(round: Omit<Round, 'roundNumber' | 'roundWind' | 'honba' | 'riichiBets'>): void;
  recordDraw(tenpaiPlayerIds: string[]): void;
  endGame(): void;
  resetGame(): void;
}

// ─── Store implementation ────────────────────────────────────────────────────────
export const useGameStore = create<GameStore>()(
  persist(
    (set, get) => ({
      phase: 'setup',
      players: [],
      startingScore: 25000,
      rounds: [],
      currentRoundNumber: 1,
      currentRoundWind: 'East',
      honba: 0,
      riichiBets: 0,
      playerRiichi: [],
      dealerIndex: 0,

      initGame(players, startingScore) {
        const count = players.length;
        const initialised = players.map((p, i) => ({
          ...p,
          score: startingScore,
          isDealer: i === 0,
          seatWind: WINDS[i],
        }));
        set({
          phase: 'playing',
          players: initialised,
          startingScore,
          rounds: [],
          currentRoundNumber: 1,
          currentRoundWind: 'East',
          honba: 0,
          riichiBets: 0,
          playerRiichi: new Array(count).fill(false),
          dealerIndex: 0,
        });
      },

      declareRiichi(playerIndex) {
        const { players, playerRiichi } = get();
        if (playerRiichi[playerIndex]) return;
        const updatedPlayers = players.map((p, i) =>
          i === playerIndex ? { ...p, score: p.score - 1000 } : p
        );
        const updatedRiichi = [...playerRiichi];
        updatedRiichi[playerIndex] = true;
        set({
          players: updatedPlayers,
          playerRiichi: updatedRiichi,
          riichiBets: get().riichiBets + 1,
        });
      },

      undoRiichi(playerIndex) {
        const { players, playerRiichi } = get();
        if (!playerRiichi[playerIndex]) return;
        const updatedPlayers = players.map((p, i) =>
          i === playerIndex ? { ...p, score: p.score + 1000 } : p
        );
        const updatedRiichi = [...playerRiichi];
        updatedRiichi[playerIndex] = false;
        set({
          players: updatedPlayers,
          playerRiichi: updatedRiichi,
          riichiBets: Math.max(0, get().riichiBets - 1),
        });
      },

      recordWin(round) {
        const {
          players,
          rounds,
          currentRoundNumber,
          currentRoundWind,
          honba,
          riichiBets,
          dealerIndex,
        } = get();

        const fullRound: Round = {
          ...round,
          roundNumber: currentRoundNumber,
          roundWind: currentRoundWind,
          honba,
          riichiBets,
        };

        // Apply payments to player scores
        const updatedPlayers = players.map(p => ({
          ...p,
          score: p.score + (round.payments[p.id] ?? 0),
        }));

        const winner = players.find(p => p.id === round.winnerId);
        const winnerIsDealer = winner?.isDealer ?? false;
        const count = players.length;

        // Advance game state
        let newDealerIndex = dealerIndex;
        let newRoundNumber = currentRoundNumber;
        let newRoundWind = currentRoundWind;
        let newHonba = honba;
        let newPhase: 'playing' | 'finished' = 'playing';

        if (winnerIsDealer) {
          // Dealer wins → dealer stays, honba++
          newHonba = honba + 1;
        } else {
          // Non-dealer wins → rotate dealer, reset honba
          newHonba = 0;
          newDealerIndex = (dealerIndex + 1) % count;
          if (newDealerIndex === 0) {
            if (currentRoundWind === 'East') {
              newRoundWind = 'South';
              newRoundNumber = 1;
            } else {
              newPhase = 'finished';
            }
          } else {
            newRoundNumber = newDealerIndex + 1;
          }
        }

        // Reassign seat winds for updated dealer
        const reassigned = updatedPlayers.map((p, i) => ({
          ...p,
          isDealer: i === newDealerIndex,
          seatWind: seatWindOf(i, newDealerIndex, count),
        }));

        set({
          players: reassigned,
          rounds: [fullRound, ...rounds],
          currentRoundNumber: newRoundNumber,
          currentRoundWind: newRoundWind,
          honba: newHonba,
          riichiBets: 0,
          playerRiichi: new Array(count).fill(false),
          dealerIndex: newDealerIndex,
          phase: newPhase,
        });
      },

      recordDraw(tenpaiPlayerIds) {
        const {
          players,
          rounds,
          currentRoundNumber,
          currentRoundWind,
          honba,
          riichiBets,
          dealerIndex,
        } = get();

        const payments = computeDrawPayments(players, tenpaiPlayerIds);

        const fullRound: Round = {
          roundNumber: currentRoundNumber,
          roundWind: currentRoundWind,
          honba,
          riichiBets,
          winnerId: null,
          loserId: null,
          isTsumo: false,
          isDraw: true,
          tenpaiPlayerIds,
          yakuList: [],
          han: 0,
          fu: 0,
          payments,
        };

        const updatedPlayers = players.map(p => ({
          ...p,
          score: p.score + (payments[p.id] ?? 0),
        }));

        const count = players.length;
        const dealerIsTenpai = tenpaiPlayerIds.includes(players[dealerIndex].id);

        // Draw: honba always increments
        // Dealer stays if tenpai; rotates if not
        let newDealerIndex = dealerIndex;
        let newRoundNumber = currentRoundNumber;
        let newRoundWind = currentRoundWind;
        let newPhase: 'playing' | 'finished' = 'playing';

        if (!dealerIsTenpai) {
          newDealerIndex = (dealerIndex + 1) % count;
          if (newDealerIndex === 0) {
            if (currentRoundWind === 'East') {
              newRoundWind = 'South';
              newRoundNumber = 1;
            } else {
              newPhase = 'finished';
            }
          } else {
            newRoundNumber = newDealerIndex + 1;
          }
        }

        const reassigned = updatedPlayers.map((p, i) => ({
          ...p,
          isDealer: i === newDealerIndex,
          seatWind: seatWindOf(i, newDealerIndex, count),
        }));

        set({
          players: reassigned,
          rounds: [fullRound, ...rounds],
          currentRoundNumber: newRoundNumber,
          currentRoundWind: newRoundWind,
          honba: honba + 1,
          // riichiBets remain on table after draw
          playerRiichi: new Array(count).fill(false),
          dealerIndex: newDealerIndex,
          phase: newPhase,
        });
      },

      endGame() {
        set({ phase: 'finished' });
      },

      resetGame() {
        set({
          phase: 'setup',
          players: [],
          rounds: [],
          currentRoundNumber: 1,
          currentRoundWind: 'East',
          honba: 0,
          riichiBets: 0,
          playerRiichi: [],
          dealerIndex: 0,
        });
      },
    }),
    {
      name: 'mahjong-game-store',
      storage: createJSONStorage(() => AsyncStorage),
    },
  ),
);

// Selectors
export const selectDealer = (state: GameStore) =>
  state.players[state.dealerIndex];

export const selectRoundLabel = (state: GameStore) => {
  const windChar = state.currentRoundWind === 'East' ? '東' : '南';
  return `${windChar}${state.currentRoundNumber}局`;
};

export const selectRoundWindLower = (state: GameStore): 'east' | 'south' =>
  state.currentRoundWind === 'East' ? 'east' : 'south';
