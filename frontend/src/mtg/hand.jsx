import Box from '@mui/material/Box'
import { Card } from './card'

export function Hand(props) {
  const content = props.content || [];
  const dir = props.dir || "row";

  return (
    <>
      <Box
        sx={{
          display: 'flex',
          width: '100%',
          height: '100%',
          background: "green",
          flexDirection: dir,
          overflow: "auto",
        }}>
        {content.map(card => {return <Card key={card.id} id={card.id} imageUrl={card.imageUrl} />})}
      </Box>
    </>
  );
}
