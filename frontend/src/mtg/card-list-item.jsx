import { useEffect, useState } from 'react';
import Box from '@mui/material/Box';
import CardContextMenu from './card-context-menu';
import './card-list-item.css';

function CardListItem ({id, card, zoneName, setActionTargetCard, setOpenMoveDialog, setOpenCounterDialog, setOpenAnnotationDialog, setOpenCreateTriggerDialog, setOpenCreateDelayedTriggerDialog, setOpenCreateTokenDialog}) {
  const [contextMenu, setContextMenu] = useState(null);
  const [showString, setShowString] = useState(null);
  const handleContextMenu = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setContextMenu(
      contextMenu === null
      ? {
        mouseX: e.clientX + 2,
        mouseY: e.clientY - 6,
        }
      : null,
    )
  };
  const handleMove = () => {
    setActionTargetCard(card);
    setOpenMoveDialog(true);
  };
  const handleSetCounter = () => {
    setActionTargetCard(card)
    setOpenCounterDialog(true);
  }
  const handleSetAnnotation = () => {
    setActionTargetCard(card)
    setOpenAnnotationDialog(true);
  }
  const handleCreateTrigger = () => {
    setActionTargetCard(card);
    setOpenCreateTriggerDialog(true);
  }
  const handleCreateDelayedTrigger = () => {
    setActionTargetCard(card);
    setOpenCreateDelayedTriggerDialog(true);
  }
  const createTokenCopy = () => {
    setActionTargetCard(card);
    setOpenCreateTokenDialog(true);
  }

  let functions = [
    {name: "move", _function: handleMove},
    {name: "create trigger", _function: handleCreateTrigger},
    {name: "create delayed trigger", _function: handleCreateDelayedTrigger},
    {name: "create token copy", _function: createTokenCopy},
  ];
  switch (zoneName) {
    case "graveyard":
    case "exile":
      functions.push(
      {name: "set counter", _function: handleSetCounter},
      );
    case "sideboard":
      // graveyard and exile can reach here
      functions.push(
        {name: "set annotation", _function: handleSetAnnotation},
      );
      break;
  }

  useEffect(() => {
    if (card && card.name) {
      setShowString(card.name);
    }
    if (card && card.counters && card.counters.length) {
      let buffer = " (";
      card.counters.forEach((counter) => {
        buffer += `${counter.type}: ${counter.amount};`;
      });
      buffer += ")";
      setShowString((prev) => prev + buffer);
    }
    if (card && card.annotations && Object.keys(card.annotations).length) {
      let buffer = "";
      Object.keys(card.annotations).forEach((key) => {
        buffer += ` [${key}: ${card.annotations[key]}]`;
      });
      setShowString((prev) => prev + buffer);
    }
  }, [card, card?.counters, card?.annotations]);

  return (
    <Box onContextMenu={handleContextMenu}>
      <li className="card-list-item" style={{"listStyleType": "none"}}>
        {showString}
      </li>
      <CardContextMenu
        {...{contextMenu, setContextMenu}}
        functions={functions}
      />
    </Box>
  )
}

export default CardListItem;
