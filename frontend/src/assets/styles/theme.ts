import { PaletteMode } from '@mui/material';
import { createTheme, ThemeOptions } from '@mui/material/styles';

const getDesignTokens = (mode: PaletteMode): ThemeOptions => ({
  palette: {
    mode,
    ...(mode === 'light'
      ? {
          // Light mode palette
          primary: {
            main: '#0D47A1', // Darker blue for better contrast
            light: '#4db6ac',
            dark: '#00796b',
          },
          secondary: {
            main: '#ad1457', // Darker pink for better contrast
            light: '#ffb74d',
            dark: '#f57c00',
          },
          background: {
            default: '#fafafa',
            paper: '#ffffff',
          },
          text: {
            primary: '#263238',
            secondary: '#546e7a',
          },
        }
      : {
          // Dark mode palette
          primary: {
            main: '#4db6ac', // Lighter Teal
            light: '#80cbc4',
            dark: '#26a69a',
          },
          secondary: {
            main: '#ffb74d', // Lighter Orange
            light: '#ffd54f',
            dark: '#ffa726',
          },
          background: {
            default: '#1c252c',
            paper: '#25313a',
          },
          text: {
            primary: '#e0e0e0',
            secondary: '#b0bec5',
          },
        }),
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontWeight: 300,
      fontSize: '6rem',
      lineHeight: 1.167,
    },
    h2: {
      fontWeight: 300,
      fontSize: '3.75rem',
      lineHeight: 1.2,
    },
    h3: {
      fontWeight: 400,
      fontSize: '3rem',
      lineHeight: 1.167,
    },
    h4: {
      fontWeight: 400,
      fontSize: '2.125rem',
      lineHeight: 1.235,
    },
    h5: {
      fontWeight: 400,
      fontSize: '1.5rem',
      lineHeight: 1.334,
    },
    h6: {
      fontWeight: 500,
      fontSize: '1.25rem',
      lineHeight: 1.6,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
          textTransform: 'none',
          fontWeight: 500,
        },
        colorInherit: {
          '&:hover': {
            backgroundColor:
              mode === 'dark' ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.04)',
            color: mode === 'dark' ? '#ffb74d' : '#f57c00',
          },
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          borderRadius: 12,
          boxShadow:
            mode === 'light'
              ? '0px 2px 8px rgba(0, 0, 0, 0.1)'
              : '0px 2px 8px rgba(0, 0, 0, 0.3)',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            borderRadius: 8,
          },
        },
      },
    },
  },
});

export const createAppTheme = (mode: PaletteMode) => createTheme(getDesignTokens(mode));

// Default light theme for backwards compatibility
export default createAppTheme('light');
