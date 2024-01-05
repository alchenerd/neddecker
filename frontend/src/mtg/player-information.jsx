import { useState, useEffect } from 'react'
import Box from '@mui/material/Box'

export function PlayerInformation({name, hasTurn, hasPriority, hp, infect, ...props}) {
  return (
    <>
      <Box sx={{display: 'flex', flexDirection: 'column', width: '100%', height: '100%', background: "red"}}>
        <p>{name}{hasTurn && "(*)"}</p>
        <p>HP: {hp}</p>
        <p>Infect: {infect}</p>
      </Box>
    </>
  );
}
