import { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import { useAffectedGameDataSelector } from './../store/slice';
import ZoneButton from './zone-button';
import PlayerContextMenu from './player-context-menu';
import InspectDialog from './inspect-dialog';
import ManaPool from './mana-pool';
import SetHitpointDialog from './set-hitpoint-dialog';

export function PlayerInformation({
  ownerName, fullName,
  setActionTargetCard,
  setOpenMoveDialog,
  setOpenCounterDialog,
  setOpenAnnotationDialog,
  setOpenCreateTriggerDialog,
  setOpenCreateDelayedTriggerDialog,
}) {
  const [ contextMenu, setContextMenu ] = useState(null);
  const [ openInspectSideboardDialog, setOpenInspectSideboardDialog ] = useState(false);
  const [ openSetHitpointDialog, setOpenSetHitpointDialog ] = useState(true);
  const affectedGameData = useAffectedGameDataSelector();
  const hasTurn = affectedGameData?.whose_turn === ownerName;
  const owner = affectedGameData?.board_state?.players.find((player) => player.player_name === ownerName);
  const ownerId = affectedGameData?.board_state?.players.findIndex(player => player.player_name === ownerName);
  const hp = owner?.hp;
  const infect = owner?.infect;
  const manaPool = owner?.mana_pool;
  const handleContextMenu = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    e.preventDefault();
    setContextMenu(
      contextMenu === null ? { mouseX: rect.left, mouseY: rect.bottom }
                           : null
    );
  };
  return (
    <>
      <Box
        justifyContent='center'
        sx={{
          display: 'flex', flexDirection: 'column',
          width: '100%', height: '100%',
          background: "red"
        }}
        position="relative"
      >
        <Grid container direction='row' justifyContent='space-around' alignItems='center'>
          <Grid container direction='column' item xs={12}>
            <Typography>{fullName}{hasTurn && "(*)"}</Typography>
            <Typography>HP: {hp}</Typography>
            <Typography>Infect: {infect}</Typography>
          </Grid>
          <ManaPool {...{manaPool, ownerId}}/>
        </Grid>
        <Box
          display="flex"
          justifyContent="flex-end"
          alignSelf="flex-end"
          position="absolute"
          top="0px"
          right="0px"
        >
          <IconButton aria-label="show-more" onClick={handleContextMenu}>
            <MoreVertIcon />
          </IconButton>
        </Box>
      </Box>
      <PlayerContextMenu
        {...{ contextMenu, setContextMenu }}
        functions={[
          {
            name: "sideboard",
            _function: () => {
              setOpenInspectSideboardDialog(true);
            }
          },
          {
            name: "set hitpoint",
            _function: () => {
              setOpenSetHitpointDialog(true);
            }
          },
        ]}
      />
      <InspectDialog
        open={openInspectSideboardDialog}
        setOpen={setOpenInspectSideboardDialog}
        title={ownerName + "'s " + "sideboard"}
        zoneName={"sideboard"}
        content={owner?.sideboard}
        setActionTargetCard={setActionTargetCard}
        setOpenMoveDialog={setOpenMoveDialog}
        setOpenCounterDialog={setOpenCounterDialog}
        setOpenAnnotationDialog={setOpenAnnotationDialog}
        setOpenCreateTriggerDialog={setOpenCreateTriggerDialog}
        setOpenCreateDelayedTriggerDialog={setOpenCreateDelayedTriggerDialog}
      />
      <SetHitpointDialog
        open={openSetHitpointDialog}
        setOpen={setOpenSetHitpointDialog}
        title={"Set " + ownerName + "'s HP"}
        owner={owner}
        ownerId={ownerId}
      />
    </>
  );
}
