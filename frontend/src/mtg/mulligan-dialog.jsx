import { useState, useEffect } from 'react'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogTitle from '@mui/material/DialogTitle'
import Button from '@mui/material/Button'
import Box from '@mui/material/Box'
import { DndProvider, useDrop } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import { Card } from './card'
import { ItemTypes } from './constants'

const Placeholder = ({id, hand, content, setMoveMessage, ...props}) => {
  let toShow = content;
  if (props.rightmost) {
    toShow = [...content, ...props.rightmost];
  }

  const [, drop] = useDrop(
    () => ({
      accept: ItemTypes.MTG_CARD,
      drop: (item) => {
        setMoveMessage({
          id: item.id,
          to: id,
        });
      },
    }), []
  )

  return (
    <Box
      ref={drop}
      sx={{
        display: "flex",
        width: "100%",
        height: "100%",
        flexDirection: props.dir || "row",
        overflow: "hidden",
      }}
    >
      {toShow.map((card, index) => {
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

export function MulliganDialog({
    open, setOpen,
    data,
    cardImageMap,
    setToBottom,
    setRequestMulligan,
    setRequestKeepHand,
    ...props}) {
  const toBottom = data.to_bottom;
  const [mulliganHand, setMulliganHand] = useState([]);
  const [mulliganBottom, setMulliganBottom] = useState([]);
  const [moveMessage, setMoveMessage] = useState({});
  const [handSizeOK, setHandSizeOK] = useState(false);
  const library = [{id: "library", name: "library", imageUrl: "", backgroundColor: "#dddddd"},];

  function handleMulligan() {
    setOpen(false);
    setRequestMulligan(true);
    setMulliganBottom([]);
  }

  function handleKeep() {
    setOpen(false);
    setRequestKeepHand(true);
    setToBottom(mulliganBottom);
    setMulliganBottom([]);
  }

  useEffect(() => {
    setRequestKeepHand(false);
    setRequestMulligan(false);
  }, []);

  useEffect(() => {
    if (data.hand) {
      setMulliganHand(data.hand.map((card) => ({
        id: card.id,
        name: card.name,
        imageUrl: cardImageMap[card.name] || cardImageMap[card.name.split(" // ")[0]],
        backImageUrl: cardImageMap[card.name.split(" // ")[1]] || "",
      })));
    }
  }, [data]);

  useEffect(() => {
    setHandSizeOK(mulliganHand.length + toBottom === 7);
  }, [mulliganHand]);

  useEffect(() => {
    const tid = moveMessage.id || "";
    const tdest = moveMessage.to || "";
    let t = mulliganHand.find(card => card.id === tid);
    if (!t) {
      t = mulliganBottom.find(card => card.id === tid);
    }
    setMulliganHand(prev => prev.filter(card => card.id !== tid));
    setMulliganBottom(prev => prev.filter(card => card.id !== tid));
    if (tdest === "to_bottom") {
      setMulliganBottom(prev => [...prev, t]);
    } else if (tdest === "hand") {
      setMulliganHand(prev => [...prev, t]);
    }
  }, [moveMessage]);

  return (
    <Dialog
      open={open}
      maxWidth='md'
    >
      <DialogTitle>Mulligan</DialogTitle>
        <DialogContent sx={{overflow: "hidden"}}>
          <Placeholder
            id="to_bottom"
            dir="row-reverse"
            content={mulliganBottom}
            setMoveMessage={setMoveMessage}
            rightmost={library}
          />
        </DialogContent>
        <DialogContent sx={{overflow: "hidden"}}>
          <Placeholder
            id="hand"
            dir="row"
            content={mulliganHand}
            setMoveMessage={setMoveMessage}
          />
        </DialogContent>
      <DialogActions>
        <Button
          onClick={handleMulligan}
          variant="contained"
        >
          Mulligan to {7 - toBottom - 1}
        </Button>
        <Button
          onClick={handleKeep}
          variant="contained"
          disabled={!handSizeOK}
        >
          Keep {7 - toBottom}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
