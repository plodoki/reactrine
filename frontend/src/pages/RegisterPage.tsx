import { PersonAdd as PersonAddIcon } from '@mui/icons-material';
import {
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Container,
  Divider,
  Link as MuiLink,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import NavBar from '../components/NavBar';
import RegistrationDisabledMessage from '../components/RegistrationDisabledMessage';
import useAppStore from '../stores/useAppStore';

interface ApiError {
  response?: {
    data?: {
      detail?: string;
    };
  };
  message?: string;
}

const RegisterPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');

  const {
    register,
    isAuthenticated,
    isLoading,
    registrationAllowed,
    registrationMessage,
    checkRegistrationStatus,
  } = useAppStore();
  const navigate = useNavigate();

  // Check registration status on component mount
  useEffect(() => {
    checkRegistrationStatus();
  }, [checkRegistrationStatus]);

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  // Show disabled message if registration is not allowed
  if (!registrationAllowed) {
    return (
      <>
        <NavBar />
        <RegistrationDisabledMessage message={registrationMessage} />
      </>
    );
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    if (!/[A-Z]/.test(password)) {
      setError('Password must contain at least one uppercase letter');
      return;
    }

    if (!/[a-z]/.test(password)) {
      setError('Password must contain at least one lowercase letter');
      return;
    }

    if (!/\d/.test(password)) {
      setError('Password must contain at least one digit');
      return;
    }

    if (!/[!@#$%^&*(),.?":{}|<>]/.test(password)) {
      setError('Password must contain at least one special character');
      return;
    }

    try {
      await register(email, password);
      navigate('/', { replace: true });
    } catch (err: unknown) {
      const errorMessage =
        err instanceof Error
          ? err.message
          : (err as ApiError)?.response?.data?.detail || 'Registration failed';
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
                <PersonAddIcon />
              </Avatar>
              <Typography component="h1" variant="h5">
                Create account
              </Typography>
              <Typography variant="body2" color="textSecondary" align="center">
                Get started with your free account today.
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
                  />
                  <TextField
                    label="Password"
                    type="password"
                    fullWidth
                    required
                    value={password}
                    onChange={e => setPassword(e.target.value)}
                    helperText="At least 8 characters with uppercase, lowercase, digit, and special character"
                  />
                  <TextField
                    label="Confirm Password"
                    type="password"
                    fullWidth
                    required
                    value={confirmPassword}
                    onChange={e => setConfirmPassword(e.target.value)}
                  />
                  <Button
                    type="submit"
                    variant="contained"
                    fullWidth
                    disabled={isLoading}
                  >
                    {isLoading ? 'Creating account…' : 'Create account'}
                  </Button>
                </Stack>
              </Box>
              <Divider flexItem />
              <Typography variant="body2">
                Already have an account?{' '}
                <MuiLink component={Link} to="/login">
                  Sign in
                </MuiLink>
              </Typography>
            </Stack>
          </CardContent>
        </Card>
      </Container>
    </>
  );
};

export default RegisterPage;
