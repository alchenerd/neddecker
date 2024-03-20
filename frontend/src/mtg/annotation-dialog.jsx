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

function AnnotationDialog({open, setOpen, card, registerSetAnnotationAction}) {

  const [annotationKey, setAnnotationKey] = useState("");
  const [annotationValue, setAnnotationValue] = useState("");
  
  // list of the card's annotation to show
  const [annotationsToDisplay, setAnnotationsToDisplay] = useState(card?.annotations || {});

  // whenever the card's annotation changes, update the display annotations
  useEffect(() => {
    if (card && card.annotations) {
      setAnnotationsToDisplay({...card.annotations});
    }
  }, [card?.annotations]);

  // whenever the dialog opens, clear the field
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

  const handleSubmit = () => {
    setOpen(false);
    registerSetAnnotationAction(card.in_game_id, annotationKey, annotationValue);
  };

  // whenever key has changed and we can find value on the card, overwrite the field
  useEffect(() => {
    if (annotationKey && card && card.annotations && Object.keys(card.annotations || {}).length) {
      setAnnotationValue("");
      console.log(card.annotations)
      Object.keys(card.annotations).forEach((key) => {
        if (key === annotationKey) {
          console.log("setting", card.annotations[key])
          setAnnotationValue(card.annotations[key]);
        }
      });
    } else {
      setAnnotationValue("");
    }
  }, [annotationKey])

  return (
    <>
      <Dialog open={open} onClose={handleClose} fullWidth={true} maxWidth="sm">
        <DialogTitle>
          {"Set annotation of " + (card?.name || 'Undefined')}
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
            <Grid container item spacing={2} xs={6} direction="column" display="flex" flexDirection="column" justifyContent="flex-end" alignItems="stretch">
              <Grid item xs={5}>
                <Autocomplete
                  id="annotation-key"
                  label="Key"
                  freeSolo
                  autoSelect
                  clearOnBlur
                  handleHomeEndKeys
                  fullWidth={true}
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
              </Grid>
              <Grid item xs={5}>
                <Autocomplete
                  id="annotation-value"
                  label="Value"
                  freeSolo
                  autoSelect
                  clearOnBlur
                  handleHomeEndKeys
                  fullWidth={true}
                  options={
                    [...(new Set(Object.values(annotationsToDisplay).map(item => item.toString?.())))]
                  }
                  getOptionLabel={(option) => (option.toString?.())}
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

export default AnnotationDialog;
