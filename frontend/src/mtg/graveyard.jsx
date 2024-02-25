import { useState, useEffect } from 'react';
import { Card } from './card';

function Graveyard({owner, setFocusedCard}) {
  const content = owner?.graveyard;
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
        card={content ? content[0] : null}
        setFocusedCard={(content && content.length) ? setFocusedCard : null}
      />
    </>
  ); 
}
export default Graveyard;
