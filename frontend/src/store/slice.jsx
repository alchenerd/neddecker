import { createSlice, current } from "@reduxjs/toolkit";
import { useSelector } from "react-redux";
import _ from 'lodash';
import { cloneDeep } from 'lodash';
import { findCardById } from '../mtg/find-card';

// gameData should not be changed by reducers except receivedNewGameData
// When the affected board state is needed,
// we should call a custom selector that applied all actions to the board state
const initialState = {
  gameData: {},
  actions: [],
};

const shuffle = (array) => {
  const newArray = cloneDeep(array);
  for (let i = array.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [newArray[i], newArray[j]] = [newArray[j], newArray[i]];
  }
  return newArray;
}

export const gameSlice = createSlice({
  name: "gameState",
  initialState,
  reducers: {
    initialize: (state) => {
      return initialState;
    },
    receivedNewGameData: (state, action) => {
      console.log("received new game data:", action);
      return {...current(state), gameData: action.payload.newGameData};
    },
    receivedNewGameAction: (state, action) => {
      if (action.payload.type === "shuffle") {
        const shuffled = shuffle(_.get(current(state).gameData, action.payload.who + ".library"));
        console.log(shuffled);
          //.sort(() => Math.random() - 0.5);
        return { ...state, actions: [ ...state.actions, { ...action.payload, shuffleResult: shuffled } ] };
      }
      return { ...state, actions: [ ...state.actions, { ...action.payload } ] };
    },
    rollbackGameAction: (state) => {
      const pastActions = state.actions.filter((item, index) => index < state.actions.length - 1);
      const previousState = {
        ...state,
        actions: pastActions,
      }
      return previousState;
    },
  },
});

export const {
  initialize,
  receivedNewGameData,
  receivedNewGameAction,
  rollbackGameAction
} = gameSlice.actions;

const selectAffectedGameData = (store) => {
  const affectedGameData = cloneDeep(store.gameState.gameData);
  const actions = store.gameState.actions;
  actions.forEach((action) => {
    const found = findCardById(affectedGameData, action.targetId);
    switch (action.type) {
      case "move":
        const newSourceZone = _.get(affectedGameData, found.path).filter(
          (card) => card.in_game_id !== found.card.in_game_id
        );
        const newTargetZone = [..._.get(affectedGameData, action.to, []), found.card];
        _.set(affectedGameData, found.path, newSourceZone);
        _.set(affectedGameData, action.to, newTargetZone); 
        break;
      case "shuffle":
        _.set(affectedGameData, action.who + ".library", action.shuffleResult);
        break;
      case "set_counter":
        const newCounter = { type: action.counterType, amount: action.counterAmount };
        const updatedCounters = [
          ...found.card.counters.filter((counter) => counter.type !== newCounter.type),
          newCounter,
        ];
        {
          const newZone = [ ..._.get(affectedGameData, found.path, []).filter((card) => card.in_game_id !== found.card.in_game_id), { ...found.card, counters: updatedCounters } ];
          _.set(affectedGameData, found.path, newZone);
        }
        break;
      case "set_annotation":
        const updatedAnnotations = {
          ...found.card.annotations,
          [ action.annotationKey ]: action.annotationValue,
        }
        {
          const newZone = [..._.get(affectedGameData, found.path, []).filter((card) => card.in_game_id !== found.card.in_game_id), { ...found.card, annotations: updatedAnnotations } ];
          _.set(affectedGameData, found.path, newZone);
        }
        break;
    }
  });
  return affectedGameData;
};

export const useAffectedGameDataSelector = () => {
  return useSelector(selectAffectedGameData);
};

export default gameSlice.reducer;
