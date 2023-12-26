import Grid from '@mui/material/Grid';
import {Card as MtgCard} from './mtg/card';

import './play.css';

function sendRegisterMatch(socket) {
  const payload = {
    type: 'register_match',
    format: 'modern',
    games: 3,
  };
  socket.send(JSON.stringify(payload));
}

function sendRegisterPlayer(socket, playData) {
  const payload_ned = {
    type: 'register_player',
    player_name: 'ned',
    player_type: 'ai',
    main: playData.neds_main,
    side: playData.neds_side,
  };
  const payload_user = {
    type: 'register_player',
    player_name: 'user',
    player_type: 'human',
    main: playData.users_main,
    side: playData.users_side,
  };
  socket.send(JSON.stringify(payload_ned));
  socket.send(JSON.stringify(payload_user));
}

function sendRequestMulligan(socket) {
  socket.send('{"type": "mulligan", "who": "user"}');
}

function mulliganToTwo(socket, data) {
  if ((7 - data.to_bottom) > 2) {
    sendRequestMulligan(socket);
  } else {
    const to_bottom = data.hand.slice(-5);
    const payload = {
      type: 'keep_hand',
      who: 'user',
      bottom: to_bottom,
    };
    socket.send(JSON.stringify(payload));
  }
}

export default function PlayPage() {
  const playData = JSON.parse(sessionStorage.getItem('playData'));
  const socket = new WebSocket('ws://localhost:8000/ws/play/');

  // Connection opened
  socket.addEventListener("open", event => {
    sendRegisterMatch(socket);
  });

  // Listen for messages
  socket.addEventListener("message", event => {
    console.debug("Data from server:", event.data);
    let data = JSON.parse(event.data);
    switch(data.type) {
      case 'log':
        console.log("Message from server:", data.message);
        break;
      case 'match_initialized':
        sendRegisterPlayer(socket, playData)
        break;
      case 'player_registered':
        console.log(data.message);
        break;
      case 'game_start':
        console.log("Game", data.game, "of", data.of, "has started.", data.who_goes_first, "goes first.");
        break;
      case 'mulligan':
        mulliganToTwo(socket, data);
    }
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
