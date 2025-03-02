import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogContent from '@mui/material/DialogContent';
import DialogActions from '@mui/material/DialogActions';
import Button from '@mui/material/Button';
import Grid from '@mui/material/Grid';
import TextField from '@mui/material/TextField';
import Select from '@mui/material/Select';
import FormGroup from '@mui/material/FormGroup';
import FormControlLabel from '@mui/material/FormControlLabel';
import Checkbox from '@mui/material/Checkbox';
import MenuItem from '@mui/material/MenuItem';
import { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { cloneDeep } from 'lodash';
import { receivedNewGameAction, selectAffectedGameData } from './../store/slice';
import store from './../store/store';
import { useSelector } from "react-redux";


function CreateTokenDialog({ open, setOpen, actionTargetCard, isCopy }) {
  const [ name, setName ] = useState("Cool Guy");
  const [ colors, setColors ] = useState([]);
  const [ type_line, setTypeLine ] = useState("Legendary Creature - Human");
  const [ oracle_text, setOracleText ] = useState("Cool Guy is very cool\nCool Guy's power and toughness is the coolness of Cool Guy (Usually infinity).");
  const [ power, setPower ] = useState("*");
  const [ toughness, setToughness ] = useState("*");
  const [ destination, setDestination ] = useState("");

  const gameData = selectAffectedGameData(store.getState());
  const players = gameData?.board_state?.players;

  const registerCreateTokenAction = (card, destination) => {
    if (!card) {
      return;
    }
    const newAction = {
      type: isCopy ? "create_copy" : "create_token",
      targetId: card.in_game_id,
      card,
      destination,
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
      card["annotations"] = {
        ...card?.annotations,
        isTokenCopyOf: card?.name
      };
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
      in_game_id: (isCopy ? "copy#" : "token#") + uuidv4(),
    };
    registerCreateTokenAction(card, destination);
  };

  useEffect(() => {
    if (open) {
      setName(actionTargetCard?.name || "");
      setColors(actionTargetCard?.colors || []);
      setTypeLine(actionTargetCard?.type_line || "");
      setOracleText(actionTargetCard?.oracle_text || "");
      setPower(actionTargetCard?.power || "");
      setToughness(actionTargetCard?.toughness || "");
      setDestination("board_state.stack");
    }
  }, [open, actionTargetCard]);

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
            <Grid item xs={12} sx={{display: "flex", justifyContent: "space-around"}}>
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
            <Grid item xs={12}>
              <Select
                value={destination}
                fullWidth={true}
                onChange={(e) => {setDestination(e.target.value)}}
              >
                {players?.map((player, index) => (
                  <MenuItem key={player.player_name} value={"board_state.players[" + index + "].battlefield"}>
                    {"Player[" + index + "]: " + player.player_name + "'s battlefield"}
                  </MenuItem>
                ))}
                <MenuItem value="board_state.stack">stack</MenuItem>
              </Select>
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
