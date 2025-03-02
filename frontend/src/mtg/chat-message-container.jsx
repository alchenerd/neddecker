import Grid from '@mui/material/Grid';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import CheckBoxOutlineBlankIcon from '@mui/icons-material/CheckBoxOutlineBlank';
import CloseIcon from '@mui/icons-material/Close';
import JoinFullIcon from '@mui/icons-material/JoinFull';
import store from '../store/store';
import { rollbackGameAction } from '../store/slice';
import { useEffect } from 'react';

const ChatMessageContainer = ({actionQueue, message, index, joiningActions, setJoiningActions, setStartIndex, setEndIndex}) => {
  const who = ("user_action" in message)? "user" : "ned";
  const keyName = ("user_action" in message)? "user_action" : "ned_action";
  const justify = ("user_action" in message)? "flex-end" : "flex-start";
  const messageBoxColor = ("user_action" in message)? "lightblue" : "palegreen";

  const handleCloseActionButtonClick = () => {
    store.dispatch(rollbackGameAction());
  }

  const handleJoinActionButtonClick = () => {
    setJoiningActions(true);
    setEndIndex(null);
    console.log(message)
    setStartIndex(message[keyName]['index']);
  }

  const handleSubmitJoinActionButtonClick = () => {
    setJoiningActions(false);
    console.log(message)
    setEndIndex(message[keyName]['index']);
  }

  const getActionButton = (isJoining) => {
    const Icon = (isJoining)? CheckBoxOutlineBlankIcon : JoinFullIcon;
    const handleOnClick = (isJoining)? handleSubmitJoinActionButtonClick : handleJoinActionButtonClick;
    return (
      <IconButton key={"action-" + index + "-group-btn"} value={index} onClick={handleOnClick}>
        <Icon key={"action-" + index + "-group-icon"}/>
      </IconButton>
    );
  }

  return (
    <Grid item xs={12} display="flex" justifyContent={justify}>
      <Box
        sx={{
          width: "100%",
          height: "100%",
          borderRadius: "5px",
          backgroundColor: messageBoxColor,
          color: "black",
        }}
      >
        <Box display="flex" flexDirection="row" alignItems="center" justifyContent="space-between">
          {getActionButton(joiningActions)}
          {message[keyName]['index'] === actionQueue.length - 1 ? (
            <IconButton key={"action-" + index + "-close-btn"}
              onClick={handleCloseActionButtonClick}
              alignself="flex-end"
            >
              <CloseIcon key={"action-" + index + "-close-icon"}/>
            </IconButton>
          ) : null}
        </Box>
        <Box display="flex" alignItems="center" justifyContent="center">
          <pre>
            {JSON.stringify(JSON.parse(message[keyName]["description"]), null, 2)}
          </pre>
        </Box>
      </Box>
    </Grid>
  )
}

export default ChatMessageContainer;
