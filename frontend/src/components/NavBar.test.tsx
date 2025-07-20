import { createAppTheme } from '@/assets/styles/theme';
import { ThemeModeProvider, useThemeMode } from '@/contexts/ThemeContext';
import { ThemeProvider } from '@mui/material/styles';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import NavBar from './NavBar';

// Inner component that uses the theme context
const ThemedWrapper = ({ children }: { children: React.ReactNode }) => {
  const { mode } = useThemeMode();
  const theme = createAppTheme(mode);

  return <ThemeProvider theme={theme}>{children}</ThemeProvider>;
};

// Test wrapper component
const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <BrowserRouter
    future={{
      v7_startTransition: true,
      v7_relativeSplatPath: true,
    }}
  >
    <ThemeModeProvider>
      <ThemedWrapper>{children}</ThemedWrapper>
    </ThemeModeProvider>
  </BrowserRouter>
);

describe('NavBar', () => {
  it('renders the application title', () => {
    render(
      <TestWrapper>
        <NavBar />
      </TestWrapper>
    );

    expect(screen.getByText('FastStack')).toBeInTheDocument();
  });

  it('renders navigation links', () => {
    render(
      <TestWrapper>
        <NavBar />
      </TestWrapper>
    );

    expect(screen.getByText('Home')).toBeInTheDocument();
    expect(screen.getByText('Haiku Generator')).toBeInTheDocument();
  });

  it('has correct link attributes', () => {
    render(
      <TestWrapper>
        <NavBar />
      </TestWrapper>
    );

    const homeLink = screen.getByText('Home').closest('a');
    const haikuLink = screen.getByText('Haiku Generator').closest('a');

    expect(homeLink).toHaveAttribute('href', '/');
    expect(haikuLink).toHaveAttribute('href', '/haiku');
  });
});
