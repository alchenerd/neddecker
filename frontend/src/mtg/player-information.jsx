import { useState, useEffect } from 'react'
import Box from '@mui/material/Box'
import Typography from '@mui/material/Typography'

export function PlayerInformation({name, hasTurn, hasPriority, hp, infect, ...props}) {
  return (
    <>
      <Box sx={{display: 'flex', flexDirection: 'column', width: '100%', height: '100%', background: "red"}}>
        <Typography>{name}{hasTurn && "(*)"}</Typography>
        <Typography>HP: {hp}</Typography>
        <Typography>Infect: {infect}</Typography>
      </Box>
    </>
  );
}
