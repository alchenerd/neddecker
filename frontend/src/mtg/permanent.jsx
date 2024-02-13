import { Card } from './card';
import Box from '@mui/material/Box';

function Permanent({id, card, backgroundColor, setSelectedCard, setActionTargetCard, setOpenMoveDialog, setOpenCounterDialog, ...props}) {
  const handleMove = () => {
    setActionTargetCard(card);
    setOpenMoveDialog(true);
  };
  const addCounter = () => {
    setActionTargetCard(card);
    setOpenCounterDialog(true);
  };
  const permanentFunctions = [
    {name: "move", _function: handleMove},
    {name: "add counter", _function: addCounter},
  ];
  return (
      <Card {...card} tappable={true} contextMenuFunctions={permanentFunctions} {...props} />
  );
}
export default Permanent;
