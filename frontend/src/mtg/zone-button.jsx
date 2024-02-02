import { useState } from 'react';
import Button from '@mui/material/Button';
import InspectDialog from './inspect-dialog';

function ZoneButton ({zoneName, buttonText, ownerName, content, setMoveTargetCard, setOpenMoveDialog, sx}) {
  const [open, setOpen] = useState(false);
  const handleClick = (e) => {
    setOpen(true);
  };
  return (
    <>
      <Button
        variant="contained"
        onClick={handleClick}
        sx={sx}
      >
        {buttonText + " " + content.length}
      </Button>
      <InspectDialog open={open} setOpen={setOpen} title={ownerName + "'s " + zoneName} content={content} setMoveTargetCard={setMoveTargetCard} setOpenMoveDialog={setOpenMoveDialog} />
    </>
  )
}

export default ZoneButton;
