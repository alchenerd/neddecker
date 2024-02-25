import _ from 'lodash';
import { cloneDeep } from 'lodash';

export const findCardById = (gameData, cardId) => {
  if (!gameData || !cardId) {
    return ({
      card: null,
      path: null,
    });
  }
  const pathsToCheck = [
    "board_state.stack",
    "board_state.players[0].battlefield",
    "board_state.players[0].hand",
    "board_state.players[0].graveyard",
    "board_state.players[1].battlefield",
    "board_state.players[1].hand",
    "board_state.players[1].graveyard",
    "board_state.players[0].library",
    "board_state.players[1].library",
    "board_state.players[0].exile",
    "board_state.players[1].exile",
  ];
  let foundCard = undefined;
  for (const path of pathsToCheck) {
    foundCard = _.get(gameData, path, []).find((card) => card.in_game_id === cardId);
    if (foundCard) {
      return ({
        card: cloneDeep(foundCard),
        path: path,
      });
    }
  }
  return ({
    card: null,
    path: null,
  });
}
