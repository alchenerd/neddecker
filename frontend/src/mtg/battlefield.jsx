import { useState, useEffect } from 'react'
import Box from '@mui/material/Box'
import { DndProvider, useDrop } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import { ItemTypes } from './constants'
import { Card } from './card'

export function Battlefield({library, map, setSelectedCard, owner, setDndMsg, ...props}) {
  const [toShow, setToShow] = useState([]);

  useEffect(() => {
    if (owner.battlefield) {
      console.log(owner.battlefield),
      setToShow(owner.battlefield.map((card) => ({
        id: card.id,
        name: card.name,
        imageUrl: map[card.name] || map[card.name.split(" // ")[0]],
        backImageUrl: map[card.name.split(" // ")[1]] || "",
      })));
    }
  }, [owner.battlefield]);

  const [, drop] = useDrop(
    () => ({
      accept: [
        ItemTypes.MTG_LAND_CARD,
        ItemTypes.MTG_NONLAND_PERMANENT_CARD,
        ItemTypes.MTG_TOKEN,
      ],
      drop: (item) => {
        console.log("Detected", item.type, "moving to", owner.player_name, "'s battlefield");
        setDndMsg(
          {
            id: item.id,
            to: {
              pathFromBoardState: ["players"],
              key: "player_name",
              value: owner.player_name,
              zone: "battlefield",
            },
          }
        );
      },
    }), [owner]
  );

  const renderLibrary = (cond) => {
    if (cond) {
      return (
        <Card
          canDrag="false"
          sx={{
            position: "absolute",
            top: 0,
            right: 0,
            margin:"10px",
            height: "50%"
          }}
          backgroundColor="#c0ffee"
        />
      )
    }
  }

  return (
    <>
      <Box sx={{display: "flex", width: "100%", height: "100%", background: "blue", position: "relative"}} ref={drop}>
        <p>Battlefield</p>
        {renderLibrary(library && library.length > 0)}
        {toShow.map(card => {
          return (
            <Card
              key={card.id}
              id={card.id}
              name={card.name}
              imageUrl={card.imageUrl}
              backImageUrl={card.backImageUrl}
              setSelectedCard={setSelectedCard}
            />
          )
        })}
      </Box>
    </>
  )
}
