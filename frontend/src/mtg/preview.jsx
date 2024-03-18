import Box from '@mui/material/Box'
import { Card } from './card'
export function Preview({focusedCard, ...props}) {
  return (
    <Box backgroundColor='#123456'
      sx={{height: "100%", overflow: "hidden"}}
      display="flex"
      alignItems="center"
      justifyContent="center"
    >
      <Card
        canDrag="false"
        card={focusedCard}
        sx={{
          height: "95%",
          borderRadius: "12px",
          backgroundColor: focusedCard?.in_game_id.startsWith("token") ? "white": "transparent",
        }}
      />
    </Box>
  );
}
