import { Card } from './card';
import Box from '@mui/material/Box';

function Permanent({id, card, backgroundColor, setActionTargetCard, setOpenMoveDialog, setOpenCounterDialog, setOpenAnnotationDialog, setOpenCreateTriggerDialog, setOpenCreateDelayedTriggerDialog, ...props}) {
  const handleMove = () => {
    setActionTargetCard(card);
    setOpenMoveDialog(true);
  };
  const setCounter = () => {
    setActionTargetCard(card);
    setOpenCounterDialog(true);
  };
  const setAnnotation = () => {
    setActionTargetCard(card);
    setOpenAnnotationDialog(true);
  };
  const createTrigger = () => {
    setActionTargetCard(card);
    setOpenCreateTriggerDialog(true);
  }
  const createDelayedTrigger = () => {
    setActionTargetCard(card);
    console.log(setOpenCreateTriggerDialog);
    setOpenCreateDelayedTriggerDialog(true);
  }
  const permanentFunctions = [
    {name: "move", _function: handleMove},
    {name: "set counter", _function: setCounter},
    {name: "set annotation", _function: setAnnotation},
    {name: "create trigger", _function: createTrigger},
    {name: "create delayed trigger", _function: createDelayedTrigger},
  ];
  return (
      <Card card={card} tappable={true} contextMenuFunctions={permanentFunctions} {...props} />
  );
}
export default Permanent;
