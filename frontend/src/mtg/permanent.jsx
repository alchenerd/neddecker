import { Card } from './card';
import Box from '@mui/material/Box';

function Permanent({id, name, imageUrl, backImageUrl, backgroundColor, setSelectedCard, typeLine, manaCost, counters, annotations, isFlipped, setActionTargetCard, setOpenMoveDialog, ...props}) {
  const handleMove = () => {
    setActionTargetCard({id: id, name: name});
    setOpenMoveDialog(true);
  };
  const addCounter = () => {
    setActionTargetCard({id: id, name: name});
    setOpenCounterDialog(true);
  };
  const permanentFunctions = [
    {name: "move", _function: handleMove},
    {name: "add counter", _function: addCounter},
  ];
  return (
      <Card {...{id, name, imageUrl, backImageUrl, backgroundColor, setSelectedCard, typeLine, manaCost, counters, annotations, isFlipped}} tappable={true} contextMenuFunctions={permanentFunctions} {...props} />
  );
}
export default Permanent;
