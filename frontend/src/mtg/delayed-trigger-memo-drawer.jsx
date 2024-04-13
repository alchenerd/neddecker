import { useState, useEffect } from 'react';
import Button from '@mui/material/Button';
import Drawer from '@mui/material/Drawer';
import IconButton from '@mui/material/IconButton';
import EventNoteIcon from '@mui/icons-material/EventNote';
import DeleteIcon from '@mui/icons-material/Delete';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemText from '@mui/material/ListItemText';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import store from './../store/store';
import { receivedNewGameAction, selectAffectedGameData } from './../store/slice';
import { useSelector } from 'react-redux';
import _ from 'lodash';

function PaperComponent(props) {
  return (
    <Draggable>
    <Paper {...props} />
    </Draggable>
  )
}

function DelayedTriggerMemoDrawer({open, setOpen}) {
  const affectedGameData = useSelector(selectAffectedGameData);
  const nedIndex = affectedGameData?.board_state?.players.findIndex((player) => player.player_name === 'ned');
  const existingDelayedTriggersForNed = affectedGameData?.board_state?.players[nedIndex].delayed_triggers || [];
  const userIndex = affectedGameData?.board_state?.players.findIndex((player) => player.player_name === 'user');
  const existingDelayedTriggersForUser = affectedGameData?.board_state?.players[userIndex].delayed_triggers || [];
  const createdDelayedTriggers = useSelector((state) => state.gameState.actions).filter((action) => action.type === "create_delayed_trigger");
  const removedDelayedTriggers = useSelector((state) => state.gameState.actions).filter((action) => action.type === "remove_delayed_trigger");
  const delayedTriggersToShow = existingDelayedTriggersForNed.concat(existingDelayedTriggersForUser, createdDelayedTriggers);
  const shownDelayedTriggers = delayedTriggersToShow.filter(cTrigger => !removedDelayedTriggers.some(rTrigger => rTrigger.targetId === cTrigger.targetId))

  useEffect(() => {
    if (!shownDelayedTriggers.length) {
      handleClose();
    }
  }, [shownDelayedTriggers]);

  const handleClose = () => {
    setOpen(false);
  }
  const handleOpen = () => {
    setOpen(true);
  }
  const registerRemoveDelayedTriggerAction = (id, who) => {
    if (!id || !who) {
      console.log("no needed parameters");
      return;
    }
    const newAction = {
      type: "remove_delayed_trigger",
      targetId: id,
      affectingWho: who,
    };
    store.dispatch(receivedNewGameAction(newAction));
    console.log("action sent")
  }
  if (shownDelayedTriggers.length) {
    return (
      <>
      <IconButton
        color="primary"
        aria-label="open drawer"
        edge="end"
        onClick={handleOpen}
        sx={{ ...(open && { display: 'none' }), position: "absolute", top: "50%", right: "0", backgroundColor: "black"}}
      >
        <EventNoteIcon />
      </IconButton>
      <Drawer open={open} onClose={handleClose} anchor="right" PaperProps={{sx: {width: "40%"}, }}>
        <List>
          {
            shownDelayedTriggers.map((trigger) => {
              const handleClickDeleteButton = () => {
                console.log("clicked!")
                registerRemoveDelayedTriggerAction(trigger.targetId, trigger.affectingWho);
              }
              return (
                <ListItem key={JSON.stringify(trigger)}>
                  <ListItemText primary={((trigger.targetId.startsWith("u"))? "User's " : "Ned's ") + trigger.targetCardName + " (" + trigger.targetId + ") affecting " + trigger.affectingWho} secondary={trigger.triggerWhen + ", " + trigger.triggerContent} />
                  <ListItemButton onClick={handleClickDeleteButton}>
                    <ListItemIcon>
                      <DeleteIcon />
                    </ListItemIcon>
                  </ListItemButton>
                </ListItem>
              )
            })}
        </List>
      </Drawer>
      </>
    )
  }
  return null;
}

export default DelayedTriggerMemoDrawer;
