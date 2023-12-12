import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Container from '@mui/material/Container';
import Grid from '@mui/material/Grid';
import Card from '@mui/material/Card';
import CardMedia from '@mui/material/CardMedia';
import CardContent from '@mui/material/CardContent';
import CardActionArea from '@mui/material/CardActionArea';
import Typography from '@mui/material/Typography';
import './index.css';

function TopFiveMetaDecks() {
  const [results, setResults] = useState([]);
  const customDeck = {
    "name": "Custom Deck",
    "meta": "???",
    "decklist": "",
    "art": "https://cards.scryfall.io/large/front/b/d/bd07b50a-0bd7-49fa-9ada-96a8f96a62cc.jpg",
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
            <CardActionArea>
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
    </Container>
  );
};

export default TopFiveMetaDecks
