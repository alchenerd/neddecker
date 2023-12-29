import PlayerInformation from './player-information'
import { Hand } from './hand'
import Battlefield from './battlefield'
import Box from '@mui/material/Box'
import Grid from '@mui/material/Grid'

export function Board(props) {
  return (
    /* Should see neither magenta nor white */
    <Box sx={{display: 'flex', width: '100vw', height: '100vh', backgroundColor: 'White'}}>
      <Grid container direction="row" justifyContent="center" alignItems="stretch">
        <Grid item xs={2} sx={{backgroundColor: "Magenta", height: "17vh"}}>
          <PlayerInformation />
        </Grid>
        <Grid item xs={10} sx={{backgroundColor: "Magenta", height: "17vh"}}>
          <Hand />
        </Grid>
        <Grid item xs={12} sx={{backgroundColor: "Magenta", height: "33vh"}}>
          <Battlefield />
        </Grid>
        <Grid item xs={12} sx={{backgroundColor: "Magenta", height: "33vh"}}>
          <Battlefield />
        </Grid>
        <Grid item xs={2} sx={{backgroundColor: "Magenta", height: "17vh"}} alignSelf="end">
          <PlayerInformation />
        </Grid>
        <Grid item xs={10} sx={{backgroundColor: "Magenta", height: "17vh"}} alignSelf="end">
          <Hand />
        </Grid>
      </Grid>
    </Box>
  );
}
