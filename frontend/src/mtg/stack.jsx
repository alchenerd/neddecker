import { useState, useEffect } from 'react'
import { useDrop } from 'react-dnd'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import { ItemTypes } from './constants'
import { Card } from './card'

export function Stack({stack, setBoardData, map, setSelectedCard, setDndMsg, setActionTargetCard, setOpenMoveDialog, setOpenCounterDialog, ...props}) {
  const [toShow, setToShow] = useState([]);

  useEffect(() => {
    if (stack) {
      setToShow(stack.map((card) => ({
        id: card.id,
        name: card.name,
        imageUrl: map[card.name] || map[card.name.split(" // ")[0]],
        backImageUrl: map[card.name.split(" // ")[1]] || "",
        typeLine: card.faces ? card.faces.front.type_line + " // " + card.faces.back.type_line: card.type_line,
        manaCost: card.mana_cost,
      })));
    }
  }, [stack]);

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
        console.log(stack)
        setDndMsg(
          {
            id: item.id,
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
      {toShow.map(card => {
        const handleMove = () => {
          setActionTargetCard(card);
          setOpenMoveDialog(true);
        }
        const functions = [
          {name: "move", _function: handleMove},
          {name: "set counter", _function: () => {
            setActionTargetCard(card);
            setOpenCounterDialog(true);
          }},
        ];
        return (
          <Card
            key={card.id}
            id={card.id}
            name={card.name}
            imageUrl={card.imageUrl}
            backImageUrl={card.backImageUrl}
            setSelectedCard={setSelectedCard}
            typeLine={card.typeLine}
            manaCost={card.manaCost}
            contextMenuFunctions={functions}
          />
        )
      })}
    </Box>
  );
}
