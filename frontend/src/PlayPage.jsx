import { useState, useEffect } from 'react';
import Grid from '@mui/material/Grid';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import Button from '@mui/material/Button';
import Select from '@mui/material/Select';
import MenuItem from '@mui/material/MenuItem';
import TextField from '@mui/material/TextField';
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
import store from './store/store';
import { selectAffectedGameData, receivedNewGameData, receivedNewGameAction, initialize, clearGameAction } from './store/slice';
import { findCardById } from './mtg/find-card';
import { useSelector } from 'react-redux';
import CreateTriggerDialog from './mtg/create-trigger-dialog';
import CreateDelayedTriggerDialog from './mtg/create-delayed-trigger-dialog';
import DelayedTriggerMemoDrawer from './mtg/delayed-trigger-memo-drawer';
import CreateTokenDialog from './mtg/create-token-dialog';
import InspectGherkinDialog from './mtg/inspect-gherkin-dialog';

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
  const { sendMessage, lastMessage, readyState } = useWebSocket(wsUrl, {share: true});
  const [ questionData, setQuestionData ] = useState(null);
  const [ openQuestionDialog, setOpenQuestionDialog ] = useState(false);
  const [ answer, setAnswer ] = useState('');
  const [ openAskRevealCompanionDialog, setOpenAskRevealCompanionDialog ] = useState(false);
  const [ sideboardData, setSideboardData ] = useState([]);
  const [ companion, setCompanion ] = useState('');
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
  const [ userIsDone, setUserIsDone] = useState(true);
  const [ userEndTurn, setUserEndTurn] = useState(true);
  const [ dndMsg, setDndMsg ] = useState({});
  const [ dblClkMsg, setDblClkMsg ] = useState({});
  //const [ actionQueue, setActionQueue ] = useState([]);
  const [ whoRequestShuffle, setWhoRequestShuffle ] = useState("");
  const [ actionTargetCard, setActionTargetCard ] = useState(null);
  const [ openMoveDialog, setOpenMoveDialog] = useState(false);
  const [ openCounterDialog, setOpenCounterDialog] = useState(false);
  const [ openAnnotationDialog, setOpenAnnotationDialog] = useState(false);
  const gameData = useSelector((state) => state.gameState.gameData);
  const affectedGameData = useSelector(selectAffectedGameData);
  const actions = useSelector((state => state.gameState.actions));
  const grouping = useSelector((state => state.gameState.grouping));
  const [ openCreateTriggerDialog, setOpenCreateTriggerDialog ] = useState(false);
  const [ openCreateDelayedTriggerDialog, setOpenCreateDelayedTriggerDialog ] = useState(false);
  const [ openDelayedTriggerMemoDrawer, setOpenDelayedTriggerMemoDrawer ] = useState(false);
  const [ openCreateTokenDialog, setOpenCreateTokenDialog ] = useState(false);
  const [ openInspectGherkinDialog, setOpenInspectGherkinDialog ] = useState(false);
  const [ isResolving, setIsResolving ] = useState(false);
  const [ targetIsCopy, setTargetIsCopy ] = useState(false);
  const [ inspectCardName, setInspectCardName ] = useState('');
  const [ inspectGherkin, setInspectGherkin ] = useState([]);

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
    store.dispatch(clearGameAction());
    store.dispatch(receivedNewGameData({ newGameData: data }));
  }

  function handleReceivePriority(data) {
    store.dispatch(clearGameAction());
    setHasPriority(true);
    setUserIsDone(false);
    store.dispatch(receivedNewGameData({ newGameData: data }));
  }

  function handleRequirePlayerAction(data) {
    store.dispatch(clearGameAction());
    setHasPseudopriority(true);
    setUserIsDone(false);
    store.dispatch(receivedNewGameData({ newGameData: data }));
  }

  function handleResolveStack(data) {
    store.dispatch(clearGameAction());
    setHasPriority(true);
    setIsResolving(true);
    setUserIsDone(false);
    store.dispatch(receivedNewGameData({ newGameData: data }));
  }

  function handleUpdateGherkin(data) {
    setActionTargetCard(null);
    console.log(data.card_name, data.gherkin)
    setInspectCardName(data.card_name);
    setInspectGherkin(data.gherkin);
    setOpenInspectGherkinDialog(true);
  }

  function handleAnswer() {
    if (!answer) {
      return;
    }
    setOpenQuestionDialog(false)
    const payload = {
      ...questionData,
      type: "answer",
      answer: answer,
    }
    sendMessage(JSON.stringify(payload));
    setAnswer('');
  }

  function handleAnswerChange(event) {
    setAnswer(event.target.value);
  }

  function handleChangeCompanion(e) {
    setCompanion(e.target.value);
  }

  function handleRevealCompanion() {
    setOpenAskRevealCompanionDialog(false)
    const payload = {
      type: "ask_reveal_companion",
      who: "user",
      targetId: companion,
    }
    sendMessage(JSON.stringify(payload));
  }

  function handleNoRevealCompanion() {
    setOpenAskRevealCompanionDialog(false)
    const payload = {
      type: "ask_reveal_companion",
      who: "user",
      targetId: null,
    }
    sendMessage(JSON.stringify(payload));
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
        case 'update':
          store.dispatch(receivedNewGameData({ newGameData: data }));
          break;
        case 'match_initialized':
          sendMessage(registerPlayerPayload('ned', playData.neds_main, playData.neds_side));
          sendMessage(registerPlayerPayload('user', playData.users_main, playData.users_side));
          break;
        case 'player_registered':
          console.log(data.message);
          break;
        case 'game_start':
          console.log("Game", data.game, "of", data.of, "has started.");
          break;
        case 'question':
          setQuestionData(data);
          setOpenQuestionDialog(true);
        case 'ask_reveal_companion':
          setSideboardData(data.sideboard);
          setOpenAskRevealCompanionDialog(true);
          break
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
        case 'resolve_stack':
          console.log("resolving", data.board_state.stack.at(-1).name);
          handleResolveStack(data);
        case 'update_gherkin':
          console.log("A card's gherkin rule is updated");
          handleUpdateGherkin(data);
      }
    }
  }, [lastMessage]);

  useEffect(() => {
    console.log("sideboard data changed")
    console.log(sideboardData)
    if (sideboardData && sideboardData.length) {
      const companions = sideboardData.filter(card => card.oracle_text?.startsWith('Companion'))
      console.log(companions)
      setCompanion(companions[0]['in_game_id']);
    }
  }, [sideboardData]);

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
    if (type === null) {
      return;
    }
    const newAction = {
      type: "set_counter",
      targetId: id,
      counterType: type,
      counterAmount: amount || 0,
    };
    store.dispatch(receivedNewGameAction(newAction));
  }

  const registerSetAnnotationAction = (id, key, value) => {
    if (key === null) {
      return;
    }
    const newAction = {
      type: "set_annotation",
      targetId: id,
      annotationKey: key,
      annotationValue: value || "",
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
              type: "set_annotation",
              targetId: foundCard.in_game_id,
              annotationKey: "isTapped",
              annotationValue: foundCard?.annotations?.isTapped ? false : true,
            };
            store.dispatch(receivedNewGameAction(newAction));
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

  const sendResolveStack = () => {
    console.log("Resolving", actions)
    const payload = {
      type: "resolve_stack",
      who: "user",
      gameData: affectedGameData,
      actions: actions,
    }
    sendMessage(JSON.stringify(payload));
    setIsResolving(false);
  }

  const sendPassPriority = () => {
    console.log("Passing", actions)
    const payload = {
      type: "pass_priority",
      who: "user",
      gameData: affectedGameData,
      actions: actions,
      grouping: grouping,
    }
    sendMessage(JSON.stringify(payload));
  };

  const sendPassNonPriority = () => {
    console.log("Ending", gameData.phase)
    const payload = {
      type: "pass_non_priority_action",
      who: "user",
      gameData: affectedGameData,
      actions: actions,
    }
    console.log("???" + JSON.stringify(payload));
    sendMessage(JSON.stringify(payload));
  };

  useEffect(() => {
    if (hasPriority && isResolving && userIsDone) {
      setHasPriority(false);
      setIsResolving(false);
      sendResolveStack();
    }
    else if (hasPriority && userIsDone) {
      setHasPriority(false);
      sendPassPriority();
    } else if (hasPseudopriority && userIsDone) {
      setHasPseudopriority(false);
      sendPassNonPriority();
    }
  }, [hasPriority, hasPseudopriority, userIsDone, isResolving]);

  useEffect(() => {
    if (hasPriority && userEndTurn && gameData.whose_turn === "user") {
      setHasPriority(false);
      setUserIsDone(true);
      sendPassPriority();
    } else if (hasPseudopriority && userEndTurn && gameData.whose_turn === "user") {
      setHasPseudopriority(false);
      setUserIsDone(true);
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
              actionTargetCard={actionTargetCard}
              setActionTargetCard={setActionTargetCard}
              setOpenMoveDialog={setOpenMoveDialog}
              setOpenCounterDialog={setOpenCounterDialog}
              setOpenAnnotationDialog={setOpenAnnotationDialog}
              setOpenCreateTriggerDialog={setOpenCreateTriggerDialog}
              setOpenCreateDelayedTriggerDialog={setOpenCreateDelayedTriggerDialog}
              setOpenCreateTokenDialog={setOpenCreateTokenDialog}
              setOpenInspectGherkinDialog={setOpenInspectGherkinDialog}
              setTargetIsCopy={setTargetIsCopy}
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
                  userIsDone={userIsDone}
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
                  isResolving={isResolving}
                />
              </Grid>
              <Grid item width='100%' height='60vh'>
                <ChatRoom
                  lastMessage={lastMessage}
                  userIsDone={userIsDone}
                  userEndTurn={userEndTurn}
                />
              </Grid>
            </Grid>
          </Grid>
        </Grid>
        <Dialog id="question-dialog"
          open={openQuestionDialog}
        >
          <DialogTitle id="question-dialog-title">
            {"Question"}
          </DialogTitle>
          <DialogContent>
            <DialogContentText id="question-dialog-description">
              {questionData?.question || null}
            </DialogContentText>
            {questionData?.options? (
              <Select
                value={answer}
                onChange={handleAnswerChange}
                fullWidth={true}
              >
                {questionData.options.map((option) => (
                  <MenuItem key={option} value={option}>{option}</MenuItem>
                ))}
              </Select>
            ) : (
              <TextField>
              </TextField>
            )}
          </DialogContent>
          <DialogActions>
            <Button onClick={handleAnswer} autoFocus>Submit</Button>
          </DialogActions>
        </Dialog>
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
        <CreateTokenDialog
          open={openCreateTokenDialog} setOpen={setOpenCreateTokenDialog}
          actionTargetCard={actionTargetCard} isCopy={targetIsCopy}
        />
        <InspectGherkinDialog
          open={openInspectGherkinDialog} setOpen={setOpenInspectGherkinDialog}
          actionTargetCard={actionTargetCard}
          cardName={inspectCardName}
          gherkin={inspectGherkin}
          sendMessage={sendMessage}
        />
      </>
    )
  } else {
    return null;
  }
}
