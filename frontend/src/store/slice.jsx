import { useMemo } from 'react';
import { createSlice, current } from "@reduxjs/toolkit";
import { createSelector } from "reselect";
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
  grouping: [],
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
        return { ...state, actions: [ ...state.actions, { ...action.payload, shuffleResult: shuffled } ] };
      }
      if (action.payload.type === "set_mana") {
        const latestAction = current(state).actions.slice(-1)[0];
        if (latestAction && latestAction.type === "set_mana" && latestAction.targetId === action.payload.targetId) {
          return { ...state, actions: [ ...state.actions.slice(0, -1), action.payload ] };
        }
      }
      if (action.payload.type === "set_hp") {
        const latestAction = current(state).actions.slice(-1)[0];
        if (latestAction && latestAction.type === "set_hp" && latestAction.targetId === action.payload.targetId) {
          return { ...state, actions: [ ...state.actions.slice(0, -1), action.payload ] };
        }
      }
      const actionLength = state.actions.length;
      const newGroupingRecord = state.grouping.filter(([tag, start, end]) => end < actionLength);
      return { ...state, actions: [ ...state.actions, { ...action.payload } ], grouping: newGroupingRecord };
    },
    rollbackGameAction: (state) => {
      const last = state.actions.length - 1;
      const groupingRef = state.grouping.find(([tag, start, end]) => last === end);
      let pastActions = null;
      let pastGrouping = null;
      if (groupingRef) {
        pastActions = state.actions.filter((item, index) => index < groupingRef[1]);
        pastGrouping = state.grouping.filter((item, index) => index < state.grouping.length - 1);
      } else {
        pastActions = state.actions.filter((item, index) => index < state.actions.length - 1);
        pastGrouping = state.grouping;
      }
      const previousState = {
        ...state,
        actions: pastActions,
        grouping: pastGrouping,
      }
      return previousState;
    },
    clearGameAction: (state) => {
      return { ...state, actions: [] };
    },
    appendNewGrouping: (state, action) => {
      return { ...state, grouping: [ ...state.grouping, [ ...action.payload ] ] };
    },
  },
});

export const {
  initialize,
  receivedNewGameData,
  receivedNewGameAction,
  rollbackGameAction,
  clearGameAction,
  appendNewGrouping,
} = gameSlice.actions;

const selectGameData = (store) => store.gameState.gameData;
const selectActions = (store) => store.gameState.actions;

