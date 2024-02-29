import { useState, useEffect } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'
import { useDrop } from 'react-dnd'
import { useSelector } from 'react-redux';
import { ItemTypes } from './constants'
import { Card } from './card'
import Permanent from './permanent'
import Library from './library'
import Graveyard from './graveyard'
import Exile from './exile'
import ZoneButton from './zone-button'
import { useAffectedGameDataSelector } from './../store/slice';

const Battlefield = ({
  ownerName,
  setFocusedCard,
  setDndMsg,
  setDblClkMsg,
  setWhoRequestShuffle,
  setActionTargetCard,
  setOpenMoveDialog,
  setOpenCounterDialog,
  setOpenAnnotationDialog,
}) => {
  const gameData = useAffectedGameDataSelector();
  const owner = gameData?.board_state?.players.find((player) => player.player_name === ownerName);
  const ownerIndex = gameData?.board_state?.players.indexOf(owner);

  const concatTextThatMightHaveCardType = (card) => {
    const majorTypeLine = card.type_line;
    const frontTypeLine = card.faces?.front.type_line;
    const backTypeLine = card.faces?.back.type_line;
    const annotationsString = JSON.stringify(card.annotations);
    return ((majorTypeLine +
           (card.isFlipped ? backTypeLine : frontTypeLine) +
           annotationsString) || "").toLowerCase()
  }

  const creatureCards = owner?.battlefield.filter(card => concatTextThatMightHaveCardType(card).includes("creature"));
  const landCards = owner?.battlefield.filter(card => {
    const text = concatTextThatMightHaveCardType(card);
    return !text.includes("creature") && text.includes("land");
  });
  const otherCards = owner?.battlefield.filter(card => {
    const text = concatTextThatMightHaveCardType(card);
    return !text.includes("creature") && !text.includes("land");
  });

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
            id: item.in_game_id,
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
                key={card.in_game_id}
                card={card}
                setFocusedCard={setFocusedCard}
                onDoubleClick={toggleTap}
                setActionTargetCard={setActionTargetCard}
                setOpenMoveDialog={setOpenMoveDialog}
                setOpenCounterDialog={setOpenCounterDialog}
                setOpenAnnotationDialog={setOpenAnnotationDialog}
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
                  key={card.in_game_id}
                  card={card}
                  setFocusedCard={setFocusedCard}
                  onDoubleClick={toggleTap}
                  setActionTargetCard={setActionTargetCard}
                  setOpenMoveDialog={setOpenMoveDialog}
                  setOpenCounterDialog={setOpenCounterDialog}
                  setOpenAnnotationDialog={setOpenAnnotationDialog}
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
                  key={card.in_game_id}
                  card={card}
                  setFocusedCard={setFocusedCard}
                  onDoubleClick={toggleTap}
                  setActionTargetCard={setActionTargetCard}
                  setOpenMoveDialog={setOpenMoveDialog}
                  setOpenCounterDialog={setOpenCounterDialog}
                  setOpenAnnotationDialog={setOpenAnnotationDialog}
                />
              )
            })}
          </Box>
        </Box>
        <Library
          owner={owner}
          content={owner?.library}
          setDndMsg={setDndMsg}
          setDblClkMsg={setDblClkMsg}
          setFocusedCard={setFocusedCard}
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
            setFocusedCard={setFocusedCard}
          />
          <Graveyard
            owner={owner}
            setFocusedCard={setFocusedCard}
          />
          <ZoneButton id="graveyardButton"
            zoneName="graveyard"
            buttonText="💀"
            owner={owner}
            content={owner?.graveyard}
            setActionTargetCard={setActionTargetCard}
            setOpenMoveDialog={setOpenMoveDialog}
            setOpenCounterDialog={setOpenCounterDialog}
            setOpenAnnotationDialog={setOpenAnnotationDialog}
            sx={{
              position: "absolute",
              top: "12px",
              right: "4px",
            }}
          />
          <ZoneButton id="exileButton"
            zoneName="exile"
            buttonText="❌"
            owner={owner}
            content={owner?.exile}
            setActionTargetCard={setActionTargetCard}
            setOpenMoveDialog={setOpenMoveDialog}
            setOpenCounterDialog={setOpenCounterDialog}
            setOpenAnnotationDialog={setOpenAnnotationDialog}
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

export default Battlefield;
