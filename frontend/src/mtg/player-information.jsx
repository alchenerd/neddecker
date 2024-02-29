import { useState, useEffect } from 'react';
import Box from '@mui/material/Box';
import Typography from '@mui/material/Typography';
import { useAffectedGameDataSelector } from './../store/slice';

export function PlayerInformation({ownerName, fullName}) {
  const affectedGameData = useAffectedGameDataSelector();
  const hasTurn = affectedGameData?.whose_turn === ownerName;
  const owner = affectedGameData?.board_state?.players.find((player) => player.player_name === ownerName);
  const hp = owner?.hp;
  const infect = owner?.infect;
  return (
    <>
      <Box sx={{display: 'flex', flexDirection: 'column', width: '100%', height: '100%', background: "red"}}>
        <Typography>{fullName}{hasTurn && "(*)"}</Typography>
        <Typography>HP: {hp}</Typography>
        <Typography>Infect: {infect}</Typography>
      </Box>
    </>
  );
}
