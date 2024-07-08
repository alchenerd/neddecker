import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogTitle from '@mui/material/DialogTitle';
import Button from '@mui/material/Button';

function InspectGherkinDialog({open, setOpen, actionTargetCard}) {
  const handleClose = () => {setOpen(false);}
  return (
    <Dialog open={open} onClose={handleClose} fullWidth={true} maxWidth="sm" onContextMenu={e => {e.stopPropagation();}}>
      <DialogTitle>
        Inspect Gherkin Rules of {actionTargetCard?.name || 'Undefined'}
      </DialogTitle>
      <DialogContent>
        {
          actionTargetCard?.rules &&
          actionTargetCard.rules.map(rule => {return (
            <pre key={JSON.stringify(rule)}>{JSON.parse(JSON.stringify(rule))}</pre>
          )})
        }
      </DialogContent>
      <DialogActions>
        <Button variant="contained" onClick={handleClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}

export default InspectGherkinDialog;
