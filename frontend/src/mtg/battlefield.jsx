import Box from '@mui/material/Box'
import { DndProvider, useDrop } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import { ItemTypes } from './constants'
import { Card } from './card'

function Battlefield(props) {
  const [, drop] = useDrop(
    () => ({
      accept: ItemTypes.MTG_CARD,
      drop: (item) => {
        console.log(item);
      },
    }), []
  );
  return (
    <>
      <Box sx={{display: "flex", width: "100%", height: "100%", background: "blue"}} ref={drop}>
        <p>Battlefield</p>
      </Box>
    </>
  )
}
export default Battlefield;
