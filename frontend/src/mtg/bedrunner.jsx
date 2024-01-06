import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'

export function Bedrunner({whoseTurn, phase, ...props}) {
  const phaseMap = {
    "beginning phase": "Beginning Phase",
    "untap step": "Beginning Phase : Untap",
    "upkeep step": "Beginning Phase: Upkeep",
    "draw step": "Beginning Phase: Draw",
    "precombat main phase": "Precombat Main Phase",
    "combat phase": "Combat Phase",
    "beginning of combat step": "Combat Phase: Beginning of Combat",
    "declare attackers step": "Combat Phase: Declare Attackers",
    "declare blockers step": "Combat Phase: Declare Blockers",
    "combat damage step": "Combat Phase: Assign Combat Damage",
    "end of combat step": "Combat Phase: End of Combat",
    "postcombat main phase": "Postcombat Main Phase",
    "ending phase": "Ending Phase",
    "end step": "Ending Phase: End Step",
    "cleanup step": "Ending Phase: Cleanup",
  };

  return (
    <Typography variant="body2">
      {whoseTurn.toUpperCase() + ": " + phaseMap[phase] || "Unknown"}
    </Typography>
  );
}
