import { useState, useEffect } from 'react';
import { useImmer } from 'use-immer';
import Grid from '@mui/material/Grid';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import { Card as MtgCard } from './mtg/card';
import { Board as MtgBoard } from './mtg/board';
import { MulliganDialog } from './mtg/mulligan-dialog';
import { GameInformation } from './mtg/game-information';
import { ChatRoom } from './mtg/chat-room';

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
  // For mulligan
  const [ openMulligan, setOpenMulligan ] = useState(false);
  const [ mulliganData, setMulliganData ] = useState({});
  const [ toBottom, setToBottom ] = useState([]);
  const [ requestMulligan, setRequestMulligan ] = useState(false);
  const [ requestKeepHand, setRequestKeepHand ] = useState(false);
  // For board rendering
  const [ boardData, setBoardData ] = useState({board_state: {stack: [], players: [ {player_name: "ned"}, {player_name: "user"}]}});
  const [ ned, setNed ] = useState({});
  const [ user, setUser ] = useState({});
  const [ selectedCard, setSelectedCard ] = useState("");
  // For communication
  const [ hasPriority, setHasPriority] = useState(false);
  const [ userIsDone, setUserIsDone] = useState(false);
  const [ userEndTurn, setUserEndTurn] = useState(false);
  const [ dndMsg, setDndMsg ] = useState({});

  useEffect(() => {
    console.log("Connection state changed");
    if (readyState === ReadyState.OPEN) {
      sendMessage(registerMatchPayload);
      console.log(playData.card_image_map)
    }
  }, [readyState]);

  function handleMulliganMessage(data) {
    setMulliganData(data);
    setOpenMulligan(true);
  }

  function handleReceiveStep(data) {
    setBoardData(data);
  }

  function handleReceivePriority(data) {
    setHasPriority(true);
    setBoardData(data);
  }

  useEffect(() => {
    if (openMulligan === false && requestMulligan === true) {
      sendMessage(JSON.stringify({
        type: "mulligan",
        who: "user",
      }));
      setRequestMulligan(false);
    }
  }, [requestMulligan]);

  useEffect(() => {
    if (requestKeepHand === true && toBottom) {
      sendMessage(JSON.stringify({
        type: "keep_hand",
        who: "user",
        bottom: toBottom.map(card => ({
          id: card.id,
          name: card.name,
        })),
      }));
    }
    setRequestKeepHand(false);
    setToBottom([]);
  }, [requestKeepHand]);

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
          handleMulliganMessage(data);
          break;
        case 'receive_step':
          handleReceiveStep(data);
          break;
        case 'receive_priority':
          console.log("Received priority", data.whose_turn, data.phase);
          handleReceivePriority(data);
          break;
      }
    }
  }, [lastMessage]);

  useEffect(() => {
    if (dndMsg) {
      console.log(dndMsg);
      // delete everything to check if all components do update
      // setBoardData({board_state: {stack: [], players: [ {player_name: "ned"}, {player_name: "user"}]}});
      // TODO: searchSourceZoneById(), remove from sourceZone, parse dndMsg for targetZone, add to targetZone
    }
  }, [dndMsg]);

  const sendPassPriority = () => {
    console.log("Passing", boardData.phase)
    const payload = {
      type: "pass_priority",
      who: "user",
      actions: [],
    }
    sendMessage(JSON.stringify(payload));
  };

  useEffect(() => {
    if (hasPriority && userIsDone) {
      setHasPriority(false);
      setUserIsDone(false);
      sendPassPriority();
    }
  }, [hasPriority, userIsDone]);

  useEffect(() => {
    if (hasPriority && userEndTurn && boardData.whose_turn === "user") {
      setHasPriority(false);
      sendPassPriority();
    }
  }, [hasPriority, userEndTurn]);

  useEffect(() => {
    if (boardData.whose_turn !== "user") {
      setUserEndTurn(false);
    }
  }, [boardData.whose_turn]);

  return (
    <>
      <Grid 
        container
        direction='row'
        alignItems='center'
        justifyContent='center'
        spacing={0}
        style={{
          minWidth: '100vw',
          maxWidth: '100vw',
          minHeight: '100vh',
          maxHeight: '100vh',
        }}
      >
        <Grid item xs={8}>
          <MtgBoard
            boardData={boardData}
            ned={ned}
            setNed={setNed}
            user={user}
            setUser={setUser}
            cardImageMap={playData.card_image_map}
            setSelectedCard={setSelectedCard}
            setDndMsg={setDndMsg}
          />
        </Grid>
        <Grid item xs={4} width='100%'>
          <Grid container
            direction='column'
            alignItems='center'
            justifyContent='center'
            spacing={0}
            width='100%'
            height='100vh'
            wrap='nowrap'
          >
            <Grid item width='100%' height='40vh'>
              <GameInformation
                selectedCard={selectedCard}
                setSelectedCard={setSelectedCard}
                boardData={boardData}
                setBoardData={setBoardData}
                setUserIsDone={setUserIsDone}
                userEndTurn={userEndTurn}
                setUserEndTurn={setUserEndTurn}
                cardImageMap={playData.card_image_map}
                stack={boardData.board_state.stack}
                setDndMsg={setDndMsg}
              />
            </Grid>
            <Grid item width='100%' height='60vh'>
              <ChatRoom lastMessage={lastMessage} />
            </Grid>
          </Grid>
        </Grid>
      </Grid>
      <MulliganDialog
        open={openMulligan}
        setOpen={setOpenMulligan}
        data={mulliganData}
        cardImageMap={playData.card_image_map}
        setToBottom={setToBottom}
        setRequestMulligan={setRequestMulligan}
        setRequestKeepHand={setRequestKeepHand}
      />
    </>
  );
}
