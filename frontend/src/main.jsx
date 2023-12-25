import React from 'react'
import ReactDOM from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import IndexPage from './index'
import PlayPage from './PlayPage'
import './index.css'

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
    <RouterProvider router={router} />
  //</React.StrictMode>
)
