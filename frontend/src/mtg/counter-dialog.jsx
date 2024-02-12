import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Grid from '@mui/material/Grid';
import TextField from '@mui/material/TextField';
import Autocomplete from '@mui/material/Autocomplete';
import { Card } from './card';
import { useState } from 'react';

function CounterDialog({open, setOpen, card, setCardCounter}) {
  const handleClose = () => {setOpen(false)}
  const [counterType, setCounterType] = useState("+1/+1")
  const [counterAmount, setCounterAmount] = useState(1)
  return (
    <>
      <Dialog open={open} onClose={handleClose} fullWidth={true} maxWidth="sm">
        <DialogTitle>
          {card?.id || 'Undefined'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} direction="row">
            <Grid item xs={6} display="flex" justifyContent="center" alignItems="center">
              <Card
                canDrag="false"
                imageUrl={card?.imageUrl || ''}
                name="where is this card?"
                backgroundColor="maroon"
              />
            </Grid>
          <Grid container item spacing={2} xs={6} direction="column" display="flex" flexDirection="column" justifyContent="flex-end" alignItems="stretch">
            <Grid item xs={5}>
              <Autocomplete
                id="counter-type"
                label="Type"
                value={counterType}
                freeSolo
                fullWidth={true}
                options={["+1/+1", "Loyalty"]}
                renderInput={(params) => <TextField {...params} label="Counter type"/>}
              />
            </Grid>
            <Grid item xs={5}>
              <TextField
                id="counter-amount"
                label="Amount"
                type="number"
                value={counterAmount}
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
          <Button onClick={handleClose}>
            Submit
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}

export default CounterDialog;
