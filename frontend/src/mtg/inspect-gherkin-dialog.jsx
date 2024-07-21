import { useEffect, useState, useRef } from 'react';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import Button from '@mui/material/Button';
import TextField from '@mui/material/TextField';

function InspectGherkinDialog({open, setOpen, actionTargetCard, cardName, gherkin, sendMessage}) {
  const [isChanged, setIsChanged] = useState(false);
  const textFieldRef = useRef('');

  var defaultCardName = actionTargetCard ? actionTargetCard.name : cardName;
  var defaultGherkin = (actionTargetCard ? actionTargetCard.rules : gherkin).join('\n\n');

  const handleChange = () => {
    if (textFieldRef.current.value !== defaultGherkin) {
      setIsChanged(true);
    } else {
      setIsChanged(false);
    }
  }

  useEffect(() => {
    if (defaultGherkin && defaultGherkin === textFieldRef?.current?.value) {
      setIsChanged(false);
    }
  }, [defaultGherkin]);

  const handleSave = () => {
    defaultGherkin = textFieldRef.current.value;
    const payload = {
      type: 'update_gherkin',
      card_name: defaultCardName,
      gherkin: defaultGherkin,
    };
    console.log(payload);
    sendMessage(JSON.stringify(payload));
  }

  const handleClose = () => {
    if (isChanged) {
      handleSave();
      console.log('handle save');
    }
    setOpen(false);
  }

  return (
    <Dialog open={open} onClose={handleClose} fullWidth={true} maxWidth="sm" onContextMenu={e => {e.stopPropagation();}}>
      <DialogTitle>
        Inspect Gherkin Rules of {defaultCardName}
      </DialogTitle>
      <DialogContent>
        <TextField
          autoFocus
          fullWidth
          defaultValue={defaultGherkin}
          variant="standard"
          multiline
          inputRef={textFieldRef}
          onChange={handleChange}
        />
      </DialogContent>
      <DialogActions>
        <Button variant="contained" color={isChanged ? "success" : "primary"} onClick={handleClose}>{isChanged ? "Save and Close" : "Close"}</Button>
      </DialogActions>
    </Dialog>
  );
}

export default InspectGherkinDialog;
