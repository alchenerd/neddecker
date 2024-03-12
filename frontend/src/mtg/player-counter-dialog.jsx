import { useState } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Autocomplete, {createFilterOptions} from '@mui/material/Autocomplete';
import TextField from '@mui/material/TextField';
import store from './../store/store';
import { receivedNewGameAction } from './../store/slice';

const filter = createFilterOptions();

const PlayerCounterDialog = ({open, setOpen, owner, ownerId}) => {
  const [counterTypes, setCounterTypes] = useState(owner?.counters);
  const [counterType, setCounterType] = useState("");
  const [counterAmount, setCounterAmount] = useState(0);
  const handleChangeType = (event, newValue) => {
    console.log(newValue);
    if (newValue && newValue.inputValue) {
      setCounterType(newValue.inputValue);
    } else {
      setCounterType(newValue);
    }
  };
  const handleChangeAmount = (event) => {
    //console.log(event.target.value);
    setCounterAmount(parseInt(event.target.value));
  };
  const registerSetPlayerCounterAction = (type, amount) => {
    if (!type) {
      return;
    }
    const newAction = {
      type: "set_player_counter",
      targetId: ownerId,
      counterType: type,
      counterAmount: amount,
    };
    store.dispatch(receivedNewGameAction(newAction));
  }
  const handleSubmit = () => {
    setOpen(false);
    registerSetPlayerCounterAction(counterType, counterAmount);
  };
  const handleClose = () => {
    setOpen(false);
  };
  return (
    <Dialog open={open} onClose={handleClose}>
      <DialogTitle>
        {"Set counter on player " + owner?.player_name}
      </DialogTitle>
      <DialogContent>
        <Autocomplete
          id="counter-type"
          label="Type"
          freeSolo
          autoSelect
          clearOnBlur
          handleHomeEndKeys
          options={
            counterTypes.toString() || []
          }
          onChange={handleChangeType}
          filterOptions={(options, params) => {
            const filtered = filter(options, params);
            const { inputValue } = params;
            // Suggest the creation of a new value
            const isExisting = options.some((option) => inputValue === option);
            if (inputValue !== '' && !isExisting) {
              filtered.push(`${inputValue}`);
            }
            return filtered;
          }}
          renderInput={(params) => <TextField {...params} label="Counter type" />}
        />
        <TextField
          id="counter-amount"
          label="Amount"
          type="number"
          value={counterAmount || 0}
          onChange={handleChangeAmount}
          InputLabelProps={{
            shrink: true,
          }}
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

export default PlayerCounterDialog;
