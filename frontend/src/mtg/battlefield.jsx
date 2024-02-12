import { useState, useEffect } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import { useDrop } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import { ItemTypes } from './constants'
import { Card } from './card'
import Permanent from './permanent'
import Library from './library'
import Graveyard from './graveyard'
import Exile from './exile'
import ZoneButton from './zone-button'

export function Battlefield({map, setSelectedCard, owner, ownerIndex, setDndMsg, setDblClkMsg, setWhoRequestShuffle, setActionTargetCard, setOpenMoveDialog, setOpenCounterDialog, ...props}) {
  const [toShow, setToShow] = useState([]);
  const [creatureCards, setCreatureCards] = useState([]);
  const [landCards, setLandCards] = useState([]);
  const [otherCards, setOtherCards] = useState([]);
  const [libraryCards, setLibraryCards] = useState([]);
  const [graveyardCards, setGraveyardCards] = useState([]);
  const [exileCards, setExileCards] = useState([]);

  const processCard = (card) => {
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
      counters: card.counters ?? {},
      annotations: card.annotations ?? {},
    }
    return {...processedCard};
  }

  useEffect(() => {
    setCreatureCards([]);
    setLandCards([]);
    setOtherCards([]);
    owner.battlefield?.map((card) => {
      const processedCard = processCard(card);
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

  useEffect(() => {
    setLibraryCards([]);
    owner.library?.map((card) => {
      const processedCard = processCard(card);
      setLibraryCards((prev) => [...prev, processedCard]);
    });
  }, [owner.library]);

  useEffect(() => {
    setGraveyardCards([]);
    owner.graveyard?.map((card) => {
      const processedCard = processCard(card);
      setGraveyardCards((prev) => [...prev, processedCard]);
    });
  }, [owner.graveyard]);

  useEffect(() => {
    setExileCards([]);
    owner.exile?.map((card) => {
      const processedCard = processCard(card);
      setExileCards((prev) => [...prev, processedCard]);
    });
  }, [owner.exile]);

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
            width: "89%",
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
                counters={card.counters}
                annotations={card.annotations}
                onDoubleClick={toggleTap}
                setActionTargetCard={setActionTargetCard}
                setOpenMoveDialog={setOpenMoveDialog}
                setOpenCounterDialog={setOpenCounterDialog}
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
            justifyContent: "flex-start",
          }}
        >
          <Box id="landZone"
            sx={{
              display: "flex",
              borderStyle: "solid",
              boarderWidth: "1px",
              borderColor: "green",
              height: "100%",
              width: "44%",
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
                  counters={card.counters}
                  annotations={card.annotations}
                  onDoubleClick={toggleTap}
                  setActionTargetCard={setActionTargetCard}
                  setOpenMoveDialog={setOpenMoveDialog}
                  setOpenCounterDialog={setOpenCounterDialog}
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
              width: "44%",
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
                  counters={card.counters}
                  annotations={card.annotations}
                  onDoubleClick={toggleTap}
                  setActionTargetCard={setActionTargetCard}
                  setOpenMoveDialog={setOpenMoveDialog}
                  setOpenCounterDialog={setOpenCounterDialog}
                />
              )
            })}
          </Box>
        </Box>
        <Library
          owner={owner}
          ownerIndex={ownerIndex}
          content={libraryCards}
          setDndMsg={setDndMsg}
          setDblClkMsg={setDblClkMsg}
          setSelectedCard={setSelectedCard}
          setWhoRequestShuffle={setWhoRequestShuffle}
          setActionTargetCard={setActionTargetCard}
          setOpenMoveDialog={setOpenMoveDialog}
        />
        <Box id="graveyardExileBox"
          sx={{
            position: "absolute",
            bottom: 0,
            right: 0,
            margin:"20px",
            height: "40%"
          }}
        >
          <Exile
            owner={owner}
            content={exileCards}
            setSelectedCard={setSelectedCard}
          />
          <Graveyard
            owner={owner}
            content={graveyardCards}
            setSelectedCard={setSelectedCard}
          />
          <ZoneButton id="graveyardButton"
            zoneName="graveyard"
            buttonText="💀"
            ownerName={owner.player_name}
            content={graveyardCards}
            setActionTargetCard={setActionTargetCard}
            setOpenMoveDialog={setOpenMoveDialog}
            setOpenCounterDialog={setOpenCounterDialog}
            sx={{
              position: "absolute",
              top: "12px",
              right: "4px",
            }}
          />
          <ZoneButton id="exileButton"
            zoneName="exile"
            buttonText="❌"
            ownerName={owner.player_name}
            content={exileCards}
            setActionTargetCard={setActionTargetCard}
            setOpenMoveDialog={setOpenMoveDialog}
            setOpenCounterDialog={setOpenCounterDialog}
            sx={{
              position: "absolute",
              bottom: "12px",
              right: "4px",
            }}
          />
        </Box>
      </Box>
    </>
  )
}
