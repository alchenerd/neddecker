import { useState, useEffect } from 'react'
import { useDrop } from 'react-dnd'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import { ItemTypes } from './constants'
import { Card } from './card'
import store from './../store/store';
import { selectAffectedGameData } from './../store/slice';

export function Stack({setFocusedCard, setDndMsg, setActionTargetCard, setOpenMoveDialog, setOpenCounterDialog, setOpenAnnotationDialog, setOpenCreateTriggerDialog, setOpenCreateDelayedTriggerDialog}) {
  const stack = selectAffectedGameData(store.getState())?.board_state?.stack || [];

  const [, drop] = useDrop(
    () => ({
      accept: [
        ItemTypes.MTG_NONLAND_PERMANENT_CARD,
        ItemTypes.MTG_INSTANT_CARD,
        ItemTypes.MTG_SORCERY_CARD,
        ItemTypes.MTG_TRIGGER,
      ],
      drop: (item) => {
        console.log("Detected", item.type, "moving to the stack");
        setDndMsg(
          {
            id: item.in_game_id,
            to: "board_state.stack",
          }
        );
      },
    }), [stack]
  );

  return (
    <Box
      backgroundColor='#abcdef'
      sx={{
        height: "100%",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "start",
      }}
      ref={drop}
    >
      <Typography variant="h5" color="Black">
        Stack
      </Typography>
      {stack.map(card => {
        const handleMove = () => {
          setActionTargetCard(card);
          setOpenMoveDialog(true);
        };
        const setCounter = () => {
          setActionTargetCard(card);
          setOpenCounterDialog(true);
        };
        const setAnnotation = () => {
          setActionTargetCard(card);
          setOpenAnnotationDialog(true);
        };
        const createTrigger = () => {
          setActionTargetCard(card);
          setOpenCreateTriggerDialog(true);
        };
        const createDelayedTrigger = () => {
          setActionTargetCard(card);
          setOpenCreateDelayedTriggerDialog(true);
        };
        const functions = [
          {name: "move", _function: handleMove},
          {name: "set counter", _function: setCounter},
          {name: "set annotation", _function: setAnnotation},
          {name: "create trigger", _function: createTrigger},
          {name: "create delayed trigger", _function: createDelayedTrigger},
        ];
        return (
          <Card
            key={card.in_game_id}
            card={card}
            setFocusedCard={setFocusedCard}
            contextMenuFunctions={functions}
            sx={{
              backgroundColor: card?.in_game_id.startsWith("token") ? "white": "transparent",
            }}
          />
        )
      })}
    </Box>
  );
}
