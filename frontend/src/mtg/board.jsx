import { useState, useEffect } from 'react'
import { PlayerInformation } from './player-information'
import { Hand } from './hand'
import { Battlefield } from './battlefield'
import { Bedrunner } from './bedrunner'
import Box from '@mui/material/Box'
import Grid from '@mui/material/Grid'

export function Board({boardData, ned, setNed, user, setUser, cardImageMap, setSelectedCard, ...props}) {
  const [whoseTurn, setWhoseTurn] = useState("user");
  const [whosePriority, setWhosePriority] = useState("user");
  const [phase, setPhase] = useState("");

  useEffect(() => {
    if (boardData.board_state) {
      setWhoseTurn(boardData.whose_turn);
      setWhosePriority(boardData.whose_priority);
      setPhase(boardData.phase);
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
    <Box sx={{display: 'flex', backgroundColor: 'White'}}>
      <Grid container direction="row" justifyContent="center" alignItems="stretch">
        <Grid item xs={2} sx={{backgroundColor: "Magenta", height: "16vh"}}>
          <PlayerInformation
            name="Ned Decker"
            hasTurn={whoseTurn === "ned"}
            hasPriority={whosePriority === "ned"}
            hp={ned.hp}
            infect={ned.infect}
          />
        </Grid>
        <Grid item xs={10} sx={{backgroundColor: "Magenta", height: "16vh"}}>
          <Hand
            content={ned.hand}
            map={cardImageMap}
            setSelectedCard={setSelectedCard}
          />
        </Grid>
        <Grid item xs={12} sx={{backgroundColor: "Magenta", height: "32vh"}}>
          <Battlefield
            content={ned.battlefield}
            library={ned.library}
            map={cardImageMap}
            setSelectedCard={setSelectedCard}
          />
        </Grid>
        <Grid item xs={12} sx={{backgroundColor: "Magenta", height: "4vh",
            display: "flex", alignItems: "center", justifyContent: "center"}}>
          <Bedrunner whoseTurn={whoseTurn} phase={phase}/>
        </Grid>
        <Grid item xs={12} sx={{backgroundColor: "Magenta", height: "32vh"}}>
          <Battlefield
            content={user.battlefield}
            library={user.library}
            map={cardImageMap}
            setSelectedCard={setSelectedCard}
          />
        </Grid>
        <Grid item xs={2} sx={{backgroundColor: "Magenta", height: "16vh"}} alignSelf="end">
          <PlayerInformation
            name="User"
            hasTurn={whoseTurn === "user"}
            hasPriority={whosePriority === "user"}
            hp={user.hp}
            infect={user.infect}
          />
        </Grid>
        <Grid item xs={10} sx={{backgroundColor: "Magenta", height: "16vh"}} alignSelf="end">
          <Hand
            content={user.hand}
            map={cardImageMap}
            setSelectedCard={setSelectedCard}
          />
        </Grid>
      </Grid>
    </Box>
  );
}
