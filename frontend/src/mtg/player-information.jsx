import { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import Popover from '@mui/material/Popover';
import { selectAffectedGameData } from './../store/slice';
import store from './../store/store';
import ZoneButton from './zone-button';
import PlayerContextMenu from './player-context-menu';
import InspectDialog from './inspect-dialog';
import ManaPool from './mana-pool';
import SetHitpointDialog from './set-hitpoint-dialog';
import PlayerCounterDialog from './player-counter-dialog';
import PlayerAnnotationDialog from './player-annotation-dialog';

const ListCounters = ({target}) => {
  if (target?.counters && target?.counters.length) {
    return (
      <>
        <Typography>Counters</Typography>
        {target?.counters.map((counter) => (
          <Typography key={counter.type}>
            {counter.type}: {counter.amount}
          </Typography>
        ))}
      </>
    )
  }
};

const ListAnnotations = ({target}) => {
  if (target?.annotations && Object.keys(target?.annotations).filter((key) => key !== "isTapped").length) {
    return (
      <>
        <Typography>Annotations</Typography>
        {Object.keys(target?.annotations).filter((key) => key !== "isTapped").map((key) => (
          <Typography key={key}>
            {key}: {String(target?.annotations[key])}
          </Typography>
        ))}
      </>
    )
  }
  return null
};

export function PlayerInformation({
  ownerName, fullName,
  setActionTargetCard,
  setOpenMoveDialog,
  setOpenCounterDialog,
  setOpenAnnotationDialog,
  setOpenCreateTriggerDialog,
  setOpenCreateDelayedTriggerDialog,
  setOpenCreateTokenDialog,
}) {
  const [ contextMenu, setContextMenu ] = useState(null);
  const [ openInspectSideboardDialog, setOpenInspectSideboardDialog ] = useState(false);
  const [ openSetHitpointDialog, setOpenSetHitpointDialog ] = useState(false);
  const [ openPlayerCounterDialog, setOpenPlayerCounterDialog ] = useState(false);
  const [ openPlayerAnnotationDialog, setOpenPlayerAnnotationDialog ] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const openCAPopover = Boolean(anchorEl);
  const _agd = selectAffectedGameData(store.getState());
  const hasTurn = _agd?.whose_turn === ownerName;
  const owner = _agd?.board_state?.players.find((player) => player.player_name === ownerName);
  const ownerId = _agd?.board_state?.players.findIndex(player => player.player_name === ownerName);
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
  const handlePopoverOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };
  const handlePopoverClose = (event) => {
    setAnchorEl(null);
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
        onMouseEnter={handlePopoverOpen}
        onMouseLeave={handlePopoverClose}
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
          {
            name: "set player counter",
            _function: () => {
              setOpenPlayerCounterDialog(true);
            }
          },
          {
            name: "set player annotation",
            _function: () => {
              setOpenPlayerAnnotationDialog(true);
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
        setOpenCreateTokenDialog={setOpenCreateTokenDialog}
      />
      <SetHitpointDialog
        open={openSetHitpointDialog}
        setOpen={setOpenSetHitpointDialog}
        title={"Set " + ownerName + "'s HP"}
        owner={owner}
        ownerId={ownerId}
      />
      <PlayerCounterDialog
        open={openPlayerCounterDialog}
        setOpen={setOpenPlayerCounterDialog}
        owner={owner}
        ownerId={ownerId}
      />
      <PlayerAnnotationDialog
        open={openPlayerAnnotationDialog}
        setOpen={setOpenPlayerAnnotationDialog}
        owner={owner}
        ownerId={ownerId}
      />
      <Popover id="player-counter-annotation-popover"
        open={openCAPopover && (owner?.counters?.length > 0 || Object.keys(owner?.annotations || {}).filter((key) => key !== "isTapped").length > 0)}
        anchorEl={anchorEl}
        sx={{
          pointerEvents: 'none',
        }}
        anchorOrigin={{
          vertical: 'center',
          horizontal: 'right',
        }}
        transformOrigin={{
          vertical: 'center',
          horizontal: 'left',
        }}
        onClose={handlePopoverClose}
        disableRestoreFocus
      >
        <ListCounters target={owner} />
        <ListAnnotations target={owner} />
      </Popover>
    </>
  );
}
