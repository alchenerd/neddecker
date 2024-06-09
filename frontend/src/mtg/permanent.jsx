import { Card } from './card';
import Box from '@mui/material/Box';

function Permanent({id, card, backgroundColor, setActionTargetCard, setOpenMoveDialog, setOpenCounterDialog, setOpenAnnotationDialog, setOpenCreateTriggerDialog, setOpenCreateDelayedTriggerDialog, setOpenCreateTokenDialog, setOpenInspectGherkinDialog, ...props}) {
  const handleMove = () => {
    setActionTargetCard(card);
    setOpenMoveDialog(true);
  };
  const setCounter = () => {
    setActionTargetCard(card);
    setOpenCounterDialog(true);
  };
  const setAnnotation = () => {
    setActionTargetCard(card);
    setOpenAnnotationDialog(true);
  };
  const createTrigger = () => {
    setActionTargetCard(card);
    setOpenCreateTriggerDialog(true);
  }
  const createDelayedTrigger = () => {
    setActionTargetCard(card);
    console.log(setOpenCreateTriggerDialog);
    setOpenCreateDelayedTriggerDialog(true);
  }
  const createTokenCopy = () => {
    setActionTargetCard(card);
    setOpenCreateTokenDialog(true);
  }
  const inspectGherkin = () => {
    setActionTargetCard(card);
    setOpenInspectGherkinDialog(true);
  }
  const permanentFunctions = [
    {name: "move", _function: handleMove},
    {name: "set counter", _function: setCounter},
    {name: "set annotation", _function: setAnnotation},
    {name: "create trigger", _function: createTrigger},
    {name: "create delayed trigger", _function: createDelayedTrigger},
    {name: "create token copy", _function: createTokenCopy},
    card?.rules? {name: "inspect gherkin", _function: inspectGherkin} : null,
  ].filter(x => x);
  return (
      <Card
        card={card}
        tappable={true}
        contextMenuFunctions={permanentFunctions}
        backgroundColor={card.in_game_id.startsWith("token") ? "white"
                                                             : props?.sx?.backgroundColor || "transparent"}
        {...props}
      />
  );
}
export default Permanent;
