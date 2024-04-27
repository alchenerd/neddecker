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
import _ from 'lodash';
import store from '../store/store';
import { rollbackGameAction } from '../store/slice';
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
  const chatroomRef = useRef(null);

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
          description: JSON.stringify(_.omit(action, "shuffleResult")),
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

  const handleCloseActionButtonClick = () => {
    store.dispatch(rollbackGameAction());
  }

  return (
    <Box sx={{display: "flex", height: "100%", width: "100%", alignItems: "center", justifyContent: "space-between", backgroundColor: "Yellow"}}>
      <Grid container sx={{height: "100%"}}>
        <Grid item xs={12} sx={{display: "flex"}}>
          <Box ref={chatroomRef} sx={{width: "100%", height: "55vh", background: "ghostwhite", overflow: "auto"}}>
            {chatHistory && chatHistory.map((message, index) => {
              if ("log" in message) {
                return (
                  <Typography
                    key={"chat-" + index}
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
                )
              } else if ("action" in message) {
                return (
                  <Typography
                    key={"action-" + index}
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
                )
              } else {
                return null;
              }
            })}
            {actionHistory && actionHistory.map((message, index) => {
              if ("ned_action" in message) {
                return (
                  <div key={"ned-action-" + index}>
                    <Typography
                      key={"ned-action-title-" + index}
                      variant="body1"
                      sx={{
                        paddingLeft: "10px",
                        backgroundColor: "palegreen",
                        color: "black",
                        textAlign: "left",
                        overflowWrap: "break-word",
                      }}
                    >
                      {message["ned_action"]["action"]}
                    </Typography>
                    <Typography
                      key={"ned-action-" + index}
                      variant="body1"
                      sx={{
                        paddingLeft: "10px",
                        backgroundColor: "palegreen",
                        color: "black",
                        textAlign: "left",
                        overflowWrap: "break-word",
                      }}
                    >
                      {message["ned_action"]["description"]}
                    </Typography>
                  </div>
                )
              } else if ("user_action" in message) {
                return (
                  <div key={"user-action-" + index}>
                    <Typography
                      key={"user-action-title-" + index}
                      variant="body1"
                      sx={{
                        paddingRight: "10px",
                        backgroundColor: "lightblue",
                        color: "black",
                        textAlign: "right",
                        overflowWrap: "break-word",
                      }}
                    >
                      {message["user_action"]["action"]}
                    </Typography>
                    <Typography
                      key={"user-action-desc-" + index}
                      variant="body1"
                      sx={{
                        paddingRight: "10px",
                        backgroundColor: "lightblue",
                        color: "black",
                        textAlign: "right",
                        overflowWrap: "break-word",
                      }}
                    >
                      {message["user_action"]["description"]}
                      {index === actionHistory.length - 1 ? (
                        <IconButton key={"action-" + index + "-close-btn"} onClick={handleCloseActionButtonClick}>
                          <CloseIcon key={"action-" + index + "-close-icon"}/>
                        </IconButton>
                      ) : null}
                    </Typography>
                  </div>
                )
              }
              <p></p>
            })}
            <Box sx={{justifyContent:"center", display: "flex"}}>
              <ThinkingIndicator isThinking={userIsDone}/>
            </Box>
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
