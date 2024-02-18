import { useState, useEffect } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';

function MoveDialog({open, setOpen, card, userIndex, registerMoveAction}) {
  const handleClose = () => {setOpen(false);};
  const [selectedZone, setSelectedZone] = useState("");
  const whose = (index) => {
    if (index === userIndex) {return "user's ";}
    else {return "ned's ";}
  }
  const possibleZones = [
    {value: "board_state.stack", text: "stack"},
    {value: "board_state.players[0].battlefield", text: whose(0) + "battlefield"},
    {value: "board_state.players[0].hand", text: whose(0) + "hand"},
    {value: "board_state.players[0].graveyard", text: whose(0) + "graveyard"},
    {value: "board_state.players[1].battlefield", text: whose(1) + "battlefield"},
    {value: "board_state.players[1].hand", text: whose(1) + "hand"},
    {value: "board_state.players[1].graveyard", text: whose(1) + "graveyard"},
    {value: "board_state.players[0].library", text: whose(0) + "library"},
    {value: "board_state.players[1].library", text: whose(1) + "library"},
    {value: "board_state.players[0].exile", text: whose(0) + "exile"},
    {value: "board_state.players[1].exile", text: whose(1) + "exile"},
  ];
  const handleSubmit = () => {
    handleClose();
    registerMoveAction(card.id, selectedZone);
  };
  const handleChange = (e) => {
    setSelectedZone(e.target.value);
  }
  return (
    <>
      <Dialog open={open} onClose={handleClose} fullWidth={true} maxWidth="xs">
        <DialogTitle>
          Move { card ? card?.name : "Undefined" } to...
        </DialogTitle>
        <DialogContent>
          <Select onChange={handleChange} value={selectedZone} fullWidth={true}>
            {possibleZones.map((zone) => (
              <MenuItem key={zone.value} value={zone.value}>{zone.text}</MenuItem>
            ))}
          </Select>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSubmit}>Submit</Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default MoveDialog;
