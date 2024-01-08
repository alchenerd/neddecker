import { useState, useEffect } from 'react'
import { useDrop } from 'react-dnd'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import { ItemTypes } from './constants'

export function Stack({content, ...props}) {
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
      {toShow.map(card => {return (
        <Card
          key={card.id}
          id={card.id}
          name={card.name}
          imageUrl={card.imageUrl}
          backImageUrl={card.backImageUrl}
          setSelectedCard={setSelectedCard}
        />
      )})}
    </Box>
  );
}
