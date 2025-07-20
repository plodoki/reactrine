import { LockOutlined as LockIcon } from '@mui/icons-material';
import {
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Link as MuiLink,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import NavBar from '../components/NavBar';
import useAppStore from '../stores/useAppStore';

interface ApiError {
  response?: {
    data?: {
      detail?: string;
    };
  };
  message?: string;
}

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const { login, isAuthenticated, isLoading, registrationAllowed } = useAppStore();
  const navigate = useNavigate();
  const location = useLocation();
  const from = location.state?.from?.pathname || '/';

  useEffect(() => {
    if (isAuthenticated) {
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, navigate, from]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : (err as ApiError)?.response?.data?.detail || 'Login failed';
      setError(errorMessage);
    }
  };

  return (
    <>
      <NavBar />
      <Container component="main" maxWidth="sm" sx={{ mt: 8 }}>
        <Card elevation={3}>
          <CardContent>
            <Stack spacing={3} alignItems="center">
              <Avatar sx={{ bgcolor: 'primary.main' }}>
                <LockIcon />
              </Avatar>
              <Typography component="h1" variant="h5">
                Sign in
              </Typography>
              {error && (
                <Typography color="error" variant="body2" align="center">
                  {error}
                </Typography>
              )}

              <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%' }}>
                <Stack spacing={2}>
                  <TextField
                    label="Email Address"
                    type="email"
                    fullWidth
                    required
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    autoComplete="email"
                  />
                  <TextField
                    label="Password"
                    type="password"
                    fullWidth
                    required
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    autoComplete="current-password"
                  />
                  <Button
                    type="submit"
                    variant="contained"
                    fullWidth
                    disabled={isLoading}
                  >
                    {isLoading ? 'Signing in…' : 'Sign in'}
                  </Button>
                </Stack>
              </Box>
              {registrationAllowed && (
                <Typography variant="body2">
                  Don&apos;t have an account?{' '}
                  <MuiLink component={Link} to="/register">
                    Sign up
                  </MuiLink>
                </Typography>
              )}
            </Stack>
          </CardContent>
        </Card>
      </Container>
    </>
  );
};

export default LoginPage;
