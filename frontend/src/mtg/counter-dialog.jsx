import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Grid from '@mui/material/Grid';
import TextField from '@mui/material/TextField';
import Autocomplete, {createFilterOptions} from '@mui/material/Autocomplete';
import { Card } from './card';
import { useState, useEffect } from 'react';

const filter = createFilterOptions();

function CounterDialog({open, setOpen, card, setCardCounter, registerCounterAction}) {
  useEffect(() => {
    if (open) {
      setCounterType(null);
      setCounterAmount(null);
    }
  }, [open]);
  const handleClose = () => {
    setOpen(false);
  };
  const [counterType, setCounterType] = useState(null);
  const [counterAmount, setCounterAmount] = useState(null);
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
    setCounterAmount(event.target.value);
  };
  const handleSubmit = () => {
    setOpen(false);
    setCardCounter({type: counterType, amount: counterAmount});
    registerCounterAction(card.id, counterType, counterAmount);
  };
  return (
    <>
      <Dialog open={open} onClose={handleClose} fullWidth={true} maxWidth="sm">
        <DialogTitle>
          {"Set counter on " + (card?.name || 'Undefined')}
        </DialogTitle>
        <DialogContent sx={{overflowY: "visible"}}>
          <Grid container spacing={2} direction="row">
            <Grid item xs={6} display="flex" justifyContent="center" alignItems="center">
              <Card
                id="card-preview"
                canDrag="false"
                imageUrl={card?.imageUrl || ''}
                name={card?.name || "Undefined"}
                backgroundColor="maroon"
              />
            </Grid>
          <Grid container item spacing={2} xs={6} direction="column" display="flex" flexDirection="column" justifyContent="flex-end" alignItems="stretch">
            <Grid item xs={5}>
              <Autocomplete
                id="counter-type"
                label="Type"
                freeSolo
                selectOnFocus
                clearOnBlur
                handleHomeEndKeys
                fullWidth={true}
                options={
                  [
                    "+1/+1",
                    "Loyalty",
                  ]
                }
                onChange={handleChangeType}
                filterOptions={(options, params) => {
                  const filtered = filter(options, params);
                  const { inputValue } = params;
                  // Suggest the creation of a new value
                  const isExisting = options.some((option) => inputValue === option.title);
                  if (inputValue !== '' && !isExisting) {
                    filtered.push(`${inputValue}`);
                  }
                  return filtered;
                }}
                renderInput={(params) => <TextField {...params} label="Counter type" />}
              />
            </Grid>
            <Grid item xs={5}>
              <TextField
                id="counter-amount"
                label="Amount"
                type="number"
                defaultValue={0}
                onChange={handleChangeAmount}
                fullWidth={true}
                InputLabelProps={{
                  shrink: true,
                }}
              />
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

export default CounterDialog;
