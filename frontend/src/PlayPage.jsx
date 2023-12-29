import { useState, useEffect } from 'react';
import Grid from '@mui/material/Grid';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { Card as MtgCard } from './mtg/card';
import { Board as MtgBoard } from './mtg/board';
import { MulliganDialog } from './mtg/mulligan-dialog';

import './play.css';

const registerMatchPayload = JSON.stringify({
  type: 'register_match',
  format: 'modern',
  games: 3,
})

const registerPlayerPayload = (who, main, side) => {
  const payload_ned = {
    type: 'register_player',
    player_name: 'ned',
    player_type: 'ai',
    main: main,
    side: side,
  };
  const payload_user = {
    type: 'register_player',
    player_name: 'user',
    player_type: 'human',
    main: main,
    side: side,
  };
  if (who === 'ned') {
    return JSON.stringify(payload_ned);
  } else if (who === 'user') {
    return JSON.stringify(payload_user);
  }
}

function mulliganToTwo(send, data) {
  if ((7 - data.to_bottom) > 2) {
    send(JSON.stringify({type: "mulligan", who: "user"}));
  } else {
    const to_bottom = data.hand.slice(-5);
    const payload = {
      type: 'keep_hand',
      who: 'user',
      bottom: to_bottom,
    };
    send(JSON.stringify(payload));
  }
}

export default function PlayPage() {
  const playData = JSON.parse(sessionStorage.getItem('playData'));
  const wsUrl = 'ws://localhost:8000/ws/play/';
  const { sendMessage, lastMessage, readyState } = useWebSocket(wsUrl);
  const [ openMulligan, setOpenMulligan ] = useState(false);
  const [ nedsHand, setNedsHand ] = useState([]);
  const [ usersHand, setUsersHand ] = useState([]);
  const [ toBottom, setToBottom ] = useState(0);

  useEffect(() => {
    console.log("Connection state changed");
    if (readyState === ReadyState.OPEN) {
      sendMessage(registerMatchPayload);
    }
  }, [readyState]);

  function handleMulliganMessage(data) {
    console.log(data);
    const processed = data.hand.map(card => {
      const imageUrl = playData.card_image_map[card.name] || playData.card_image_map[card.name.split(" // ")[0]];
      const backImageUrl= playData.card_image_map[card.name.split(" // ")[1]] || "";
      return {
        id: card.id,
        name: card.name,
        imageUrl: imageUrl,
        backImageUrl: backImageUrl,
      };
    });
    setUsersHand([...processed]);
    setToBottom(data.to_bottom);
    setOpenMulligan(true);
  }

  useEffect(() => {
    console.debug(lastMessage);
    if (lastMessage) {
      const data = JSON.parse(lastMessage.data);
      switch(data.type) {
        case 'log':
          console.log("Message from server:", data.message);
          break;
        case 'match_initialized':
          sendMessage(registerPlayerPayload('ned', playData.neds_main, playData.neds_side));
          sendMessage(registerPlayerPayload('user', playData.users_main, playData.users_side));
          break;
        case 'player_registered':
          console.log(data.message);
          break;
        case 'game_start':
          console.log("Game", data.game, "of", data.of, "has started.", data.who_goes_first, "goes first.");
          break;
        case 'mulligan':
          //mulliganToTwo(sendMessage, data);
          handleMulliganMessage(data);
          break;
      }
    }
  }, [lastMessage]);

  return (
    <>
      <Grid 
        container
        direction='column'
        alignItems='center'
        justifyContent='center'
        spacing={0}
        style={{
          minWidth: '100vw'
        }}
      >
        <Grid item minWidth='100%' xs={12}>
          <MtgBoard />
        </Grid>
      </Grid>
      <MulliganDialog
        open={openMulligan}
        setOpen={setOpenMulligan}
        hand={usersHand}
        setHand={setUsersHand}
        toBottom={toBottom}
      />
    </>
  );
}
