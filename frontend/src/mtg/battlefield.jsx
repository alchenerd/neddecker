import { useState, useEffect } from 'react'
import Box from '@mui/material/Box'
import { DndProvider, useDrop } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import { ItemTypes } from './constants'
import { Card } from './card'

export function Battlefield({library, map, setSelectedCard, owner, ownerIndex, setDndMsg, ...props}) {
  const [toShow, setToShow] = useState([]);

  useEffect(() => {
    if (owner.battlefield) {
      console.log(owner.battlefield),
      setToShow(owner.battlefield.map((card) => ({
        id: card.id,
        name: card.name,
        imageUrl: map[card.name] || map[card.name.split(" // ")[0]],
        backImageUrl: map[card.name.split(" // ")[1]] || "",
        typeLine: card.faces ? card.faces.front.type_line + " // " + card.faces.back.type_line: card.type_line,
        manaCost: card.mana_cost,
        offsetX: card.offsetX,
        offsetY: card.offsetY,
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
      drop: (item, monitor) => {
        console.log("Detected", item.type, "moving to", owner.player_name, "'s battlefield");
        const clientOffset = monitor.getClientOffset();
        const dropZone = document.getElementById("battlefield-" + owner.player_name).getBoundingClientRect();
        const draggedCard = document.getElementById(item.id).getBoundingClientRect();
        setDndMsg(
          {
            id: item.id,
            to: "board_state.players[" + ownerIndex + "].battlefield",
            offsetX: clientOffset.x - dropZone.x - (draggedCard.width / 2) + "px",
            offsetY: clientOffset.y - dropZone.y - (draggedCard.height / 2)+ "px",
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
            height: "40%"
          }}
          backgroundColor="#c0ffee"
        />
      )
    }
  }

  return (
    <>
      <Box sx={{display: "flex", width: "100%", height: "100%", background: "blue", position: "relative"}} ref={drop} id={"battlefield-" + owner.player_name}>
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
              typeLine={card.typeLine}
              manaCost={card.manaCost}
              sx={{
                height: "40%",
                position: "absolute",
                left: card.offsetX,
                top: card.offsetY,
              }}
            />
          )
        })}
      </Box>
    </>
  )
}
