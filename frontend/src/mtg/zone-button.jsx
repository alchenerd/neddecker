import { useState } from 'react';
import Button from '@mui/material/Button';
import InspectDialog from './inspect-dialog';

function ZoneButton ({zoneName, buttonText, ownerName, content, setActionTargetCard, setOpenMoveDialog, setOpenCounterDialog, setOpenAnnotationDialog, setOpenCreateTriggerDialog, sx}) {
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
        {buttonText + " " + (content?.length || 0)}
      </Button>
      <InspectDialog
        open={open}
        setOpen={setOpen}
        title={ownerName + "'s " + zoneName}
        zoneName={zoneName}
        content={content}
        setActionTargetCard={setActionTargetCard}
        setOpenMoveDialog={setOpenMoveDialog}
        setOpenCounterDialog={setOpenCounterDialog}
        setOpenAnnotationDialog={setOpenAnnotationDialog}
        setOpenCreateTriggerDialog={setOpenCreateTriggerDialog}
      />
    </>
  )
}

export default ZoneButton;
