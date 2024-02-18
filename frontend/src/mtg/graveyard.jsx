import { useState, useEffect } from 'react';
import { Card } from './card';

function Graveyard({owner, content, setSelectedCard}) {
  return (
    <>
      <Card
        id="graveyardShowCard"
        canDrag="false"
        sx={{
          position: "absolute",
          bottom: 0,
          right: 0,
          height: "100%"
        }}
        imageUrl={(content && content.length) ? content[content.length - 1].imageUrl : ""}
        setSelectedCard={(content && content.length) ? setSelectedCard : null}
      />
    </>
  ); 
}
export default Graveyard;
