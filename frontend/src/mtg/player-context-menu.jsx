import Menu from '@mui/material/Menu';
import MenuItem from '@mui/material/MenuItem';

const PlayerContextMenu = ({ contextMenu, setContextMenu, functions }) => {
  const handleClose = () => {
    setContextMenu(null);
  }

  if (functions && functions.length) {
    return (
      <>
        <Menu
          open={contextMenu}
          onClose={handleClose}
          anchorReference="anchorPosition"
          anchorPosition={
            contextMenu ? { top: contextMenu.mouseY, left: contextMenu.mouseX } : undefined
          }
        >
          {
            functions.map((item) => {
              return (
                <MenuItem key={item.name} onClick={() => {handleClose(); item?._function();}}>
                  {item.name || "Undefined"}
                </MenuItem>
              )
            })
          }
        </Menu>
      </>
    );
  } else {
    return (<></>);
  }
}

export default PlayerContextMenu;
