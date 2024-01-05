import { useState, useEffect } from 'react'
import Box from '@mui/material/Box'
import { DndProvider, useDrop } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import { ItemTypes } from './constants'
import { Card } from './card'

export function Hand({content, map, ...props}) {
  const [toShow, setToShow] = useState([]);

  useEffect(() => {
    if (content) {
      console.log(content);
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

  return (
    <>
      <Box
        ref={drop}
        sx={{
          display: 'flex',
          width: '100%',
          height: '100%',
          background: "green",
          overflow: "auto",
        }}>
        {toShow.map(card => {return <Card key={card.id} id={card.id} imageUrl={card.imageUrl} backImageUrl={card.backImageUrl} />})}
      </Box>
    </>
  );
}
