import Box from '@mui/material/Box'

function PlayerInformation(props) {
  if (props.name) {
    let name, setName = useState(name);
  } else {
    let name = '';
  }
  return (
    <>
      <Box sx={{display: 'flex', width: '100%', height: '100%', background: "red"}}>
        <p>Player Information</p>
      </Box>
    </>
  );
}
export default PlayerInformation;
