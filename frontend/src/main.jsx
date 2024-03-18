import React from 'react';
import ReactDOM from 'react-dom/client';
import { createBrowserRouter, RouterProvider, Navigate } from 'react-router-dom';
import IndexPage from './index';
import PlayPage from './PlayPage';
import './index.css';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { Provider as ReduxProvider } from 'react-redux';
import store from './store/store'

const router = createBrowserRouter([
  {
    path: '/',
    element: <IndexPage />,
  }, 
  {
    path: '/play/',
    element: (<PlayPage />) || (<Navigate to="/" replace />),
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);

ReactDOM.createRoot(document.getElementById('root')).render(
  //<React.StrictMode>
  <DndProvider backend={HTML5Backend}>
    <ReduxProvider store={store}>
      <RouterProvider router={router} />
    </ReduxProvider>
  </DndProvider>
  //</React.StrictMode>
)
