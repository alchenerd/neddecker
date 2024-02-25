import { configureStore } from "@reduxjs/toolkit";
import gameReducer from "./slice";

const store = configureStore({ reducer: {gameState: gameReducer} });

export default store;
