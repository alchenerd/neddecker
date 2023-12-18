import Grid from '@mui/material/Grid'
import './play.css'

export default function PlayPage() {
  const playData = JSON.parse(sessionStorage.getItem('playData'));
  return (
    <>
      <Grid 
        container
        direction='column'
        alignItems='center'
        justifyContent='center'
        style={{
          minWidth: '100vw'
        }}
      >
        <Grid xs={12}>
          <h1>Play</h1>
        </Grid>
      </Grid>
    </>
  );
}
