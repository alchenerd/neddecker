import { Card } from './card';
import Box from '@mui/material/Box';

function Permanent({id, card, backgroundColor, setFocusedCard, setActionTargetCard, setOpenMoveDialog, setOpenCounterDialog, setOpenAnnotationDialog, setOpenCreateTriggerDialog, ...props}) {
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
  const permanentFunctions = [
    {name: "move", _function: handleMove},
    {name: "set counter", _function: setCounter},
    {name: "set annotation", _function: setAnnotation},
    {name: "create trigger", _function: createTrigger},
  ];
  return (
      <Card card={card} tappable={true} contextMenuFunctions={permanentFunctions} {...props} />
  );
}
export default Permanent;
