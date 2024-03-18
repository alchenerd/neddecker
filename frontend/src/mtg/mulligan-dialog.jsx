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

const Placeholder = ({componentId, hand, content, setMoveMessage, rightmost, ...props}) => {
  let toShow = content;

  if (rightmost) {
    toShow = [...toShow, ...rightmost];
  }

  const [, drop] = useDrop(
    () => ({
      accept: [
        ItemTypes.MTG_LAND_CARD,
        ItemTypes.MTG_SORCERY_CARD,
        ItemTypes.MTG_INSTANT_CARD,
        ItemTypes.MTG_NONLAND_PERMANENT_CARD,
      ],
      drop: (item) => {
        setMoveMessage({
          id: item.in_game_id,
          to: componentId,
        });
      },
    }), []
  )

  return (
    <Box
      ref={drop}
      sx={{
        display: "flex",
        justifyContent: "start",
        width: "50vw",
        height: "20vh",
        flexDirection: props.dir || "row",
        overflow: "auto",
      }}
    >
      {toShow.map((card, index) => {
        return (
          <Card
            key={card?.in_game_id}
            card={card || null}
            backgroundColor={card?.backgroundColor || "white"}
            canDrag={card?.canDrag}
          />
        )
      })}
    </Box>
  );
}

export function MulliganDialog({
    open, setOpen,
    data,
    setToBottom,
    setRequestMulligan,
    setRequestKeepHand,
}) {
  const toBottom = data.to_bottom;
  const [mulliganHand, setMulliganHand] = useState([]);
  const [mulliganBottom, setMulliganBottom] = useState([]);
  const [moveMessage, setMoveMessage] = useState({});
  const [handSizeOK, setHandSizeOK] = useState(false);
  const library = [{
      in_game_id: "library",
      name: "Library",
      imageUrl: "",
      backgroundColor: "#dddddd",
      canDrag: "false"
  },];

  function handleMulligan() {
    setOpen(false);
    setRequestMulligan(true);
    setMulliganBottom([]);
  }

  function handleKeep() {
    setOpen(false);
    setToBottom(mulliganBottom);
    setRequestKeepHand(true);
    setMulliganBottom([]);
  }

  useEffect(() => {
    setRequestKeepHand(false);
    setRequestMulligan(false);
  }, []);

  useEffect(() => {
    console.log("inspecting", data);
    if (data.hand) {
      setMulliganHand(data.hand);
    }
  }, [data]);

  useEffect(() => {
    setHandSizeOK(mulliganHand.length + toBottom === 7);
  }, [mulliganHand]);

  useEffect(() => {
    const tid = moveMessage.id || "";
    const tdest = moveMessage.to || "";
    let t = mulliganHand.find((card) => card.in_game_id === tid);
    console.log(t, tid);
    if (!t) {
      t = mulliganBottom.find((card) => card.in_game_id === tid);
    }
    setMulliganHand(prev => prev.filter(card => card.in_game_id !== tid));
    setMulliganBottom(prev => prev.filter(card => card.in_game_id !== tid));
    if (tdest === "to_bottom") {
      setMulliganBottom(prev => [...prev, t]);
    } else if (tdest === "hand") {
      setMulliganHand(prev => [...prev, t]);
    }
    console.log(mulliganHand, mulliganBottom);
  }, [moveMessage]);

  return (
    <Dialog
      open={open}
      maxWidth='md'
    >
      <DialogTitle>Mulligan</DialogTitle>
        <DialogContent sx={{overflow: "hidden"}}>
          <Placeholder
            componentId="to_bottom"
            dir="row"
            content={mulliganBottom}
            setMoveMessage={setMoveMessage}
            rightmost={library}
          />
        </DialogContent>
        <DialogContent sx={{overflow: "hidden"}}>
          <Placeholder
            componentId="hand"
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
