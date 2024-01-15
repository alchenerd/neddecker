import { useState, useEffect } from 'react'
import { PlayerInformation } from './player-information'
import { Hand } from './hand'
import { Battlefield } from './battlefield'
import { Bedrunner } from './bedrunner'
import Box from '@mui/material/Box'
import Grid from '@mui/material/Grid'

export function Board({boardData, ned, setNed, user, setUser, cardImageMap, setSelectedCard, setDndMsg, ...props}) {

  useEffect(() => {
    if (boardData.board_state) {
      setUser(boardData.board_state.players.find((player) => player.player_name === "user"));
      setNed(boardData.board_state.players.find((player) => player.player_name === "ned"));
    }
  }, [boardData]);

  /*
  useEffect(() => {
    console.log(ned);
    console.log(user);
  }, [ned, user]);
  */

  return (
    /* Should see neither magenta nor white */
    <Box sx={{display: 'flex', backgroundColor: 'White'}}>
      <Grid container direction="row" justifyContent="center" alignItems="stretch">
        <Grid item xs={2} sx={{backgroundColor: "Magenta", height: "16vh"}}>
          <PlayerInformation
            name="Ned Decker"
            hasTurn={boardData.whose_turn === "ned"}
            hasPriority={boardData.whose_priority === "ned"}
            hp={ned.hp}
            infect={ned.infect}
          />
        </Grid>
        <Grid item xs={10} sx={{backgroundColor: "Magenta", height: "16vh"}}>
          <Hand
            map={cardImageMap}
            setSelectedCard={setSelectedCard}
            owner={ned}
            setDndMsg={setDndMsg}
          />
        </Grid>
        <Grid item xs={12} sx={{backgroundColor: "Magenta", height: "32vh"}}>
          <Battlefield
            library={ned.library}
            map={cardImageMap}
            setSelectedCard={setSelectedCard}
            owner={ned}
            setDndMsg={setDndMsg}
          />
        </Grid>
        <Grid item xs={12} sx={{backgroundColor: "Magenta", height: "4vh",
            display: "flex", alignItems: "center", justifyContent: "center"}}>
          <Bedrunner whoseTurn={boardData ? boardData.whose_turn : "unknown"} phase={boardData ? boardData.phase : "unknown"}/>
        </Grid>
        <Grid item xs={12} sx={{backgroundColor: "Magenta", height: "32vh"}}>
          <Battlefield
            library={user.library}
            map={cardImageMap}
            setSelectedCard={setSelectedCard}
            owner={user}
            setDndMsg={setDndMsg}
          />
        </Grid>
        <Grid item xs={2} sx={{backgroundColor: "Magenta", height: "16vh"}} alignSelf="end">
          <PlayerInformation
            name="User"
            hasTurn={boardData.whose_turn === "user"}
            hasPriority={boardData.whose_priority === "user"}
            hp={user.hp}
            infect={user.infect}
          />
        </Grid>
        <Grid item xs={10} sx={{backgroundColor: "Magenta", height: "16vh"}} alignSelf="end">
          <Hand
            map={cardImageMap}
            setSelectedCard={setSelectedCard}
            owner={user}
            setDndMsg={setDndMsg}
          />
        </Grid>
      </Grid>
    </Box>
  );
}
