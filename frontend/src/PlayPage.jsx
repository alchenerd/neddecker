import Grid from '@mui/material/Grid';
import {Card as MtgCard} from './mtg/card';

import './play.css';

export default function PlayPage() {
  const playData = JSON.parse(sessionStorage.getItem('playData'));
  const socket = new WebSocket('ws://localhost:8000/ws/play/');

  // Connection opened
  socket.addEventListener("open", event => {
    socket.send(JSON.stringify({'type': 'log', 'message': 'hello world form react'}));
  });

  // Listen for messages
  socket.addEventListener("message", event => {
    console.log("Message from server ", event.data);
  });

  const testId = 'helowrld';
  const testName = Object.keys(playData.users_main)[0];
  const testImg = playData.card_image_map[testName];

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
        <Grid item xs={12}>
          <h1>Play</h1>
            <MtgCard
              id={testId}
              name={testName}
              imageUrl={testImg}
            />
        </Grid>
      </Grid>
    </>
  );
}
