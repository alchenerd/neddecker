import React from 'react';
import TopFiveMetaDecks from './index';
import Container from '@mui/material/Container';
import Grid from '@mui/material/Grid';
import './App.css';

function App () {
  return (
    <Container>
      <Grid container justifyContent='center' alignItems='center'>
        <Grid item xs={12} md={12} />
        <Grid item xs={12} md={12}>
          <TopFiveMetaDecks />
        </Grid>
      </Grid>
    </Container>
  );
}

export default App