const calculateAffectedGameData = (gameData, actions) => {
  const affectedGameData = cloneDeep(gameData);
  actions?.forEach((action) => {
    const found = findCardById(affectedGameData, action.targetId);
    switch (action.type) {
      case "move":
        const newSourceZone = _.get(affectedGameData, found.path).filter(
          (card) => card.in_game_id !== found.card.in_game_id
        );
        if (action.to === "board_state.stack") {
          const previousControllerId = parseInt(found.path.match(/players\[(.*)\]/)[1]);
          const previousControllerName = affectedGameData.board_state.players[previousControllerId].player_name;
          found.card.annotations.controller = previousControllerName;
        }
        const newTargetZone = [..._.get(affectedGameData, action.to, []), found.card];
        _.set(affectedGameData, found.path, newSourceZone);
        _.set(affectedGameData, action.to, newTargetZone); 
        break;
      case "shuffle":
        _.set(affectedGameData, action.who + ".library", action.shuffleResult);
        break;
      case "set_counter":
        {
          let newCounter = { type: action.counterType, amount: action.counterAmount };
          let updatedCounters = [ ...found.card.counters.filter((counter) => counter.type !== newCounter.type) ];
          if (action.counterAmount) {
            updatedCounters = [...updatedCounters, newCounter];
          }
          const newZone = [ ..._.get(affectedGameData, found.path, []).filter((card) => card.in_game_id !== found.card.in_game_id), { ...found.card, counters: updatedCounters } ];
          _.set(affectedGameData, found.path, newZone);
        }
        break;
      case "set_annotation":
        let updatedAnnotations = {
          ...found.card.annotations,
          [ action.annotationKey ]: action.annotationValue,
        }
        if (!action.annotationValue) {
          delete updatedAnnotations[action.annotationKey];
        }
        {
          const newZone = [..._.get(affectedGameData, found.path, []).filter((card) => card.in_game_id !== found.card.in_game_id), { ...found.card, annotations: updatedAnnotations } ];
          _.set(affectedGameData, found.path, newZone);
        }
        break;
      case "create_trigger":
        {
          const stack = _.get(affectedGameData, "board_state.stack");
          const FilteredStackIds = stack.map((card) => card.in_game_id).filter((id) => id.endsWith(found.card.in_game_id));
          let availableTriggerSerialNumber = 1;
          for (const id of FilteredStackIds) {
            if (id.startsWith("trigger" + availableTriggerSerialNumber)) {
              availableTriggerSerialNumber++;
            }
          }
          const pseudoCard = cloneDeep(found.card);
          _.set(pseudoCard, "in_game_id", "trigger" + availableTriggerSerialNumber + "@" + found.card.in_game_id);
          _.set(pseudoCard, "triggerContent", action.triggerContent);
          const previousControllerId = parseInt(found.path.match(/players\[(.*)\]/)[1]);
          const previousControllerName = affectedGameData.board_state.players[previousControllerId].player_name;
          pseudoCard.annotations.controller = previousControllerName;
          const newStack = [ ..._.get(affectedGameData, "board_state.stack"), pseudoCard ];
          _.set(affectedGameData, "board_state.stack", newStack);
        }
        break;
      case "remove_trigger":
        {
          const stack = _.get(affectedGameData, "board_state.stack");
          const newStack = stack.filter(card => card.in_game_id !== found.card.in_game_id);
          _.set(affectedGameData, "board_state.stack", newStack);
        }
        break;
      case "set_mana":
        _.set(affectedGameData, "board_state.players[" + action.targetId + "].mana_pool", action.manaPool);
        break;
      case "set_hp":
        _.set(affectedGameData, "board_state.players[" + action.targetId + "].hp", action.value);
        break;
      case "set_player_counter":
        {
          const newCounter = { type: action.counterType, amount: action.counterAmount };
          const oldPlayerCounters = _.get(affectedGameData, "board_state.players[" + action.targetId + "].counters");
          let updatedCounters = [ ...oldPlayerCounters.filter((counter) => counter.type !== newCounter.type) ];
          if (action.counterAmount) {
            updatedCounters = [...updatedCounters, newCounter];
          }
          _.set(affectedGameData, "board_state.players[" + action.targetId + "].counters", updatedCounters);
        }
        break;
      case "set_player_annotation":
        {
          const oldPlayerAnnotations = _.get(affectedGameData, "board_state.players[" + action.targetId + "].annotations");
          let updatedAnnotations = { ...oldPlayerAnnotations, [action.annotationKey]: action.annotationValue, };
          if (!action.annotationValue) {
            delete updatedAnnotations[action.annotationKey];
          }
          _.set(affectedGameData, "board_state.players[" + action.targetId + "].annotations", updatedAnnotations);
        }
        break;
      case "create_token":
        {
          const newZone = [
            ..._.get(affectedGameData, action.destination),
            action.card,
          ];
          _.set(affectedGameData, action.destination, newZone);
        }
        break;
      case "remove_token":
        {
          const battlefield = _.get(affectedGameData, found.path);
          const newBattlefield = battlefield.filter(card => card.in_game_id !== found.card.in_game_id);
          _.set(affectedGameData, found.path, newBattlefield);
        }
        break;
      case "create_delayed_trigger":
        {
          const players = _.get(affectedGameData, "board_state.players");
          const playerId = players.findIndex(player => player.player_name === action.affectingWho);
          const newDelayedTriggers = [
            ..._.get(affectedGameData, "board_state.players[" + playerId + "].delayed_triggers"),
            action,
          ]
          _.set(affectedGameData, "board_state.players[" + playerId + "].delayed_triggers", newDelayedTriggers);
        }
        break;
      case "remove_delayed_trigger":
        {
          const players = _.get(affectedGameData, "board_state.players");
          const playerId = players.findIndex(player => player.player_name === action.affectingWho);
          const delayedTriggers = _.get(affectedGameData, "board_state.players[" + playerId + "].delayed_triggers");
          const newDelayedTriggers = delayedTriggers.filter(trigger => trigger.targetId !== action.targetId);
          _.set(affectedGameData, "board_state.players[" + playerId + "].delayed_triggers", newDelayedTriggers);
        }
        break;
    }
  });
  return affectedGameData;
};

export const selectAffectedGameData = createSelector([selectGameData, selectActions], calculateAffectedGameData);

const selectPlayerByName = (name) => {
  return (gameData) => gameData?.board_state?.players.find(player => player.player_name === name);
};
export const usePlayerSelector = (name) => {
  return useSelector(createSelector([selectGameData], selectPlayerByName(name)));
};

export default gameSlice.reducer;
