import Box from '@mui/material/Box'
import { Card } from './card'
export function Preview({selectedCard, ...props}) {
  return (
    <Box backgroundColor='#123456'
      sx={{height: "100%", overflow: "hidden"}}
      display="flex"
      alignItems="center"
      justifyContent="center"
    >
      <Card
        canDrag="false"
        imageUrl={selectedCard || ''}
        sx={{
          height: "95%",
          borderRadius: "12px",
          backgroundColor: "transparent",
        }}
      />
    </Box>
  );
}
