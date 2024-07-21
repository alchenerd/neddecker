import { useState } from 'react';
import Button from '@mui/material/Button';
import InspectDialog from './inspect-dialog';

function ZoneButton ({zoneName, buttonText, owner, content, setActionTargetCard, setOpenMoveDialog, setOpenCounterDialog, setOpenAnnotationDialog, setOpenCreateTriggerDialog, setOpenCreateDelayedTriggerDialog, setOpenCreateTokenDialog, setTargetIsCopy, sx}) {
  const ownerName = owner?.player_name;
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
        onContextMenu={(e) => {e.stopPropagation();}}
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
        setOpenCreateDelayedTriggerDialog={setOpenCreateDelayedTriggerDialog}
        setOpenCreateTokenDialog={setOpenCreateTokenDialog}
        setTargetIsCopy={setTargetIsCopy}
      />
    </>
  )
}

export default ZoneButton;
