import { useRef } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';
import store from './../store/store';
import { receivedNewGameAction } from './../store/slice';

const SetHitpointDialog = ({open, setOpen, title, owner, ownerId}) => {
  const hp = owner?.hp;
  const valueRef = useRef();

  const handleClose = () => {
    setOpen(false);
  };

  const handleSubmit = () => {
    setOpen(false);
    registerSetHpAction(parseInt(valueRef.current.value));
  };

  const registerSetHpAction = (value) => {
    if (value === owner.hp) {
      return;
    }
    const newAction = {
      type: "set_hp",
      targetId: ownerId,
      value: value,
    };
    store.dispatch(receivedNewGameAction(newAction));
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm">
      <DialogTitle>
        {title}
      </DialogTitle>
      <DialogContent>
        <TextField
          id="outlined-number"
          type="number"
          defaultValue={hp ? hp.toString() : "0"}
          inputRef={valueRef}
        />
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
  );
} 

export default SetHitpointDialog;
