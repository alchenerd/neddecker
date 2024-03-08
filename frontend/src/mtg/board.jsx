import { useState, useEffect } from 'react';
import { PlayerInformation } from './player-information';
import Hand from './hand';
import Battlefield from './battlefield';
import { Bedrunner } from './bedrunner';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';

export function Board({
  setFocusedCard,
  setDndMsg,
  setDblClkMsg,
  setWhoRequestShuffle,
  actionTargetCard,
  setActionTargetCard,
  setOpenMoveDialog,
  setOpenCounterDialog,
  setOpenAnnotationDialog,
  setOpenCreateTriggerDialog,
  setOpenCreateDelayedTriggerDialog,
}) {
  const [ whoIsAskingAttackTarget, setWhoIsAskingAttackTarget ] = useState(null);
  const [ whoIsAskingBlockTarget, setWhoIsAskingBlockTarget ] = useState(null);
  const [ combatTargetCard, setCombatTargetCard ] = useState(null);

  return (
    /* Should see neither magenta nor white */
    <Box sx={{display: 'flex', backgroundColor: 'White'}}>
      <Grid container direction="row" justifyContent="center" alignItems="stretch">
        <Grid item xs={3} sx={{backgroundColor: "Magenta", height: "16vh"}}>
          <PlayerInformation
            ownerName="ned"
            fullName="Ned Decker"
            setActionTargetCard={setActionTargetCard}
            setOpenMoveDialog={setOpenMoveDialog}
            setOpenCounterDialog={setOpenCounterDialog}
            setOpenAnnotationDialog={setOpenAnnotationDialog}
            setOpenCreateTriggerDialog={setOpenCreateTriggerDialog}
            setOpenCreateDelayedTriggerDialog={setOpenCreateDelayedTriggerDialog}
          />
        </Grid>
        <Grid item xs={9} sx={{backgroundColor: "Magenta", height: "16vh"}}>
          <Hand
            ownerName="ned"
            setFocusedCard={setFocusedCard}
            setDndMsg={setDndMsg}
            setActionTargetCard={setActionTargetCard}
            setOpenMoveDialog={setOpenMoveDialog}
            setOpenCreateTriggerDialog={setOpenCreateTriggerDialog}
            setOpenCreateDelayedTriggerDialog={setOpenCreateDelayedTriggerDialog}
          />
        </Grid>
        <Grid item xs={12} sx={{backgroundColor: "Magenta", height: "32vh"}}>
          <Battlefield
            key="ned-battlefield"
            ownerName="ned"
            setFocusedCard={setFocusedCard}
            setDndMsg={setDndMsg}
            setDblClkMsg={setDblClkMsg}
            setWhoRequestShuffle={setWhoRequestShuffle}
            setActionTargetCard={setActionTargetCard}
            setOpenMoveDialog={setOpenMoveDialog}
            setOpenCounterDialog={setOpenCounterDialog}
            setOpenAnnotationDialog={setOpenAnnotationDialog}
            setOpenCreateTriggerDialog={setOpenCreateTriggerDialog}
            setOpenCreateDelayedTriggerDialog={setOpenCreateDelayedTriggerDialog}
            {...{whoIsAskingAttackTarget, setWhoIsAskingAttackTarget}}
            {...{whoIsAskingBlockTarget, setWhoIsAskingBlockTarget}}
            {...{combatTargetCard, setCombatTargetCard}}
          />
        </Grid>
        <Grid item xs={12} sx={{backgroundColor: "Magenta", height: "4vh",
            display: "flex", alignItems: "center", justifyContent: "center"}}>
          <Bedrunner />
        </Grid>
        <Grid item xs={12} sx={{backgroundColor: "Magenta", height: "32vh"}}>
          <Battlefield
            key="user-battlefield"
            ownerName="user"
            setFocusedCard={setFocusedCard}
            setDndMsg={setDndMsg}
            setDblClkMsg={setDblClkMsg}
            setWhoRequestShuffle={setWhoRequestShuffle}
            setActionTargetCard={setActionTargetCard}
            setOpenMoveDialog={setOpenMoveDialog}
            setOpenCounterDialog={setOpenCounterDialog}
            setOpenAnnotationDialog={setOpenAnnotationDialog}
            setOpenCreateTriggerDialog={setOpenCreateTriggerDialog}
            setOpenCreateDelayedTriggerDialog={setOpenCreateDelayedTriggerDialog}
            {...{whoIsAskingAttackTarget, setWhoIsAskingAttackTarget}}
            {...{whoIsAskingBlockTarget, setWhoIsAskingBlockTarget}}
            {...{combatTargetCard, setCombatTargetCard}}
          />
        </Grid>
        <Grid item xs={3} sx={{backgroundColor: "Magenta", height: "16vh"}} alignSelf="end">
          <PlayerInformation
            ownerName="user"
            fullName="User"
            setActionTargetCard={setActionTargetCard}
            setOpenMoveDialog={setOpenMoveDialog}
            setOpenCounterDialog={setOpenCounterDialog}
            setOpenAnnotationDialog={setOpenAnnotationDialog}
            setOpenCreateTriggerDialog={setOpenCreateTriggerDialog}
            setOpenCreateDelayedTriggerDialog={setOpenCreateDelayedTriggerDialog}
          />
        </Grid>
        <Grid item xs={9} sx={{backgroundColor: "Magenta", height: "16vh"}} alignSelf="end">
          <Hand
            ownerName="user"
            setFocusedCard={setFocusedCard}
            setDndMsg={setDndMsg}
            setActionTargetCard={setActionTargetCard}
            setOpenMoveDialog={setOpenMoveDialog}
            setOpenCreateTriggerDialog={setOpenCreateTriggerDialog}
            setOpenCreateDelayedTriggerDialog={setOpenCreateDelayedTriggerDialog}
          />
        </Grid>
      </Grid>
    </Box>
  );
}
