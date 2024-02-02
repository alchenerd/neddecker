import { Card } from './card';
import Box from '@mui/material/Box';

function Permanent({id, name, imageUrl, backImageUrl, backgroundColor, setSelectedCard, typeLine, manaCost, isFlipped, setMoveTargetCard, setOpenMoveDialog, ...props}) {
  const handleMove = () => {
    setMoveTargetCard({id: id, name: name});
    setOpenMoveDialog(true);
  };
  const permanentFunctions = [
    {name: "move", _function: handleMove},
  ];
  return (
      <Card {...{id, name, imageUrl, backImageUrl, backgroundColor, setSelectedCard, typeLine, manaCost, isFlipped}} tappable={true} contextMenuFunctions={permanentFunctions} {...props} />
  );
}
export default Permanent;
