import { useEffect, useState } from 'react';
import CardContextMenu from './card-context-menu';
import './card-list-item.css';

function CardListItem ({id, card, zoneName, setActionTargetCard, setOpenMoveDialog, setOpenCounterDialog, setOpenAnnotationDialog}) {
  const [contextMenu, setContextMenu] = useState(null);
  const [showString, setShowString] = useState(null);
  const handleContextMenu = (e) => {
    e.preventDefault();
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
  const functions =
    (zoneName === "graveyard" || zoneName === "exile") ?
    [
      {name: "move", _function: handleMove},
      {name: "set counter", _function: handleSetCounter},
      {name: "set annotation", _function: handleSetAnnotation},
    ] :
    [
      {name: "move", _function: handleMove},
    ];
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
    <>
      <li className="card-list-item" style={{"listStyleType": "none"}}
        onContextMenu={handleContextMenu}
      >
        {showString}
      </li>
      <CardContextMenu
        {...{contextMenu, setContextMenu}}
        functions={functions}
      />
    </>
  )
}

export default CardListItem;
