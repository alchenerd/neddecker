import { useState } from 'react'
import Box from '@mui/material/Box'
import Button from '@mui/material/Button'
import Grid from '@mui/material/Grid'
import { Preview } from './preview'
import { Stack } from './stack'
import { useAffectedGameDataSelector } from './../store/slice';

export function GameInformation({focusedCard, setFocusedCard, setUserIsDone, userEndTurn, setUserEndTurn, setDndMsg, setActionTargetCard, setOpenMoveDialog, setOpenCounterDialog, setOpenAnnotationDialog, ...props}) {
  const [ isResolving, setIsResolving ] = useState(false);
  const handleClickDoneButton = () => {
    setUserIsDone(true);
  }
  const handleClickEndTurnButton = () => {
    setUserEndTurn(true);
  }
  const whoseTurn = useAffectedGameDataSelector()?.whose_turn || "";
  const stack = useAffectedGameDataSelector()?.board_state?.stack || [];
  return (
    <Box sx={{display: "flex", alignItems: "space-between", height: "100%", width: "100%", backgroundColor: "cyan"}}>
      <Grid container sx={{height: "100%"}}>
        <Grid item xs={6} sx={{height: "90%"}}>
          <Preview focusedCard={focusedCard} />
        </Grid>
        <Grid item xs={6} sx={{height: "90%"}}>
          <Stack
            setFocusedCard={setFocusedCard}
            setDndMsg={setDndMsg}
            setActionTargetCard={setActionTargetCard}
            setOpenMoveDialog={setOpenMoveDialog}
            setOpenCounterDialog={setOpenCounterDialog}
            setOpenAnnotationDialog={setOpenAnnotationDialog}
          />
        </Grid>
        <Grid item xs={6} sx={{height: "10%"}}>
          <Button
            id="doneButton"
            variant="contained"
            sx={{width: "100%", height: "100%"}}
            onClick={handleClickDoneButton}
          >
            { isResolving ? `Resolve` : `Pass` }
          </Button>
        </Grid>
        <Grid item xs={6} sx={{height: "10%"}}>
          <Button
            variant="contained"
            color="error"
            sx={{width: "100%", height: "100%"}}
            disabled={userEndTurn || whoseTurn !== "user" || stack.length > 0}
            onClick={handleClickEndTurnButton}
          >
            End Turn
          </Button>
        </Grid>
      </Grid>
    </Box>
  )
}
