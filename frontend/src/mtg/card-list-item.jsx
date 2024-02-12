import { useEffect, useState } from 'react';
import CardContextMenu from './card-context-menu';
import './card-list-item.css';

function CardListItem ({id, string, setActionTargetCard, setOpenMoveDialog}) {
  const [contextMenu, setContextMenu] = useState(null);
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
    setActionTargetCard({id: id, name: string});
    setOpenMoveDialog(true);
  };
  return (
    <>
      <li className="card-list-item" style={{"listStyleType": "none"}} onContextMenu={handleContextMenu}>{string}</li>
      <CardContextMenu
        {...{contextMenu, setContextMenu}}
        functions={[
          {name: "move", _function: handleMove},
        ]}
      />
    </>
  )
}

export default CardListItem;
