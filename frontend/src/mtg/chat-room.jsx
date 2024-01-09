import { useState, useEffect, useRef } from 'react'
import Box from '@mui/material/Box'
import Grid from '@mui/material/Grid'
import TextField from '@mui/material/TextField'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import MicIcon from '@mui/icons-material/Mic'
import PlayArrowIcon from '@mui/icons-material/PlayArrow'

export function ChatRoom({lastMessage, ...props}) {
  const [chatHistory, setChatHistory] = useState([]);
  const chatroomRef = useRef(null);

  useEffect(() => {
    if (lastMessage) {
      const data = JSON.parse(lastMessage.data);
      switch(data.type) {
        case "log":
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
              " has started.\n" +
              data.who_goes_first + " goes first.\n"
          }]));
          break;
      }
    }
  }, [lastMessage]);

  useEffect(() => {
    if (chatroomRef.current && chatroomRef.current.scrollTo) {
      chatroomRef.current.scrollTo(0, chatroomRef.current.scrollHeight);
    }
  }, [chatroomRef, chatHistory]);

  return (
    <Box sx={{display: "flex", height: "100%", width: "100%", alignItems: "center", justifyContent: "space-between", backgroundColor: "Yellow"}}>
      <Grid container sx={{height: "100%"}}>
        <Grid item xs={12} sx={{display: "flex"}}>
          <Box ref={chatroomRef} sx={{width: "100%", height: "55vh", background: "white", overflow: "auto"}}>
            {chatHistory && chatHistory.map((message, index) => {
              if ("log" in message) {
                return (
                  <Typography
                    key={index}
                    variant="subtitle1"
                    sx={{
                      color: "grey",
                      textAlign: "center",
                      textDecoration: "underline",
                    }}
                  >
                    [SYSTEM]: {message["log"]}
                  </Typography>
                )
              } else if ("ned" in message) {
                return (
                  <>
                  <Typography
                    key={index}
                    variant="body1"
                    sx={{
                      paddingLeft: "10px",
                      backgroundColor: "palegreen",
                      color: "black",
                      textAlign: "left",
                    }}
                  >
                    {message["ned"]["action"]}
                  </Typography>
                  <Typography
                    key={index}
                    variant="body1"
                    sx={{
                      paddingLeft: "10px",
                      backgroundColor: "palegreen",
                      color: "black",
                      textAlign: "left",
                    }}
                  >
                    {message["ned"]["description"]}
                  </Typography>
                  </>
                )
              } else if ("user" in message) {
                return (
                  <>
                  <Typography
                    key={index}
                    variant="body1"
                    sx={{
                      paddingRight: "10px",
                      backgroundColor: "lightblue",
                      color: "black",
                      textAlign: "right",
                    }}
                  >
                    {message["user"]["action"]}
                  </Typography>
                  <Typography
                    key={message["user"]["description"]}
                    variant="body1"
                    sx={{
                      paddingRight: "10px",
                      backgroundColor: "lightblue",
                      color: "black",
                      textAlign: "right",
                    }}
                  >
                    {message["user"]["description"]}
                  </Typography>
                  </>
                )
              }
              <p></p>
            })}
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
