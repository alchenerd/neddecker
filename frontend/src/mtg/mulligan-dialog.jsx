import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogTitle from '@mui/material/DialogTitle'
import Button from '@mui/material/Button'
import Box from '@mui/material/Box'
import { Hand } from './hand'
import { Card } from './card'

const Placeholder = (props) => {
  const content = props.content;
  return (
    <Box
      sx={{
        display: "flex",
        width: "100%",
        height: "100%",
        flexDirection: props.dir || "row",
        overflow: "auto",
      }}>
      {content.map(card => {
        return (
          <Card
            key={card.id}
            id={card.id}
            name={card.name}
            imageUrl={card.imageUrl}
            backgroundColor={card.backgroundColor}
          />
        )
      })}
    </Box>
  );
}

export function MulliganDialog(props) {
  const setOpen = props.setOpen;
  const hand = props.hand || [];
  const setHand = props.setHand;
  const library = [{id: "library", name: "library", imageUrl: "", backgroundColor: "#dddddd"},];

  function handleMulligan() {
    setOpen(false);
  }

  function handleKeep() {
    setOpen(false);
  }

  return (
    <Dialog
      open={props.open}
      maxWidth='md'
    >
      <DialogTitle>Mulligan</DialogTitle>
      <DialogContent>
        <Placeholder dir='row-reverse' content={library}/>
      </DialogContent>
      <DialogContent>
        <Placeholder dir='row' content={hand}/>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleMulligan}>Mulligan to {7 - props.toBottom - 1}</Button>
        <Button onClick={handleKeep}>Keep {7 - props.toBottom}</Button>
      </DialogActions>
    </Dialog>
  );
}
