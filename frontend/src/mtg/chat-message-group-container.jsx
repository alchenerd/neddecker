import Grid from '@mui/material/Grid';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import ChatMessageContainer from './chat-message-container';
import { useEffect } from 'react';

const ChatMessageGroupContainer = ({
  groupIndex,
  actionQueue,
  messageGroup,
  index,
  joiningActions,
  setJoiningActions,
  setStartIndex,
  setEndIndex
}) => {
  return (
    <>
      <Grid item container spacing={1} xs={12} display="flex" justifyContent="flex-end">
        <Box
          sx={{
            width: "75%",
            borderRadius: "5px",
            backgroundColor: "grey",
          }}
        >
          <Typography align="center">{messageGroup.tag}</Typography>
          {messageGroup.group && messageGroup.group.map((message, index) => {
            const who = ("user_action" in message)? "user" : "ned";
            return (
              <ChatMessageContainer
                key={who + "-action-" + groupIndex + "-" + index}
                actionQueue={actionQueue}
                message={message}
                index={index}
                joiningActions={joiningActions}
                setJoiningActions={setJoiningActions}
                setStartIndex={setStartIndex}
                setEndIndex={setEndIndex}
              />
            );
          })}
        </Box>
      </Grid>
    </>
  )
}

export default ChatMessageGroupContainer;
