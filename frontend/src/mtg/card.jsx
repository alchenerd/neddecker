import {useState} from 'react'
import Paper from '@mui/material/Paper'

export function Card(props) {
  let id = props.id;
  let name = props.name;
  let imageUrl = props.imageUrl;
  let backImageUrl = props.backImageUrl;
  const [isFlipped, setIsFlipped] = useState(false);
  const imageSource = isFlipped ? backImageUrl : imageUrl;
  return (
    <Paper
      sx={{
        width: '0.96in',
        height: '1.26in',
        borderRadius: '5px',
        overflow: 'hidden',
      }}
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
