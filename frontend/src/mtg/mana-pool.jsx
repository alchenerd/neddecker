import Grid from '@mui/material/Grid';
import Typography from '@mui/material/Typography';

const ManaCounter = ({xs, sx, manaType, value}) => {
  return (
    <Grid container item xs={xs} sx={sx}>
      <Grid item xs={12} textAlign='center'>
        <Typography>{'{' + manaType + '}'}</Typography>
      </Grid>
      <Grid item xs={12} textAlign='center'>
        <Typography>{"< " + value + " >"}</Typography>
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

const ManaPool = ({manaPool}) => {
  return (
    <Grid container item xs={12} nowrap>
      {manaPool && Object.keys(manaPool).map(manaType => (
        <ManaCounter key={manaType} xs={2} sx={{backgroundColor: colorMap[manaType]}} manaType={manaType} value={manaPool[manaType]} />
      ))}
    </Grid>
  );
}

export default ManaPool;
