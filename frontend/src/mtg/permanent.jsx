import { Card } from './card';
import Box from '@mui/material/Box';

function Permanent({id, name, imageUrl, backImageUrl, backgroundColor, setSelectedCard, typeLine, manaCost, isFlipped, ...props}) {
  return (
      <Card {...{id, name, imageUrl, backImageUrl, backgroundColor, setSelectedCard, typeLine, manaCost, isFlipped}} tappable={true} {...props} />
  );
}
export default Permanent;
