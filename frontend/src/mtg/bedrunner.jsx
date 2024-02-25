import Paper from '@mui/material/Paper';
import Typography from '@mui/material/Typography';
import { useAffectedGameDataSelector } from './../store/slice';

export function Bedrunner() {
  const affectedGameData = useAffectedGameDataSelector();
  const whoseTurn = affectedGameData.whose_turn;
  const phase = affectedGameData.phase;
  const phaseMap = {
    "start of game phase": "Start of Game Phase",
    "beginning phase": "Beginning Phase",
    "untap step": "Beginning Phase : Untap",
    "upkeep step": "Beginning Phase: Upkeep",
    "draw step": "Beginning Phase: Draw",
    "precombat main phase": "Precombat Main Phase",
    "combat phase": "Combat Phase",
    "beginning of combat step": "Combat Phase: Beginning of Combat",
    "declare attackers step": "Combat Phase: Declare Attackers",
    "declare blockers step": "Combat Phase: Declare Blockers",
    "order blockers step": "Combat Phase: Order Damage Assignment on blockers",
    "order attackers step": "Combat Phase: Order Damage Assignment on Attackers",
    "first strike combat damage step": "Combat Phase: Assign First Strike Damage",
    "combat damage step": "Combat Phase: Assign Combat Damage",
    "end of combat step": "Combat Phase: End of Combat",
    "postcombat main phase": "Postcombat Main Phase",
    "ending phase": "Ending Phase",
    "end step": "Ending Phase: End Step",
    "cleanup step": "Ending Phase: Cleanup",
  };

  return (
    <Typography variant="body2">
      {(whoseTurn && phase) && whoseTurn.toUpperCase() + ": " + phaseMap[phase] || "Unknown"}
    </Typography>
  );
}
