import { useState, useEffect } from 'react';
import Grid from '@mui/material/Grid';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import _ from 'lodash';
import { cloneDeep } from 'lodash';
import{ Card as MtgCard } from './mtg/card';
import { Board as MtgBoard } from './mtg/board';
import { MulliganDialog } from './mtg/mulligan-dialog';
import { GameInformation } from './mtg/game-information';
import { ChatRoom } from './mtg/chat-room';
import MoveDialog from './mtg/move-dialog';
import CounterDialog from './mtg/counter-dialog';
import AnnotationDialog from './mtg/annotation-dialog';
import { useNavigate } from 'react-router-dom';
import store from './store/store'
import { useAffectedGameDataSelector, receivedNewGameData, receivedNewGameAction, initialize } from './store/slice';
import { findCardById } from './mtg/find-card';
import { useSelector } from 'react-redux';
import CreateTriggerDialog from './mtg/create-trigger-dialog';
import CreateDelayedTriggerDialog from './mtg/create-delayed-trigger-dialog';
import DelayedTriggerMemoDrawer from './mtg/delayed-trigger-memo-drawer';

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
  const navigate = useNavigate();
  let playData = JSON.parse(sessionStorage.getItem('playData'));
  useEffect(() => {
    playData = JSON.parse(sessionStorage.getItem('playData'));
    if (!playData) {
      navigate("/");
    }
    store.dispatch(initialize());
  }, []);
  const wsUrl = 'ws://localhost:8000/ws/play/';
  const { sendMessage, lastMessage, readyState } = useWebSocket(wsUrl);
  // For mulligan
  const [ openMulliganDialog, setOpenMulliganDialog ] = useState(false);
  const [ mulliganData, setMulliganData ] = useState({});
  const [ toBottom, setToBottom ] = useState([]);
  const [ requestMulligan, setRequestMulligan ] = useState(false);
  const [ requestKeepHand, setRequestKeepHand ] = useState(false);
  // For board rendering
  // const defaultgameData = {board_state: {stack: [], players: [ {player_name: "ned"}, {player_name: "user"}]}};
  // const [ gameData, setBoardData ] = useState(cloneDeep(defaultBoardData));
  // const [ shadowgameData, setShadowBoardData ] = useState(cloneDeep(defaultBoardData));
  // const [ ned, setNed ] = useState({});
  // const [ user, setUser ] = useState({});
  const [ focusedCard, setFocusedCard ] = useState(null);
  // For communication
  const [ hasPriority, setHasPriority] = useState(false);
  const [ hasPseudopriority, setHasPseudopriority] = useState(false);
  const [ userIsDone, setUserIsDone] = useState(false);
  const [ userEndTurn, setUserEndTurn] = useState(false);
  const [ dndMsg, setDndMsg ] = useState({});
  const [ dblClkMsg, setDblClkMsg ] = useState({});
  //const [ actionQueue, setActionQueue ] = useState([]);
  const [ whoRequestShuffle, setWhoRequestShuffle ] = useState("");
  const [ actionTargetCard, setActionTargetCard ] = useState(null);
  const [ openMoveDialog, setOpenMoveDialog] = useState(false);
  const [ openCounterDialog, setOpenCounterDialog] = useState(false);
  const [ openAnnotationDialog, setOpenAnnotationDialog] = useState(false);
  const gameData = useSelector((state) => state.gameState.gameData);
  const affectedGameData = useAffectedGameDataSelector();
  const [ openCreateTriggerDialog, setOpenCreateTriggerDialog ] = useState(false);
  const [ openCreateDelayedTriggerDialog, setOpenCreateDelayedTriggerDialog ] = useState(false);
  const [ openDelayedTriggerMemoDrawer, setOpenDelayedTriggerMemoDrawer ] = useState(false);

  useEffect(() => {
    console.log("Connection state changed");
    if (readyState === ReadyState.OPEN) {
      sendMessage(registerMatchPayload);
    }
  }, [readyState]);

  function handleMulliganMessage(data) {
    setMulliganData(data);
    setOpenMulliganDialog(true);
  }

  function handleReceiveStep(data) {
    store.dispatch(receivedNewGameData({ newGameData: data }));
  }

  function handleReceivePriority(data) {
    setHasPriority(true);
    store.dispatch(receivedNewGameData({ newGameData: data }));
  }

  function handleRequirePlayerAction(data) {
    setHasPseudopriority(true);
    store.dispatch(receivedNewGameData({ newGameData: data }));
  }

  useEffect(() => {
    if (openMulliganDialog === false && requestMulligan === true) {
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
        bottom: toBottom,
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
        case 'require_player_action':
          console.log("Requires Player's action but no priority", data.whose_turn, data.phase);
          handleRequirePlayerAction(data);
          break;
      }
    }
  }, [lastMessage]);

  const registerMoveAction = (id, to) => {
    console.log("registermoveaction is called");
    console.log("moving", id, "to", to);
    const found = findCardById(affectedGameData, id);
    const foundCard = found.card;
    const foundPath = found.path;
    if (foundPath !== to) {
      const newAction = {
        type: "move",
        targetId: id,
        from: foundPath,
        to: to,
      };
      store.dispatch(receivedNewGameAction(newAction));
    }
  }

  const registerCounterAction = (id, type, amount) => {
    if (type === null || amount === null) {
      return;
    }
    const newAction = {
      type: "set_counter",
      targetId: id,
      counterType: type,
      counterAmount: amount,
    };
    store.dispatch(receivedNewGameAction(newAction));
  }

  const registerSetAnnotationAction = (id, key, value) => {
    if (key === null || value === null) {
      return;
    }
    const newAction = {
      type: "set_annotation",
      targetId: id,
      annotationKey: key,
      annotationValue: value,
    };
    store.dispatch(receivedNewGameAction(newAction));
  }

  useEffect(() => {
    console.log("DNDMSG", dndMsg);
    if (dndMsg && dndMsg.to && dndMsg.id) {
      registerMoveAction(dndMsg.id, dndMsg.to);
    }
  }, [dndMsg]);

  useEffect(() => {
    if (dblClkMsg) {
      const found = findCardById(affectedGameData, dblClkMsg.id);
      const foundCard = found.card;
      const foundPath = found.path;
      switch (dblClkMsg?.type) {
        case "toggleTap":
          {
            const newAction = {
              type: foundCard?.annotations?.isTapped ? "untap" : "tap",
              targetId: foundCard.in_game_id,
            };
            // setActionQueue((prev) => [...prev, newAction]);
          }
          break;
        case "drawFromLibrary":
          const players = _.get(affectedGameData, "board_state.players");
          const ownerIndex = players.findIndex((player) => player.player_name === dblClkMsg.who);
          const cardId = _.get(affectedGameData, "board_state.players[" + ownerIndex + "].library[0]").in_game_id;
          registerMoveAction(cardId, "board_state.players[" + ownerIndex + "].hand");
          break;
      }
    }
  }, [dblClkMsg]);

  const sendPassPriority = () => {
    console.log("Passing", gameData.phase)
    const payload = {
      type: "pass_priority",
      who: "user",
      actions: [],
    }
    sendMessage(JSON.stringify(payload));
  };

  const sendPassNonPriority = () => {
    console.log("Ending", gameData.phase)
    const payload = {
      type: "pass_non_priority_action",
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
    } else if (hasPseudopriority && userIsDone) {
      setHasPseudopriority(false);
      setUserIsDone(false);
      sendPassNonPriority();
    }
  }, [hasPriority, hasPseudopriority, userIsDone]);

  useEffect(() => {
    if (hasPriority && userEndTurn && gameData.whose_turn === "user") {
      setHasPriority(false);
      sendPassPriority();
    } else if (hasPseudopriority && userEndTurn && gameData.whose_turn === "user") {
      setHasPseudopriority(false);
      sendPassNonPriority();
    }
  }, [hasPriority, hasPseudopriority, userEndTurn]);

  useEffect(() => {
    if (gameData.whose_turn !== "user") {
      setUserEndTurn(false);
    }
  }, [gameData.whose_turn]);

  useEffect(() => { 
    if (whoRequestShuffle && whoRequestShuffle.length) {
      const ownerIndex = affectedGameData.board_state.players.findIndex((player) => player.player_name === whoRequestShuffle);
      const newAction = {
        type: "shuffle",
        targetId: null,
        who: "board_state.players[" + ownerIndex + "]",
      };
      store.dispatch(receivedNewGameAction(newAction));
      setWhoRequestShuffle("");
    }
  }, [whoRequestShuffle])

  if (playData) {
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
              setFocusedCard={setFocusedCard}
              setDndMsg={setDndMsg}
              setDblClkMsg={setDblClkMsg}
              setWhoRequestShuffle={setWhoRequestShuffle}
              setActionTargetCard={setActionTargetCard}
              setOpenMoveDialog={setOpenMoveDialog}
              setOpenCounterDialog={setOpenCounterDialog}
              setOpenAnnotationDialog={setOpenAnnotationDialog}
              setOpenCreateTriggerDialog={setOpenCreateTriggerDialog}
              setOpenCreateDelayedTriggerDialog={setOpenCreateDelayedTriggerDialog}
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
                  focusedCard={focusedCard}
                  setFocusedCard={setFocusedCard}
                  setUserIsDone={setUserIsDone}
                  userEndTurn={userEndTurn}
                  setUserEndTurn={setUserEndTurn}
                  setDndMsg={setDndMsg}
                  setActionTargetCard={setActionTargetCard}
                  setOpenMoveDialog={setOpenMoveDialog}
                  setOpenCounterDialog={setOpenCounterDialog}
                  setOpenAnnotationDialog={setOpenAnnotationDialog}
                  setOpenCreateTriggerDialog={setOpenCreateTriggerDialog}
                  setOpenCreateDelayedTriggerDialog={setOpenCreateDelayedTriggerDialog}
                />
              </Grid>
              <Grid item width='100%' height='60vh'>
                <ChatRoom
                  lastMessage={lastMessage}
                />
              </Grid>
            </Grid>
          </Grid>
        </Grid>
        <MulliganDialog
          open={openMulliganDialog}
          setOpen={setOpenMulliganDialog}
          data={mulliganData}
          setToBottom={setToBottom}
          setRequestMulligan={setRequestMulligan}
          setRequestKeepHand={setRequestKeepHand}
        />
        <MoveDialog
          open={openMoveDialog}
          setOpen={setOpenMoveDialog}
          card={actionTargetCard}
          userIndex={affectedGameData?.board_state?.players.findIndex(player => player.player_name === "user")}
          registerMoveAction={registerMoveAction}
        />
        <CounterDialog
          open={openCounterDialog}
          setOpen={setOpenCounterDialog}
          card={actionTargetCard}
          registerCounterAction={registerCounterAction}
        />
        <AnnotationDialog
          open={openAnnotationDialog}
          setOpen={setOpenAnnotationDialog}
          card={actionTargetCard}
          registerSetAnnotationAction={registerSetAnnotationAction}
        />
        <CreateTriggerDialog
          open={openCreateTriggerDialog}
          setOpen={setOpenCreateTriggerDialog}
          card={actionTargetCard}
        />
        <CreateDelayedTriggerDialog
          open={openCreateDelayedTriggerDialog}
          setOpen={setOpenCreateDelayedTriggerDialog}
          card={actionTargetCard}
        />
        <DelayedTriggerMemoDrawer
          open={openDelayedTriggerMemoDrawer}
          setOpen={setOpenDelayedTriggerMemoDrawer}
        />
      </>
    )
  } else {
    return null;
  }
}
