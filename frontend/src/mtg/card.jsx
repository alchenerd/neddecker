import { useState } from 'react'
import Paper from '@mui/material/Paper'
import { useDrag } from 'react-dnd'
import { ItemTypes } from './constants'

export function Card(props) {
  const id = props.id;
  const name = props.name;
  const imageUrl = props.imageUrl;
  const backImageUrl = props.backImageUrl;
  const backgroundColor = props.backgroundColor;
  const [isFlipped, setIsFlipped] = useState(false);
  const imageSource = isFlipped ? backImageUrl : imageUrl;
  const [{ isDragging }, drag] = useDrag(() => ({
    type: ItemTypes.MTG_CARD,
    item: {id: id},
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging()
    })
  }))

  return (
    <div ref={drag}>
    <Paper
      sx={{
        width: '0.96in',
        height: '1.26in',
        borderRadius: '5px',
        overflow: 'hidden',
        backgroundColor: backgroundColor,
      }}
      id={id}
    >
      <img
        src={isFlipped? backImageUrl : imageUrl}
        alt={name}
        height='100%'
        width='100%'
        style={{opacity: isDragging? 0.5 : 1,}}
      />
    </Paper>
    </div>
  );
}
