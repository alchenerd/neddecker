import { useState, useEffect } from 'react'
import Box from '@mui/material/Box'
import { useDrag } from 'react-dnd'
import { ItemTypes } from './constants'

export function Card({id, name, imageUrl, backImageUrl, backgroundColor, setSelectedCard, typeLine, manaCost, isFlipped, ...props}) {
  const [isFocused, setIsFocused] = useState(false);
  const imageSource = isFlipped ? backImageUrl : imageUrl;
  const getItemTypeByTypeLine = () => {
    if (!typeLine) {
      return null;
    }
    if (typeLine.toLowerCase().indexOf("land") !== -1) {
      return ItemTypes.MTG_LAND_CARD;
    } else if (typeLine.toLowerCase().indexOf("sorcery") !== -1) {
      return ItemTypes.MTG_SORCERY_CARD;
    } else if (typeLine.toLowerCase().indexOf("instant") !== -1) {
      return ItemTypes.MTG_INSTANT_CARD;
    } else {
      return ItemTypes.MTG_NONLAND_PERMANENT_CARD
    }
  }
  const [{ isDragging }, drag] = useDrag(() => ({
    type: getItemTypeByTypeLine() || ItemTypes.MTG_CARD,
    item: {
      id: id,
      typeLine: typeLine,
      type: getItemTypeByTypeLine(),
    },
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
        borderRadius: "4%",
        transform: props?.annotations?.isTapped ? "rotate(90deg)" : "",
        ...props.sx,
      }}
      id={id}
      ref={drag}
      onMouseOver={registerFocus}
      onDoubleClick={props?.onDoubleClick}
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
