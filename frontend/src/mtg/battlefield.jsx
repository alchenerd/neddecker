import { useState, useEffect } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import { DndProvider, useDrop } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import { ItemTypes } from './constants'
import { Card } from './card'
import Permanent from './permanent'

export function Battlefield({library, map, setSelectedCard, owner, ownerIndex, setDndMsg, setDblClkMsg, ...props}) {
  const [toShow, setToShow] = useState([]);
  const [creatureCards, setCreatureCards] = useState([]);
  const [landCards, setLandCards] = useState([]);
  const [otherCards, setOtherCards] = useState([]);

  useEffect(() => {
    setCreatureCards([]);
    setLandCards([]);
    setOtherCards([]);
    owner.battlefield?.map((card) => {
      const processedCard = {
        id: card.id,
        name: card.name,
        imageUrl: map[card.name] || map[card.name.split(" // ")[0]],
        backImageUrl: map[card.name.split(" // ")[1]] || "",
        isFlipped: card?.isFlipped || false,
        typeLine: card?.isFlipped ?
          (card?.faces?.back.type_line || "") :
          (card?.faces?.front.type_line || card.type_line || ""),
        manaCost: card.mana_cost,
        annotations: card.annotations ?? {},
      }
      const couldHaveCardType =
        JSON.stringify(processedCard.typeLine).toLowerCase() +
        (JSON.stringify(processedCard?.annotations).toLowerCase() || "");
      if (couldHaveCardType.includes("creature")) {
        setCreatureCards((prev) => [...prev, processedCard]);
      } else if (couldHaveCardType.includes("land")) {
        setLandCards((prev) => [...prev, processedCard]);
      } else {
        setOtherCards((prev) => [...prev, processedCard]);
      }
    });
  }, [owner.battlefield]);

  const [, drop] = useDrop(
    () => ({
      accept: [
        ItemTypes.MTG_LAND_CARD,
        ItemTypes.MTG_NONLAND_PERMANENT_CARD,
        ItemTypes.MTG_TOKEN,
      ],
      drop: (item, monitor) => {
        console.log("Detected", item.type, "moving to", owner.player_name, "'s battlefield");
        setDndMsg(
          {
            id: item.id,
            to: "board_state.players[" + ownerIndex + "].battlefield",
          }
        );
      },
    }), [owner]
  );

  const renderLibrary = (cond) => {
    if (cond) {
      return (
        <Card
          canDrag="false"
          sx={{
            position: "absolute",
            top: 0,
            right: 0,
            margin:"10px",
            height: "40%"
          }}
          backgroundColor="#c0ffee"
          onDoubleClick={drawFromTop}
        />
      )
    }
  }

  const toggleTap = (e) => {
    console.log("Detected", e?.currentTarget?.id, "tapping/untapping at", owner.player_name, "'s battlefield");
    setDblClkMsg(
      {
        id: e?.currentTarget?.id,
        type: "toggleTap",
      }
    );
  }

  const drawFromTop = (e) => {
    console.log("Detected", owner.player_name, "drawing from their library");
    setDblClkMsg(
      {
        id: null,
        type: "drawFromLibrary",
        who: owner.player_name,
      }
    );
  }

  return (
    <>
      <Box sx={{display: "flex", flexDirection: "column", width: "100%", height: "100%", background: "navy", position: "relative", alignItems: "center"}} ref={drop}>
        <Typography sx={{alignSelf: "flex-start"}}>Battlefield</Typography>
          <Box id="creatureZone"
            sx={{
              display: "flex",
              borderStyle: "solid",
              boarderWidth: "1px",
              borderColor: "red",
              height: "40%",
              width: "90%",
              alignSelf: "flex-start",
              justifyContent: "space-around",
            }}
          >
            {creatureCards && creatureCards.map(card => {
              return (
                <Permanent
                  key={card.id}
                  id={card.id}
                  name={card.name}
                  imageUrl={card.imageUrl}
                  backImageUrl={card.backImageUrl}
                  setSelectedCard={setSelectedCard}
                  typeLine={card.typeLine}
                  manaCost={card.manaCost}
                  annotations={card.annotations}
                  onDoubleClick={toggleTap}
                />
              )
            })}
          </Box>
          <Box id="nonCreatureZone"
            sx={{
              display: "flex",
              flexDirection: "row",
              height: "40%",
              width: "100%",
              alignSelf: "flex-end",
              justifyContent: "space-between",
            }}
          >
            <Box id="landZone"
              sx={{
                display: "flex",
                borderStyle: "solid",
                boarderWidth: "1px",
                borderColor: "green",
                height: "100%",
                width: "40%",
                justifySelf: "flex-start",
                justifyContent: "space-around",
              }}
            >
              {landCards && landCards.map(card => {
                return (
                  <Permanent
                    key={card.id}
                    id={card.id}
                    name={card.name}
                    imageUrl={card.imageUrl}
                    backImageUrl={card.backImageUrl}
                    setSelectedCard={setSelectedCard}
                    typeLine={card.typeLine}
                    manaCost={card.manaCost}
                    annotations={card.annotations}
                    onDoubleClick={toggleTap}
                  />
                )
              })}
            </Box>
            <Box id="otherZone"
              sx={{
                display: "flex",
                borderStyle: "solid",
                boarderWidth: "1px",
                borderColor: "blue",
                height: "100%",
                width: "40%",
                justifySelf: "flex-end",
                justifyContent: "space-around",
              }}
            >
              {otherCards && otherCards.map(card => {
                return (
                  <Permanent
                    key={card.id}
                    id={card.id}
                    name={card.name}
                    imageUrl={card.imageUrl}
                    backImageUrl={card.backImageUrl}
                    setSelectedCard={setSelectedCard}
                    typeLine={card.typeLine}
                    manaCost={card.manaCost}
                    annotations={card.annotations}
                    onDoubleClick={toggleTap}
                  />
                )
              })}
            </Box>
          </Box>
        {renderLibrary(library && library.length > 0)}
      </Box>
    </>
  )
}
