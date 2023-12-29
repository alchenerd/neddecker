import {useState} from 'react'
import Paper from '@mui/material/Paper'

export function Card(props) {
  const id = props.id;
  const name = props.name;
  const imageUrl = props.imageUrl;
  const backImageUrl = props.backImageUrl;
  const backgroundColor = props.backgroundColor;
  const [isFlipped, setIsFlipped] = useState(false);
  const imageSource = isFlipped ? backImageUrl : imageUrl;
  return (
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
        src={imageSource}
        alt={name}
        height='100%'
        width='100%'
      />
    </Paper>
  );
}
