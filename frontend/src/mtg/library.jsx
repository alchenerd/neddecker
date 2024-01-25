import { useEffect } from 'react';
import { Card } from './card';

function Library({owner, ownerIndex, content, setDndMsg, setDblClkMsg, setSelectedCard, setWhoRequestShuffle}) {
  const drawFromTop = (e) => {
    console.log("Detected", owner.player_name, "drawing from their library");
    setDblClkMsg(
      {
        id: null,
        type: "drawFromLibrary",
        who: owner.player_name,
      }
    );
  }

  const shuffle = () => {
    console.log("Detected", owner.player_name, "shuffling their library");
    setWhoRequestShuffle(owner.player_name);
  };

  const libraryFunctions = [
    {name: "shuffle", _function: shuffle}
  ];

  return (
    <>
      <Card
        canDrag="false"
        sx={{
          position: "absolute",
          top: 0,
          right: 0,
          margin:"20px",
          height: "40%"
        }}
        backgroundColor={(content && content.length) ? "#c0ffee" : null}
        onDoubleClick={drawFromTop}
        contextMenuFunctions={libraryFunctions}
      />
    </>
  ); 
}
export default Library;
