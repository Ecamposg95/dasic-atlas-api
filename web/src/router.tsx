import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Layout } from '@/components/layout/Layout';
import { LoginPage } from '@/features/auth/pages/LoginPage';
import { HelloPage } from '@/features/hello/pages/HelloPage';

export const router = createBrowserRouter([
  {
    path: '/spa',
    element: <Layout />,
    children: [
      { index: true, element: <Navigate to="/spa/hello" replace /> },
      { path: 'login', element: <LoginPage /> },
      { path: 'hello', element: <HelloPage /> },
    ],
  },
]);
