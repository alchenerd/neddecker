import { useEffect, useState } from 'react';
import { Card } from './card';
import InspectDialog from './inspect-dialog';

function Library({owner, ownerIndex, content, setDndMsg, setDblClkMsg, setSelectedCard, setWhoRequestShuffle, setActionTargetCard, setOpenMoveDialog}) {
  const [openInspectDialog, setOpenInspectDialog] = useState(false);

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

  const inspect = () => {
    console.log("Detected", owner.player_name, "insepecting their library");
    setOpenInspectDialog(true);
  };

  const libraryFunctions = [
    {name: "inspect", _function: inspect},
    {name: "shuffle", _function: shuffle},
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
      <InspectDialog
        open={openInspectDialog}
        setOpen={setOpenInspectDialog}
        zoneName="library"
        title={owner.player_name + "'s library"}
        content={content}
        setActionTargetCard={setActionTargetCard}
        setOpenMoveDialog={setOpenMoveDialog}
      />
    </>
  ); 
}
export default Library;
