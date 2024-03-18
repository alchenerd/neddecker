import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';
import { receivedNewGameAction } from './../store/slice';
import store from './../store/store';

const setMana = (playerId, manaType, amount, manaPool) => {
  const newAction = {
    type: "set_mana",
    targetId: playerId,
    manaPool: { ...manaPool, [manaType]: manaPool[manaType] + amount },
  };
  console.log(newAction);
  store.dispatch(receivedNewGameAction(newAction));
}

const ManaCounter = ({xs, sx, ownerId, manaType, value, manaPool}) => {
  return (
    <Grid container item xs={xs} sx={sx}>
      <Grid item xs={12} textAlign='center'>
        <Typography>{'{' + manaType + '}'}</Typography>
      </Grid>
      <Grid item xs={12} textAlign='center'>
        <Typography display="inline" onClick={() => {setMana(ownerId, manaType, -1, manaPool)}}>{"< "}</Typography>
        <Typography display="inline">{value}</Typography>
        <Typography display="inline" onClick={() => {setMana(ownerId, manaType, +1, manaPool)}}>{" >"}</Typography>
      </Grid>
    </Grid>
  )
}

const colorMap = {
  W: "goldenrod",
  U: "blue",
  B: "purple",
  R: "red",
  G: "green",
  C: "grey",
}

const ManaPool = ({manaPool, ownerId}) => {
  return (
    <Grid container item xs={12}>
      {manaPool && Object.keys(manaPool).map(manaType => (
        <ManaCounter key={manaType}
          xs={2}
          sx={{backgroundColor: colorMap[manaType]}}
          {...{ownerId, manaPool}}
          manaType={manaType}
          value={manaPool[manaType]}
        />
      ))}
    </Grid>
  );
}

export default ManaPool;
