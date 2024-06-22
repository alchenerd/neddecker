import { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useDrop } from 'react-dnd';
import { useSelector } from 'react-redux';
import { ItemTypes } from './constants';
import { Card } from './card';
import Permanent from './permanent';
import CreaturePermanent from './creature-permanent';
import NonlandPermanent from './nonland-permanent';
import Library from './library';
import Graveyard from './graveyard';
import Exile from './exile';
import ZoneButton from './zone-button';
import BattlefieldContextMenu from './battlefield-context-menu';
import { selectAffectedGameData } from './../store/slice';
import store from './../store/store';

const Battlefield = ({
  ownerName,
  setFocusedCard,
  setDndMsg,
  setDblClkMsg,
  setWhoRequestShuffle,
  actionTargetCard,
  setActionTargetCard,
  setOpenMoveDialog,
  setOpenCounterDialog,
  setOpenAnnotationDialog,
  setOpenCreateTriggerDialog,
  setOpenCreateDelayedTriggerDialog,
  whoIsAskingAttackTarget,
  setWhoIsAskingAttackTarget,
  whoIsAskingBlockTarget,
  setWhoIsAskingBlockTarget,
  combatTargetCard,
  setCombatTargetCard,
  setOpenCreateTokenDialog,
  setOpenInspectGherkinDialog,
  setTargetIsCopy,
}) => {
  const gameData = selectAffectedGameData(store.getState());
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

  const [ contextMenu, setContextMenu ] = useState(null);
  const handleBattlefieldContext = (event) => {
    event.preventDefault();
    event.stopPropagation();
    setContextMenu(
      contextMenu === null ? { mouseX: event.clientX + 2, mouseY: event.clientY - 6, }
                           : null
    );
  }

  const battlefieldFunctions = [
    {
      name: "create token", _function: () => {
        setActionTargetCard(null);
        setOpenCreateTokenDialog(true);
      },
    },
  ];

  return (
    <>
      <Box sx={{display: "flex", flexDirection: "column", width: "100%", height: "100%", background: "navy", position: "relative", alignItems: "center", justifyContent: "center"}} ref={drop} onContextMenu={handleBattlefieldContext}>
        <Box id="creatureZone"
          sx={{
            display: "flex",
            borderStyle: "solid",
            boarderWidth: "1px",
            borderColor: "red",
            height: "45%",
            width: "88.55%",
            alignSelf: "flex-start",
            justifyContent: "space-around",
          }}
        >
          {creatureCards && creatureCards.map(card => {
            return (
              <CreaturePermanent
                key={card.in_game_id}
                card={card}
                setFocusedCard={setFocusedCard}
                onDoubleClick={toggleTap}
                setActionTargetCard={setActionTargetCard}
                setOpenMoveDialog={setOpenMoveDialog}
                setOpenCounterDialog={setOpenCounterDialog}
                setOpenAnnotationDialog={setOpenAnnotationDialog}
                setOpenCreateTriggerDialog={setOpenCreateTriggerDialog}
                setOpenCreateDelayedTriggerDialog={setOpenCreateDelayedTriggerDialog}
                controller={ownerName}
                {...{whoIsAskingAttackTarget, setWhoIsAskingAttackTarget}}
                {...{whoIsAskingBlockTarget, setWhoIsAskingBlockTarget}}
                {...{combatTargetCard, setCombatTargetCard}}
                setOpenCreateTokenDialog={setOpenCreateTokenDialog}
                setOpenInspectGherkinDialog={setOpenInspectGherkinDialog}
              />
            )
          })}
        </Box>
        <Box id="nonCreatureZone"
          sx={{
            display: "flex",
            flexDirection: "row",
            height: "45%",
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
                  setOpenCreateTriggerDialog={setOpenCreateTriggerDialog}
                  setOpenCreateDelayedTriggerDialog={setOpenCreateDelayedTriggerDialog}
                  setOpenCreateTokenDialog={setOpenCreateTokenDialog}
                  setOpenInspectGherkinDialog={setOpenInspectGherkinDialog}
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
                <NonlandPermanent
                  key={card.in_game_id}
                  card={card}
                  setFocusedCard={setFocusedCard}
                  onDoubleClick={toggleTap}
                  setActionTargetCard={setActionTargetCard}
                  setOpenMoveDialog={setOpenMoveDialog}
                  setOpenCounterDialog={setOpenCounterDialog}
                  setOpenAnnotationDialog={setOpenAnnotationDialog}
                  setOpenCreateTriggerDialog={setOpenCreateTriggerDialog}
                  setOpenCreateDelayedTriggerDialog={setOpenCreateDelayedTriggerDialog}
                  controller={ownerName}
                  {...{whoIsAskingAttackTarget, setWhoIsAskingAttackTarget}}
                  {...{combatTargetCard, setCombatTargetCard}}
                  setOpenCreateTokenDialog={setOpenCreateTokenDialog}
                  setOpenInspectGherkinDialog={setOpenInspectGherkinDialog}
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
          setOpenCreateTriggerDialog={setOpenCreateTriggerDialog}
          setOpenCreateDelayedTriggerDialog={setOpenCreateDelayedTriggerDialog}
          setOpenCreateTokenDialog={setOpenCreateTokenDialog}
          setTargetIsCopy={setTargetIsCopy}
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
            setOpenCreateTriggerDialog={setOpenCreateTriggerDialog}
            setOpenCreateDelayedTriggerDialog={setOpenCreateDelayedTriggerDialog}
            setOpenCreateTokenDialog={setOpenCreateTokenDialog}
            setTargetIsCopy={setTargetIsCopy}
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
            setOpenCreateTriggerDialog={setOpenCreateTriggerDialog}
            setOpenCreateDelayedTriggerDialog={setOpenCreateDelayedTriggerDialog}
            setOpenCreateTokenDialog={setOpenCreateTokenDialog}
            setTargetIsCopy={setTargetIsCopy}
            sx={{
              position: "absolute",
              bottom: "12px",
              right: "4px",
            }}
          />
        </Box>
      </Box>
      <BattlefieldContextMenu contextMenu={contextMenu} setContextMenu={setContextMenu} functions={battlefieldFunctions}/>
    </>
  )
}

export default Battlefield;
