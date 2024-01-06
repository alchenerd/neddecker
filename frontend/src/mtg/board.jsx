import { useState, useEffect } from 'react'
import { PlayerInformation } from './player-information'
import { Hand } from './hand'
import { Battlefield } from './battlefield'
import Box from '@mui/material/Box'
import Grid from '@mui/material/Grid'

export function Board({boardData, ned, setNed, user, setUser, cardImageMap, ...props}) {
  const [whoseTurn, setWhoseTurn] = useState("user");
  const [whosePriority, setWhosePriority] = useState("user");

  useEffect(() => {
    if (boardData.board_state) {
      setWhoseTurn(boardData.whose_turn);
      setWhosePriority(boardData.whose_priority);
      setUser(boardData.board_state.players.find((player) => player.player_name === "user"));
      setNed(boardData.board_state.players.find((player) => player.player_name === "ned"));
    }
  }, [boardData]);

  useEffect(() => {
    console.log(ned);
    console.log(user);
  }, [ned, user]);

  return (
    /* Should see neither magenta nor white */
    <Box sx={{display: 'flex', width: '100vw', height: '100vh', backgroundColor: 'White'}}>
      <Grid container direction="row" justifyContent="center" alignItems="stretch">
        <Grid item xs={2} sx={{backgroundColor: "Magenta", height: "17vh"}}>
          <PlayerInformation
            name="Ned Decker"
            hasTurn={whoseTurn === "ned"}
            hasPriority={whosePriority === "ned"}
            hp={ned.hp}
            infect={ned.infect}
          />
        </Grid>
        <Grid item xs={10} sx={{backgroundColor: "Magenta", height: "17vh"}}>
          <Hand content={ned.hand} map={cardImageMap} />
        </Grid>
        <Grid item xs={12} sx={{backgroundColor: "Magenta", height: "33vh"}}>
          <Battlefield content={ned.battlefield} library={ned.library} map={cardImageMap} />
        </Grid>
        <Grid item xs={12} sx={{backgroundColor: "Magenta", height: "33vh"}}>
          <Battlefield content={user.battlefield} library={user.library} map={cardImageMap} />
        </Grid>
        <Grid item xs={2} sx={{backgroundColor: "Magenta", height: "17vh"}} alignSelf="end">
          <PlayerInformation
            name="User"
            hasTurn={whoseTurn === "user"}
            hasPriority={whosePriority === "user"}
            hp={user.hp}
            infect={user.infect}
          />
        </Grid>
        <Grid item xs={10} sx={{backgroundColor: "Magenta", height: "17vh"}} alignSelf="end">
          <Hand content={user.hand} map={cardImageMap} />
        </Grid>
      </Grid>
    </Box>
  );
}
