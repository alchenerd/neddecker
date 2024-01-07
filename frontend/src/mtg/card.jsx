import { useState, useEffect } from 'react'
import Box from '@mui/material/Box'
import { useDrag } from 'react-dnd'
import { ItemTypes } from './constants'

export function Card({id, name, imageUrl, backImageUrl, backgroundColor, setSelectedCard, ...props}) {
  const [isFlipped, setIsFlipped] = useState(false);
  const [isFocused, setIsFocused] = useState(false);
  const imageSource = isFlipped ? backImageUrl : imageUrl;
  const [{ isDragging }, drag] = useDrag(() => ({
    type: ItemTypes.MTG_CARD,
    item: {id: id},
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging()
    }),
      canDrag: props.canDrag === undefined ? true : false,
  }))

  const registerFocus = () => {
    setIsFocused(true);
  }

  useEffect(() => {
    if (isFocused) {
      setSelectedCard?.(imageSource);
    }
    setIsFocused(false);
  }, [isFocused]);

  return (
    <Box
      sx={{
        height: '100%',
        display: "inline-block",
        aspectRatio: 2.5 / 3.5,
        overflow: 'hidden',
        backgroundColor: backgroundColor || 'transparent',
        ...props.sx,
      }}
      id={id}
      ref={drag}
      onMouseOver={registerFocus}
    >
      <img
        src={isFlipped? backImageUrl : imageUrl}
        alt={name}
        height='100%'
        style={{
          opacity: isDragging? 0.5 : 1,
          aspectRatio: 2.5 / 3.5,
        }}
      />
    </Box>
  );
}
