import { useState, useEffect } from 'react'
import Box from '@mui/material/Box'
import { useDrop } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import { ItemTypes } from './constants'
import { Card } from './card'

export function Hand({map, setSelectedCard, owner, ownerIndex, setDndMsg, ...props}) {
  const [toShow, setToShow] = useState([]);

  useEffect(() => {
    if (owner.hand) {
      setToShow(owner.hand.map((card) => ({
        id: card.id,
        name: card.name,
        imageUrl: map[card.name] || map[card.name.split(" // ")[0]],
        backImageUrl: map[card.name.split(" // ")[1]] || "",
        isFlipped: card?.isFlipped || false,
        typeLine: card?.isFlipped ?
          (card?.faces?.back.type_line || "") :
          (card?.faces?.front.type_line || card.type_line || ""),
        manaCost: card.mana_cost,
      })));
    } else {
      setToShow([]);
    }
  }, [owner.hand]);

  const [, drop] = useDrop(
    () => ({
      accept: [
        ItemTypes.MTG_LAND_CARD,
        ItemTypes.MTG_NONLAND_PERMANENT_CARD,
        ItemTypes.MTG_INSTANT_CARD,
        ItemTypes.MTG_SORCERY_CARD,
      ],
      drop: (item) => {
        console.log("Detected", item.type, "moving to", owner.player_name, "'s hand");
        setDndMsg(
          {
            id: item.id,
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
      {toShow.map(card => {
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
          />
        )
      })}
    </Box>
  );
}
