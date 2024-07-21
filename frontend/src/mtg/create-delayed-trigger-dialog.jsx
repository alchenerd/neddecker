import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Grid from '@mui/material/Grid';
import TextField from '@mui/material/TextField';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import InputLabel from '@mui/material/InputLabel';
import FormControl from '@mui/material/FormControl';
import { useState, useEffect } from 'react';
import { Card } from './card';
import { receivedNewGameAction } from './../store/slice';
import store from './../store/store';


function CreateDelayedTriggerDialog({open, setOpen, card}) {
  const [ affectingWho, setAffectingWho ] = useState("user");
  const playerNames = ["user", "ned"];

  const registerCreateDelayedTriggerAction = (who, id, name, triggerWhen, triggerContent) => {
    if (!id || !name || !triggerWhen || !triggerContent) {
      return;
    }
    const newAction = {
      type: "create_delayed_trigger",
      targetId: id,
      targetCardName: name,
      affectingWho: who,
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
    registerCreateDelayedTriggerAction(affectingWho, card.in_game_id, card.name, triggerWhen, triggerContent);
    setTriggerWhen("");
    setTriggerContent("");
  };

  const handleTriggerWhenTextChange = (event) => {
    setTriggerWhen(event.target.value);
  };

  const handleTriggerContentTextChange = (event) => {
    setTriggerContent(event.target.value);
  };

  const handleAffectingWhoTextChange = (event) => {
    setAffectingWho(event.target.value);
  };

  return (
    <>
      <Dialog open={open} onClose={handleClose} fullWidth={true} maxWidth="md">
        <DialogTitle>
          Create delayed trigger for {card?.name || "Undefined"}
        </DialogTitle>
        <DialogContent sx={{overflowY: "visible"}}>
          <Grid container spacing={4} direction="row">
            <Grid item xs={6} display="flex" justifyContent="center" alignItems="center">
              <Card
                id="card-preview"
                canDrag="false"
                card={card}
                backgroundColor="maroon"
              />
            </Grid>
            <Grid container item spacing={2} xs={6} direction="column" display="flex" flexDirection="column" justifyContent="center" alignItems="stretch">
              <Grid item>
                <FormControl fullWidth>
                  <InputLabel id="select-who-label">Affecting Who</InputLabel>
                  <Select
                    labelId="select-who-label"
                    value={affectingWho}
                    onChange={handleAffectingWhoTextChange}
                    label="Affecting Who"
                  >
                    {playerNames.map((name) => (
                      <MenuItem key={name} value={name}>{name}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item>
                <FormControl fullWidth>
                  <TextField
                    id="trigger-when"
                    label="Trigger when"
                    fullWidth={true}
                    value={triggerWhen}
                    onChange={handleTriggerWhenTextChange}
                    InputLabelProps={{
                      shrink: true,
                    }}
                  />
                </FormControl>
              </Grid>
              <Grid item>
                <FormControl fullWidth>
                  <TextField
                    id="trigger-content"
                    label="Trigger content"
                    fullWidth={true}
                    multiline={true}
                    rows={17}
                    value={triggerContent}
                    onChange={handleTriggerContentTextChange}
                    InputLabelProps={{
                      shrink: true,
                    }}
                  />
                </FormControl>
              </Grid>
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
