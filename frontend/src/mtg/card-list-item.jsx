import { useEffect, useState } from 'react';
import CardContextMenu from './card-context-menu';
function CardListItem ({string}) {
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
  return (
    <>
      <li style={{"listStyleType": "none"}} onContextMenu={handleContextMenu}>{string}</li>
      <CardContextMenu
        {...{contextMenu, setContextMenu}}
        functions={[
          {name: "move (not implemented)", _function: () => {console.log("move is not yet implemented!");}},
        ]}
      />
    </>
  )
}

export default CardListItem;
