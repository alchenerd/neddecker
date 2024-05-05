import { useState, useEffect, useRef } from 'react';
import Box from '@mui/material/Box';
import Grid from '@mui/material/Grid';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import Button from '@mui/material/Button';
import MicIcon from '@mui/icons-material/Mic';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import IconButton from '@mui/material/IconButton';
import CloseIcon from '@mui/icons-material/Close';
import CircularProgress from '@mui/material/CircularProgress';
import JoinFullIcon from '@mui/icons-material/JoinFull';
import _ from 'lodash';
import ChatMessageContainer from './chat-message-container';
import store from '../store/store';
import { rollbackGameAction, appendNewGrouping } from '../store/slice';
import { useSelector } from 'react-redux';

function ThinkingIndicator({isThinking}) {
    if (isThinking) {
        return (<CircularProgress />);
    }
    return null;
}

export function ChatRoom({lastMessage, userIsDone, userEndTurn, hasPriority, ...props}) {
  const [chatHistory, setChatHistory] = useState([]);
  const [actionHistory, setActionHistory] = useState([]);
  const actionQueue = useSelector((state) => state.gameState.actions);
  const groupingRecord = useSelector((state) => state.gameState.grouping);
  const chatroomRef = useRef(null);
  const [ joiningActions, setJoiningActions ] = useState(false);
  const [ startIndex, setStartIndex ] = useState(null);
  const [ endIndex, setEndIndex ] = useState(null);

  useEffect(() => {
    if (startIndex !== null && endIndex !== null) {
      const grouping = [
        "test_string",
        startIndex,
        endIndex,
      ]
      store.dispatch(appendNewGrouping(grouping));
    }
  }, [startIndex, endIndex]);

  useEffect(() => {
    if (groupingRecord) {
      console.log(groupingRecord);
    }
  }, [groupingRecord])

  useEffect(() => {
    if (lastMessage) {
      const data = JSON.parse(lastMessage.data);
      switch(data.type) {
        case "log":
        case 'who_goes_first':
        case 'ask_reveal_companion':
          setChatHistory(prev => ([...prev,
            {
              "log": data.message
            }
          ]));
          break;
        case 'game_start':
          setChatHistory(prev => ([...prev, {
            "log":
              "Game " + data.game +
              " of " + data.of +
              " has started.\n"
          }]));
          break;
      }
    }
  }, [lastMessage]);

  useEffect(() => {
    if (actionQueue) {
      setActionHistory(actionQueue.map((action) => ({
        user_action: {
          action: "[" + action.type + "]",
          description: JSON.stringify(_.omit(action, "shuffleResult"), null, 2),
        }
      })));
    }
  }, [actionQueue]);

  useEffect(() => {
    console.log(chatHistory);
    console.log(actionQueue);
    if ((userIsDone || userEndTurn) && actionQueue) {
      for (const action of actionQueue) {
        setChatHistory(prev => [ ...prev, {...action, ["action"]: action.type} ]);
      }
    }
  }, [userIsDone, userEndTurn, actionQueue]);

  useEffect(() => {
    if (chatroomRef.current && chatroomRef.current.scrollTo) {
      chatroomRef.current.scrollTo(0, chatroomRef.current.scrollHeight);
    }
  }, [chatroomRef, chatHistory, actionHistory]);


  return (
    <Box sx={{display: "flex", height: "100%", width: "100%", alignItems: "center", justifyContent: "space-between", backgroundColor: "Yellow"}}>
      <Grid container sx={{height: "100%"}}>
        <Grid item container xs={12} sx={{display: "flex"}}>
          <Box ref={chatroomRef} sx={{width: "100%", height: "55vh", background: "ghostwhite", overflow: "auto"}}>
            {chatHistory && chatHistory.map((message, index) => {
              if ("log" in message) {
                return (
                  <Grid item key={"chat-" + index} xs={12}>
                    <Typography
                      variant="subtitle1"
                      sx={{
                        color: "grey",
                        textAlign: "center",
                        textDecoration: "underline",
                        overflowWrap: "break-word",
                      }}
                    >
                      [LOG]: {message["log"]}
                    </Typography>
                  </Grid>
                )
              } else if ("action" in message) {
                return (
                  <Grid item key={"action-" + index} xs={12}>
                    <Typography
                      variant="subtitle1"
                      sx={{
                        color: "black",
                        textAlign: "center",
                        textDecoration: "underline",
                        overflowWrap: "break-word",
                      }}
                    >
                      [ACTION] - {message.action + (message.targetId ? ": " + message.targetId : "")}
                    </Typography>
                  </Grid>
                )
              } else {
                return null;
              }
            })}
            <Grid item container spacing={1}>
            {actionHistory && actionHistory.map((message, index) => {
              const who = ("user_action" in message)? "user" : "ned";
              return (
                <ChatMessageContainer
                  key={who + "-action-" + index}
                  actionHistory={actionHistory}
                  message={message}
                  index={index}
                  joiningActions={joiningActions}
                  setJoiningActions={setJoiningActions}
                  setStartIndex={setStartIndex}
                  setEndIndex={setEndIndex}
                />
              );
            })}
            </Grid>
            <Grid item xs={12} sx={{justifyContent:"center", display: "flex"}}>
              <ThinkingIndicator isThinking={userIsDone}/>
            </Grid>
          </Box>
        </Grid>
        <Grid item xs={9}>
          <TextField
            id="inputline"
            label=""
            fullWidth
            variant="outlined"
            multiline
            sx={{
              width: "100%",
              background: "white",
            }}
            InputProps={{
              style: {
                height: "5vh",
              },
            }}
          />
        </Grid>
        <Grid item xs={3}>
          <Button
            variant="contained"
            sx={{width: "50%", height: "5vh"}}
          >
            <MicIcon />
          </Button>
          <Button
            variant="contained"
            sx={{width: "50%", height: "5vh"}}
          >
            <PlayArrowIcon />
          </Button>
        </Grid>
      </Grid>
    </Box>
  )
}
