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


function CreateTriggerDialog({open, setOpen, card}) {

  const registerCreateTriggerAction = (id, triggerContent) => {
    if (!id || !triggerContent) {
      return;
    }
    const newAction = {
      type: "create_trigger",
      targetId: id,
      triggerContent: triggerContent,
    };
    store.dispatch(receivedNewGameAction(newAction));
  }

  const [triggerContent, setTriggerContent] = useState("");

  useEffect(() => {
    if (open && triggerContent) {
      setTriggerContent("");
    }
  }, [open])

  const handleClose = () => {
    setOpen(false);
    setTriggerContent("");
  };

  const handleSubmit = () => {
    setOpen(false);
    registerCreateTriggerAction(card.in_game_id, triggerContent);
    setTriggerContent("");
  };

  const handleTriggerContentTextChange = (event) => {
    setTriggerContent(event.target.value);
  };

  return (
    <>
      <Dialog open={open} onClose={handleClose} fullWidth={true} maxWidth="sm">
        <DialogTitle>
          Create trigger for {card?.name || "Undefined"}
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
                id="trigger-content"
                label="Input desired trigger content:"
                fullWidth={true}
                multiline={true}
                rows={15}
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

export default CreateTriggerDialog;
