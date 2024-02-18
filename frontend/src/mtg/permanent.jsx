import { Card } from './card';
import Box from '@mui/material/Box';

function Permanent({id, card, backgroundColor, setSelectedCard, setActionTargetCard, setOpenMoveDialog, setOpenCounterDialog, setOpenAnnotationDialog, ...props}) {
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
  const permanentFunctions = [
    {name: "move", _function: handleMove},
    {name: "set counter", _function: setCounter},
    {name: "set annotation", _function: setAnnotation},
  ];
  return (
      <Card {...card} tappable={true} contextMenuFunctions={permanentFunctions} {...props} />
  );
}
export default Permanent;
