import { useState, useEffect } from 'react';
import { useImmer } from 'use-immer';
import Grid from '@mui/material/Grid';
import useWebSocket, { ReadyState } from 'react-use-websocket';
import _ from 'lodash';
import { cloneDeep } from 'lodash';
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
  const defaultBoardData = {board_state: {stack: [], players: [ {player_name: "ned"}, {player_name: "user"}]}};
  const [ boardData, setBoardData ] = useState(cloneDeep(defaultBoardData));
  const [ shadowBoardData, setShadowBoardData ] = useState(cloneDeep(defaultBoardData));
  const [ ned, setNed ] = useState({});
  const [ user, setUser ] = useState({});
  const [ selectedCard, setSelectedCard ] = useState("");
  // For communication
  const [ hasPriority, setHasPriority] = useState(false);
  const [ userIsDone, setUserIsDone] = useState(false);
  const [ userEndTurn, setUserEndTurn] = useState(false);
  const [ dndMsg, setDndMsg ] = useState({});
  const [ dblClkMsg, setDblClkMsg ] = useState({});
  const [ actionQueue, setActionQueue ] = useState([]);
  const [ whoRequestShuffle, setWhoRequestShuffle ] = useState("");

  useEffect(() => {
    console.log("Connection state changed");
    setActionQueue([]);
    setBoardData(defaultBoardData);
    setShadowBoardData(defaultBoardData);
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
    setShadowBoardData(cloneDeep(data));
    setBoardData(data);
  }

  function handleReceivePriority(data) {
    setHasPriority(true);
    setShadowBoardData(cloneDeep(data));
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
          type_line: card.typeLine,
          mana_cost: card.manaCost,
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

  const findCardById = (board, cardId) => {
    if (!cardId || !board) {
      return [null, ""];
    }
    let cardToFind = null;
    const zonesToCheck = [
      "board_state.stack",
      "board_state.players[0].battlefield",
      "board_state.players[0].hand",
      "board_state.players[0].graveyard",
      "board_state.players[1].battlefield",
      "board_state.players[1].hand",
      "board_state.players[1].graveyard",
      "board_state.players[0].library",
      "board_state.players[1].library",
      "board_state.players[0].exile",
      "board_state.players[1].exile",
    ];
    for (let i = 0; i < zonesToCheck.length; i++) {
      const path = zonesToCheck[i];
      cardToFind = _.get(board, path).find((card) => _.get(card, "id", null) === cardId);
      if (cardToFind) {
        return [cardToFind, path];
      }
    }
    return [cardToFind, ""];
  };

  const findPlayerIndexByName = (board, name) => {
    if (!board || !name) {
      return -1;
    }
    const players = _.get(board, "board_state.players");
    return players.findIndex((player) => player.player_name === name);
  }

  useEffect(() => {
    if (dndMsg && dndMsg.to) {
      const [foundCard, foundPath] = findCardById(boardData, dndMsg.id);
      if (foundPath !== dndMsg.to) {
        // changed zone, record move action
        const newAction = {
          type: "move",
          targetId: dndMsg.id,
          from: foundPath,
          to: dndMsg.to,
        };
        setActionQueue((prev) => [...prev, newAction]);
      }
    }
  }, [dndMsg]);

  useEffect(() => {
    if (dblClkMsg) {
      const [foundCard, foundPath] = findCardById(boardData, dblClkMsg.id);
      switch (dblClkMsg?.type) {
        case "toggleTap":
          {
            const newAction = {
              type: foundCard?.annotations?.isTapped ? "untap" : "tap",
              targetId: foundCard.id,
            };
            setActionQueue((prev) => [...prev, newAction]);
          }
          break;
        case "drawFromLibrary":
          const ownerIndex = findPlayerIndexByName(boardData, dblClkMsg.who);
          {
            const newAction = {
              type: "move",
              targetId: null,
              amount: 1,
              from: "board_state.players[" + ownerIndex + "].library",
              to: "board_state.players[" + ownerIndex + "].hand",
            };
            setActionQueue((prev) => [...prev, newAction]);
          }
          break;
      }
    }
  }, [dblClkMsg]);

  useEffect(() => {
    if (!actionQueue) {
      return;
    }
    let tempBoardData = cloneDeep(shadowBoardData);
    actionQueue.map((action) => {
      console.log(action);
      let [foundCard, foundPath] = findCardById(tempBoardData, action.targetId);
      let newCard = null;
      switch (action.type) {
        case "move":
          if (action.targetId) {
            console.log("moving known card");
            const annotationWhitelist = ["stickers",];
            newCard = {
              ...foundCard,
              annotations: (action.to.indexOf("battlefield") < 0) ?
              Object.keys(foundCard.annottions || {})
                .filter((key) => annotationWhitelist.includes(key))
                .reduce((obj, key) => {
                  obj[key] = foundCard.annotations[key];
                  return obj;
                }, {}) :
              foundCard.annotations,
            }
          } else { // moving unknown card
            foundPath = action.from;
            newCard = {..._.get(tempBoardData, action.from)[0]};
          }
          const toPopFrom = _.get(tempBoardData, foundPath, []);
          const toPushTo = _.get(tempBoardData, action.to, []);
          _.set(tempBoardData, foundPath, [...toPopFrom.filter((card) => card.id !== newCard.id)]);
          _.set(tempBoardData, action.to, [...toPushTo, newCard]);
          break;
        case "tap":
          {
            const newCard = {
              ...foundCard,
              annotations: foundCard?.annotations ? {...foundCard.annotations, isTapped: true} : {isTapped: true},
            };
            const targetZone = _.get(tempBoardData, foundPath, []);
            const idx = targetZone.findIndex((card) => card.id === action.targetId);
            targetZone.splice(idx, 1, newCard);
          }
          break;
        case "untap":
          {
            const newCard = {
              ...foundCard,
              annotations: foundCard?.annotations || {},
            };
            delete newCard.annotations.isTapped;
            const targetZone = _.get(tempBoardData, foundPath, []);
            const idx = targetZone.findIndex((card) => card.id === action.targetId);
            targetZone.splice(idx, 1, newCard);
          }
          break;
        case "shuffle":
          {
            console.log(action.who + ".library");
            const targetZone = _.get(tempBoardData, action.who + ".library");
            targetZone.sort(() => Math.random() - 0.5);
          }
          break;
      }
    });
    console.log(tempBoardData)
    setBoardData(tempBoardData);
  }, [actionQueue]);

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

  useEffect(() => {
    const ownerIndex = findPlayerIndexByName(boardData, whoRequestShuffle);
    if (whoRequestShuffle && whoRequestShuffle.length) {
      const newAction = {
        type: "shuffle",
        targetId: null,
        who: "board_state.players[" + ownerIndex + "]",
      };
      setActionQueue((prev) => [...prev, newAction]);
      setWhoRequestShuffle("");
    }
  }, [whoRequestShuffle])

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
            setDblClkMsg={setDblClkMsg}
            setWhoRequestShuffle={setWhoRequestShuffle}
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
              <ChatRoom
                lastMessage={lastMessage}
                actionQueue={actionQueue}
                setActionQueue={setActionQueue}
              />
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
