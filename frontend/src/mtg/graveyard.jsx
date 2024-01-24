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
          margin:"20px",
          height: "40%"
        }}
        imageUrl={(content && content.length) ? content[content.length - 1].imageUrl : ""}
        setSelectedCard={setSelectedCard}
      />
    </>
  ); 
}
export default Graveyard;
