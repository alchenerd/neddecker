import { useState, useEffect } from 'react';
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

const PlayerAnnotationDialog = ({open, setOpen, owner, ownerId}) => {
  const [annotationKey, setAnnotationKey] = useState("");
  const [annotationValue, setAnnotationValue] = useState("");
  const [annotationsToDisplay, setAnnotationsToDisplay] = useState(owner?.annotations || {});
  useEffect(() => {
    if (owner?.annotations) {
      setAnnotationsToDisplay({...owner.annotations});
    }
  }, [owner?.annotations]);
  useEffect(() => {
    if (open) {
      setAnnotationKey("");
      setAnnotationValue("");
    }
  }, [open]);
  const handleClose = () => {
    setOpen(false);
    setAnnotationKey("");
    setAnnotationValue("");
  };
  const handleChangeKey = (event, newValue) => {
    console.log(newValue);
    if (newValue && newValue.inputValue) {
      setAnnotationKey(newValue.inputValue);
    } else {
      setAnnotationKey(newValue);
    }
  };
  const handleChangeValue = (event, newValue) => {
    console.log(newValue);
    if (newValue && newValue.inputValue) {
      setAnnotationValue(newValue.inputValue);
    } else {
      setAnnotationValue(newValue);
    }
  };
  useEffect(() => {
    if (annotationKey && owner?.annotations && Object.keys(owner.annotations || {}).length) {
      setAnnotationValue("");
      console.log(owner.annotations)
      Object.keys(owner.annotations).forEach((key) => {
        if (key === annotationKey) {
          console.log("setting", owner.annotations[key])
          setAnnotationValue(owner.annotations[key]);
        }
      });
    } else {
      setAnnotationValue("");
    }
  }, [annotationKey])
  const registerSetPlayerAnnotationAction = (ownerId, key, value) => {
    if (!key) {
      return;
    }
    const newAction = {
      type: "set_player_annotation",
      targetId: ownerId,
      annotationKey: key,
      annotationValue: value,
    };
    store.dispatch(receivedNewGameAction(newAction));
  }
  const handleSubmit = () => {
    setOpen(false);
    registerSetPlayerAnnotationAction(ownerId, annotationKey, annotationValue);
  };
  return (
    <Dialog open={open} onClose={handleClose}>
      <DialogTitle>
        Set annotation on player {owner?.player_name || "Undefined"}
      </DialogTitle>
      <DialogContent>
        <Autocomplete
          id="player-annotation-key"
          label="Key"
          freeSolo
          autoSelect
          clearOnBlur
          handleHomeEndKeys
          options={
            Object.keys(annotationsToDisplay)
          }
          onChange={handleChangeKey}
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
          renderInput={(params) => <TextField {...params} label="Annotation key" />}
        />
        <Autocomplete
          id="annotation-value"
          label="Value"
          freeSolo
          autoSelect
          clearOnBlur
          handleHomeEndKeys
          fullWidth={true}
          options={
            [... new Set(Object.values(annotationsToDisplay))]
          }
          onChange={handleChangeValue}
          value={annotationValue || ""}
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
          renderInput={(params) => <TextField {...params} label="Annotation value" />}
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

export default PlayerAnnotationDialog;
