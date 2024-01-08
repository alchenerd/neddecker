import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Grid from '@mui/material/Grid'
import { Preview } from './preview'
import { Stack } from './stack'
export function GameInformation({selectedCard, setSelectedCard, whoseTurn, ...props}) {
  return (
    <Box sx={{display: "flex", alignItems: "space-between", height: "100%", width: "100%", backgroundColor: "cyan"}}>
      <Grid container sx={{height: "100%"}}>
        <Grid item xs={6} sx={{height: "90%"}}>
          <Preview selectedCard={selectedCard} />
        </Grid>
        <Grid item xs={6} sx={{height: "90%"}}>
          <Stack />
        </Grid>
        <Grid item xs={6} sx={{height: "10%"}}>
          <Button
            variant="contained"
            sx={{width: "100%", height: "100%"}}
          >
            Pass Priority
          </Button>
        </Grid>
        <Grid item xs={6} sx={{height: "10%"}}>
          <Button
            variant="contained"
            color="error"
            sx={{width: "100%", height: "100%"}}
            disabled={whoseTurn !== "user"}
          >
            End Turn
          </Button>
        </Grid>
      </Grid>
    </Box>
  )
}
