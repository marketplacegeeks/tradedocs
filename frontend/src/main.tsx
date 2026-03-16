import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ConfigProvider } from 'antd'
import { AuthProvider } from './store/AuthContext'
import './index.css'
import App from './App.tsx'

const queryClient = new QueryClient()

// Map design system tokens onto Ant Design's theme system.
const antTheme = {
  token: {
    colorPrimary: '#4F6EF7',
    colorPrimaryHover: '#3A58E0',
    borderRadius: 8,
    borderRadiusLG: 14,
    fontFamily: "'DM Sans', sans-serif",
    colorBgContainer: '#FFFFFF',
    colorBgLayout: '#F4F5F7',
    colorBorder: '#D8DCE6',
    colorBorderSecondary: '#ECEEF2',
    colorText: '#1A1D23',
    colorTextSecondary: '#5A6070',
    colorTextTertiary: '#9BA3B5',
    boxShadow: '0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04)',
    colorBgElevated: '#FFFFFF',
  },
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <ConfigProvider theme={antTheme}>
          <AuthProvider>
            <App />
          </AuthProvider>
        </ConfigProvider>
      </QueryClientProvider>
    </BrowserRouter>
  </StrictMode>,
)
