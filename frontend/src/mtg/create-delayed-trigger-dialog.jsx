import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Grid from '@mui/material/Grid';
import TextField from '@mui/material/TextField';
import { useState, useEffect } from 'react';
import { Card } from './card';
import { receivedNewGameAction } from './../store/slice';
import store from './../store/store';


function CreateDelayedTriggerDialog({open, setOpen, card}) {

  const registerCreateDelayedTriggerAction = (id, name, triggerWhen, triggerContent) => {
    if (!id || !name || !triggerWhen || !triggerContent) {
      return;
    }
    const newAction = {
      type: "create_delayed_trigger",
      targetId: id,
      targetCardName: name,
      triggerWhen: triggerWhen,
      triggerContent: triggerContent,
    };
    store.dispatch(receivedNewGameAction(newAction));
  }

  const [triggerWhen, setTriggerWhen] = useState("");
  const [triggerContent, setTriggerContent] = useState("");

  useEffect(() => {
    if (open) {
      setTriggerWhen(card?.oracle_text || "");
    }
  }, [open]);

  useEffect(() => {
    if (open) {
      setTriggerContent(card?.oracle_text || "");
    }
  }, [open]);

  const handleClose = () => {
    setOpen(false);
    setTriggerWhen("");
    setTriggerContent("");
  };

  const handleSubmit = () => {
    setOpen(false);
    registerCreateDelayedTriggerAction(card.in_game_id, card.name, triggerWhen, triggerContent);
    setTriggerWhen("");
    setTriggerContent("");
  };

  const handleTriggerWhenTextChange = (event) => {
    setTriggerWhen(event.target.value);
  };

  const handleTriggerContentTextChange = (event) => {
    setTriggerContent(event.target.value);
  };

  return (
    <>
      <Dialog open={open} onClose={handleClose} fullWidth={true} maxWidth="sm">
        <DialogTitle>
          Create delayed trigger for {card?.name || "Undefined"}
        </DialogTitle>
        <DialogContent sx={{overflowY: "visible"}}>
          <Grid container spacing={2} direction="row">
            <Grid item xs={6} display="flex" justifyContent="center" alignItems="center">
              <Card
                id="card-preview"
                canDrag="false"
                card={card}
                backgroundColor="maroon"
              />
            </Grid>
            <Grid container item spacing={2} xs={6} direction="column" display="flex" flexDirection="column" justifyContent="center" alignItems="stretch">
              <TextField
                id="trigger-when"
                label="Input when the trigger is created (Whenever...):"
                fullWidth={true}
                value={triggerWhen}
                onChange={handleTriggerWhenTextChange}
                InputLabelProps={{
                  shrink: true,
                }}
              />
              <TextField
                id="trigger-content"
                label="Input desired trigger content:"
                fullWidth={true}
                multiline={true}
                rows={12}
                value={triggerContent}
                onChange={handleTriggerContentTextChange}
                InputLabelProps={{
                  shrink: true,
                }}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>
            Close
          </Button>
          <Button onClick={handleSubmit}>
            Submit
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

export default CreateDelayedTriggerDialog;
