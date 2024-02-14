import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import Button from '@mui/material/Button';
import CardListItem from './card-list-item';

function InspectDialog({open, setOpen, zoneName, title, content, setActionTargetCard, setOpenMoveDialog, setOpenCounterDialog}) {
  const handleClose = () => {setOpen(false);};
  return (
    <Dialog open={open} onClose={handleClose} fullWidth={true} maxWidth="sm">
      <DialogTitle>
        Inspect {title}
      </DialogTitle>
      <DialogContent>
        {
          content?.map((card) => (
            <CardListItem key={card.id} card={card} zoneName={zoneName} setActionTargetCard={setActionTargetCard} setOpenMoveDialog={setOpenMoveDialog} setOpenCounterDialog={setOpenCounterDialog}/>
          ))
        }
      </DialogContent>
      <DialogActions>
        <Button variant="contained" onClick={handleClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}

export default InspectDialog;
