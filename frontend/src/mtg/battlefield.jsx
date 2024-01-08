import { useState, useEffect } from 'react'
import Box from '@mui/material/Box'
import { DndProvider, useDrop } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import { ItemTypes } from './constants'
import { Card } from './card'

export function Battlefield({content, library, map, setSelectedCard, ...props}) {
  const [toShow, setToShow] = useState([]);

  useEffect(() => {
    if (content) {
      console.log(content),
      setToShow(content.map((card) => ({
        id: card.id,
        name: card.name,
        imageUrl: map[card.name] || map[card.name.split(" // ")[0]],
        backImageUrl: map[card.name.split(" // ")[1]] || "",
      })));
    }
  }, [content]);

  const [, drop] = useDrop(
    () => ({
      accept: ItemTypes.MTG_CARD,
      drop: (item) => {
        console.log(item);
      },
    }), []
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
