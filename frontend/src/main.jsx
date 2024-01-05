import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import IndexPage from './index'
import PlayPage from './PlayPage'
import './index.css'
import { DndProvider } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'

const router = createBrowserRouter([
  {
    path: '/',
    element: <IndexPage />,
  }, 
  {
    path: '/play/',
    element: <PlayPage />,
  }
]);

ReactDOM.createRoot(document.getElementById('root')).render(
  //<React.StrictMode>
  <DndProvider backend={HTML5Backend}>
    <RouterProvider router={router} />
  </DndProvider>
  //</React.StrictMode>
)
