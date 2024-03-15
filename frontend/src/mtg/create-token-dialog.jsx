import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Grid from '@mui/material/Grid';
import TextField from '@mui/material/TextField';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { cloneDeep } from 'lodash';
import { receivedNewGameAction } from './../store/slice';
import store from './../store/store';


function CreateTokenDialog({ owner, open, setOpen, actionTargetCard }) {
  const [ name, setName ] = useState("Cool Guy");
  const [ colors, setColors ] = useState([]);
  const [ type_line, setTypeLine ] = useState("Legendary Creature - Human");
  const [ oracle_text, setOracleText ] = useState("Cool Guy is very cool\nCool Guy's power and toughness is the coolness of Cool Guy (Usually infinity).");
  const [ power, setPower ] = useState("*");
  const [ toughness, setToughness ] = useState("*");

  const registerCreateTokenAction = (card, playerId) => {
    if (!card) {
      return;
    }
    const newAction = {
      type: "create_token",
      targetId: card.in_game_id,
      card: card,
      controllerPlayerId: playerId,
    };
    store.dispatch(receivedNewGameAction(newAction));
  }

  const handleClose = () => {
    setOpen(false);
  };

  const handleSubmit = () => {
    setOpen(false);
    let card = {};
    const colorString = [ ...colors ].sort((x, y) => {return "WUBRG".indexOf(x) - "WUBRG".indexOf(y);}).join("");
    if (actionTargetCard) {
      card = cloneDeep(actionTargetCard);
    } else {
      card = {
        ...card,
        name,
        colors: colorString,
        type_line,
        oracle_text,
        power,
        toughness,
        counters: {},
        annotations: [],
      };
    }
    card = {
      ...card,
      in_game_id: "token@" + (owner?.playerName[0] || "?") + "#" + uuidv4(),
    };
    registerCreateTokenAction(card);
  };

  useEffect(() => {
    if (open) {
      setName("");
      setColors([]);
      setTypeLine("");
      setOracleText("");
      setPower("");
      setToughness("");
    }
  }, [open]);

  return (
    <>
      <Dialog open={open} onClose={handleClose} fullWidth={true} maxWidth="sm">
        <DialogTitle>
          Create token
        </DialogTitle>
        <DialogContent>
          <Grid container>
            <Grid item xs={12}>
              <TextField id="token-name"
                label="name"
                value={name}
                onChange={(e) => {setName(e.target.value);}}
                fullWidth={true}
              />
            </Grid>
            <Grid item xs={12}>
              <FormGroup row>
                <FormControlLabel control={<Checkbox checked={colors.includes("W")}/>} onChange={e => {setColors(prev => e.target.checked ? [...prev, "W"] : [...prev.filter(c => c !== "W")])}} label="White" labelPlacement="top" />
                <FormControlLabel control={<Checkbox checked={colors.includes("U")}/>} onChange={e => {setColors(prev => e.target.checked ? [...prev, "U"] : [...prev.filter(c => c !== "U")])}} label="Blue" labelPlacement="top" />
                <FormControlLabel control={<Checkbox checked={colors.includes("B")}/>} onChange={e => {setColors(prev => e.target.checked ? [...prev, "B"] : [...prev.filter(c => c !== "B")])}} label="Black" labelPlacement="top" />
                <FormControlLabel control={<Checkbox checked={colors.includes("R")}/>} onChange={e => {setColors(prev => e.target.checked ? [...prev, "R"] : [...prev.filter(c => c !== "R")])}} label="Red" labelPlacement="top" />
                <FormControlLabel control={<Checkbox checked={colors.includes("G")}/>} onChange={e => {setColors(prev => e.target.checked ? [...prev, "G"] : [...prev.filter(c => c !== "G")])}} label="Green" labelPlacement="top" />
              </FormGroup>
            </Grid>
            <Grid item xs={12}>
              <TextField id="token-typeline"
                label="typeline"
                value={type_line}
                onChange={(e) => {setTypeLine(e.target.value);}}
                fullWidth={true}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField id="token-oracle-text"
                label="oracle text"
                multiline={true}
                rows={10}
                value={oracle_text}
                onChange={(e) => {setOracleText(e.target.value);}}
                fullWidth={true}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField id="token-power"
                label="power"
                value={power}
                onChange={(e) => {setPower(e.target.value);}}
                fullWidth={true}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField id="token-toughness"
                label="toughness"
                value={toughness}
                onChange={(e) => {setToughness(e.target.value);}}
                fullWidth={true}
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

export default CreateTokenDialog;
