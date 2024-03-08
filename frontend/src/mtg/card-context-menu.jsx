import { useState } from 'react';
import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';
import Typography from '@mui/material/Typography';

function CardContextMenu({contextMenu, setContextMenu, functions, setActionTargetCard, setOpenMoveDialog}) {
  const handleClose = () => {
    setContextMenu(null);  
  }
  if (functions && functions.length) {
    return (
      <>
        <Menu
          open={contextMenu !== null}
          onClose={handleClose}
          anchorReference="anchorPosition"
          anchorPosition={
            contextMenu ? { top: contextMenu.mouseY, left: contextMenu.mouseX } : undefined
          }
        >
          {functions && functions.map((item) => {
            return (
              <MenuItem key={item.name} onClick={() => {handleClose(); item?._function();}}>
                {item.name || "Undefined"}
              </MenuItem>
            )
          })}
        </Menu>
      </>
    );
  } else {
    return (<></>);
  }
}

export default CardContextMenu;
