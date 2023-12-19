import React, { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import Container from '@mui/material/Container'
import Grid from '@mui/material/Grid'
import Card from '@mui/material/Card'
import CardMedia from '@mui/material/CardMedia'
import CardContent from '@mui/material/CardContent'
import CardActionArea from '@mui/material/CardActionArea'
import Typography from '@mui/material/Typography'
import TextField from '@mui/material/TextField'
import Dialog from '@mui/material/Dialog'
import DialogActions from '@mui/material/DialogActions'
import DialogContent from '@mui/material/DialogContent'
import DialogContentText from '@mui/material/DialogContentText'
import DialogTitle from '@mui/material/DialogTitle'
import Button from '@mui/material/Button'
import './index.css'

function TopFiveMetaDecks() {
  const [open, setOpen] = useState(false);
  const [readonly, setReadonly] = useState(false);
  const [targetDeckName, setTargetDeckName] = useState('');
  const [targetDecklist, setTargetDecklist] = useState('');
  const [results, setResults] = useState([]);
  const [dialogErrorString, setDialogErrorString] = useState('');
  const textFieldRef = useRef('');
  const customDeck = {
    "name": "Custom Deck",
    "meta": "???",
    "decklist": "",
    "art": "https://cards.scryfall.io/large/front/b/d/bd07b50a-0bd7-49fa-9ada-96a8f96a62cc.jpg",
  };

  const handleClickOpen = (deck) => {
    setTargetDeckName(deck.name);
    if (deck.name === 'Custom Deck') {
      setReadonly(false);
    } else {
      setReadonly(true);
    }
    setTargetDecklist(deck.decklist.trim());
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
    setDialogErrorString('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const data = {
      decklist: textFieldRef.current.value,
    };

    try {
      const response = await axios.post('http://localhost:8000/api/play/', data);
      handleClose();
      sessionStorage.setItem('playData', JSON.stringify(response.data));
      window.location.href = 'play/';
    } catch (error) {
      if (error.response) {
        const statusCode = error.response.status;
        const errorMessage = error.response.data.message;
        switch (statusCode) {
          case 400:
            console.error('Server-side validation errors:', errorMessage);
            setDialogErrorString(errorMessage);
          default:
            console.error('HTTP error:', statusCode, errorMessage);
        }
      } else if (error.request) {
        console.error('Network error:', error.request);
      } else {
        console.error('Error:', error.message);
      }
    }
  };

  useEffect(() => {
    axios.get('http://localhost:8000/api/index/')
      .then(response => {
        setResults(response.data.results.concat(customDeck));
      })
      .catch(error => {
        console.log(error);
      });
  }, []);

  return (
    <Container>
      <Grid container spacing={2} sx={{ mt: 'auto', mb: 2 }} justifyContent='center' alignItems='center'>
        {results.map(deck => (
          <Grid item key={deck.name} xs={12} md={4}>
          <Card sx={{ minWidth: 350 }}>
            <CardActionArea onClick={() => handleClickOpen(deck)}>
              <CardMedia
                style={{ backgroundSize: '118%', backgroundPosition: '50% 26%', margin: 'auto' }}
                sx={{ height: 150 }}
                image={deck.art}
                title={deck.name}
              />
              <CardContent>
                <Typography gutterBottom variant="h5" component="div">
                  {deck.name}
                </Typography>
                <Typography variant="subtitle1" color="text.secondary">
                  Meta: {deck.meta}%
                </Typography>
              </CardContent>
            </CardActionArea>
          </Card>
          </Grid>
        ))}
      </Grid>
      <Dialog open={open} onClose={handleClose} scroll='paper'>
        <DialogTitle>
          Challenge Ned Decker with {targetDeckName}
        </DialogTitle>
        <DialogContent dividers={scroll === 'paper'}>
          <TextField
            autoFocus
            id="decklist"
            label="Decklist"
            fullWidth
            defaultValue={targetDecklist}
            variant="standard"
            multiline
            inputRef={textFieldRef}
            InputProps={{
              readOnly: readonly,
            }}
            helperText='Example: "4 Colossal Dreadmaw"'
          />
          <Typography variant="body2" color="red">
            {dialogErrorString}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button onClick={handleSubmit}>Play</Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default function IndexPage() {
  return (
    <>
      <Grid 
        container
        direction='column'
        alignItems='center'
        justifyContent='center'
        style={{
          minWidth: '100vw'
        }}
      >
        <Grid item xs={12}>
        </Grid>
        <Grid item xs={12}>
          <TopFiveMetaDecks />
        </Grid>
      </Grid>
    </>
  )
}
