import { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import { useDrop } from 'react-dnd';
import { useSelector } from 'react-redux';
import { ItemTypes } from './constants';
import { Card } from './card';
import store from './../store/store';
import { selectAffectedGameData } from './../store/slice';

const Hand = ({
  ownerName,
  setFocusedCard,
  setDndMsg,
  setActionTargetCard,
  setOpenMoveDialog,
  setOpenCreateTriggerDialog,
  setOpenCreateDelayedTriggerDialog,
  setOpenCreateTokenDialog,
  setTargetIsCopy,
  setOpenInspectGherkinDialog,
}) => {
  const gameData = selectAffectedGameData(store.getState());
  const owner = gameData?.board_state?.players.find((player) => player.player_name === ownerName);
  const ownerIndex = gameData?.board_state?.players.indexOf(owner);

  const [, drop] = useDrop(
    () => ({
      accept: [
        ItemTypes.MTG_LAND_CARD,
        ItemTypes.MTG_NONLAND_PERMANENT_CARD,
        ItemTypes.MTG_INSTANT_CARD,
        ItemTypes.MTG_SORCERY_CARD,
      ],
      drop: (item) => {
        console.log("Detected", item.type, "moving to", owner?.player_name, "'s hand");
        setDndMsg(
          {
            id: item.in_game_id,
            to: "board_state.players[" + ownerIndex + "].hand",
          }
        );
      },
    }), [owner]
  );

  return (
    <Box
      ref={drop}
      sx={{
        display: 'flex',
        width: '100%',
        height: '100%',
        background: "green",
        overflow: "auto",
        alignItems: "center",
        justifyContent: "start",
      }}
    >
      {owner?.hand.map((card) => {
        const handleMove = () => {
          setActionTargetCard(card);
          setOpenMoveDialog(true);
        }
        const handleCreateTrigger = () => {
          setActionTargetCard(card);
          setOpenCreateTriggerDialog(true);
        }
        const handleCreateDelayedTrigger = () => {
          setActionTargetCard(card);
          setOpenCreateDelayedTriggerDialog(true);
        }
        const createTokenCopy = () => {
          setActionTargetCard(card);
          setTargetIsCopy(true);
          setOpenCreateTokenDialog(true);
        }
        const inspectGherkin = () => {
          setActionTargetCard(card);
          setOpenInspectGherkinDialog(true);
        }
        const functions = [
          {name: "move", _function: handleMove},
          {name: "create trigger", _function: handleCreateTrigger},
          {name: "create delayed trigger", _function: handleCreateDelayedTrigger},
          {name: "create token copy", _function: createTokenCopy},
          card.rules? {name: "inspect gherkin", _function: inspectGherkin} : null,
        ].filter(x => x);
        return (
          <Card
            key={card.in_game_id}
            card={card}
            setFocusedCard={setFocusedCard}
            contextMenuFunctions={functions}
          />
        )
      })}
    </Box>
  );
}

export default Hand;
