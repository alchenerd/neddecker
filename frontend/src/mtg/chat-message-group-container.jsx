import Grid from '@mui/material/Grid';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import ChatMessageContainer from './chat-message-container';
import { useEffect } from 'react';
import store from '../store/store';
import { setGroupTag } from '../store/slice';

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
  const handleGroupTagChange = (e) => {
    store.dispatch(setGroupTag({tag: e.target.textContent, index: Object.values(messageGroup.group[0])[0].index}));
  }
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
          <Typography
            align="center"
            suppressContentEditableWarning={true}
            contentEditable={true}
            onBlur={handleGroupTagChange}>
            {messageGroup.tag}
          </Typography>
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
