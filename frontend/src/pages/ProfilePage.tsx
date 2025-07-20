import {
  AccountCircle as AccountCircleIcon,
  ArrowForward as ArrowForwardIcon,
  CalendarToday as CalendarIcon,
  Email as EmailIcon,
  Security as SecurityIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';
import {
  Avatar,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Container,
  Divider,
  Paper,
  Stack,
  Typography,
} from '@mui/material';
import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import useAppStore from '../stores/useAppStore';

const ProfilePage: React.FC = () => {
  const { user } = useAppStore();

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (!user) {
    return (
      <Container maxWidth="md" sx={{ mt: 4 }}>
        <Box
          display="flex"
          justifyContent="center"
          alignItems="center"
          minHeight="50vh"
        >
          <Typography variant="h6" color="text.secondary">
            Loading user information...
          </Typography>
        </Box>
      </Container>
    );
  }

  const getInitials = (email: string) => {
    return email.charAt(0).toUpperCase();
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Stack spacing={3}>
        {/* Profile Header */}
        <Card elevation={2}>
          <CardContent>
            <Stack direction="row" spacing={3} alignItems="center">
              <Avatar
                sx={{
                  width: 80,
                  height: 80,
                  bgcolor: 'primary.main',
                  fontSize: '2rem',
                }}
              >
                {getInitials(user.email)}
              </Avatar>
              <Box flex={1}>
                <Typography variant="h4" gutterBottom>
                  Profile
                </Typography>
                <Typography variant="body1" color="text.secondary">
                  Manage your account information and preferences
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>

        {/* Account Information */}
        <Card elevation={2}>
          <CardContent>
            <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
              Account Information
            </Typography>
            <Stack spacing={2}>
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: { xs: '1fr', sm: '1fr 1fr' },
                  gap: 2,
                }}
              >
                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Stack direction="row" spacing={2} alignItems="center">
                    <EmailIcon color="primary" />
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Email Address
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {user.email}
                      </Typography>
                    </Box>
                  </Stack>
                </Paper>

                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Stack direction="row" spacing={2} alignItems="center">
                    <AccountCircleIcon color="primary" />
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        User ID
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {user.id}
                      </Typography>
                    </Box>
                  </Stack>
                </Paper>

                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Stack direction="row" spacing={2} alignItems="center">
                    <SecurityIcon color="primary" />
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Authentication Provider
                      </Typography>
                      <Chip
                        label={user.auth_provider}
                        color="primary"
                        variant="outlined"
                        size="small"
                        sx={{ mt: 0.5 }}
                      />
                    </Box>
                  </Stack>
                </Paper>

                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Stack direction="row" spacing={2} alignItems="center">
                    <SecurityIcon color="success" />
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Account Status
                      </Typography>
                      <Chip
                        label={user.is_active ? 'Active' : 'Inactive'}
                        color={user.is_active ? 'success' : 'error'}
                        variant="outlined"
                        size="small"
                        sx={{ mt: 0.5 }}
                      />
                    </Box>
                  </Stack>
                </Paper>

                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Stack direction="row" spacing={2} alignItems="center">
                    <CalendarIcon color="primary" />
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Account Created
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {formatDate(user.created_at)}
                      </Typography>
                    </Box>
                  </Stack>
                </Paper>

                <Paper variant="outlined" sx={{ p: 2 }}>
                  <Stack direction="row" spacing={2} alignItems="center">
                    <CalendarIcon color="primary" />
                    <Box>
                      <Typography variant="subtitle2" color="text.secondary">
                        Last Updated
                      </Typography>
                      <Typography variant="body1" fontWeight="medium">
                        {formatDate(user.updated_at)}
                      </Typography>
                    </Box>
                  </Stack>
                </Paper>
              </Box>
            </Stack>
          </CardContent>
        </Card>

        {/* API Keys Management */}
        <Card elevation={2}>
          <CardContent>
            <Stack direction="row" spacing={2} alignItems="flex-start">
              <SecurityIcon color="primary" sx={{ mt: 0.5 }} />
              <Box flex={1}>
                <Typography variant="h6" gutterBottom>
                  API Keys
                </Typography>
                <Divider sx={{ my: 1 }} />
                <Typography variant="body2" color="text.secondary" mb={2}>
                  Manage your personal API keys for programmatic access to your account.
                  Create, view, and revoke API keys as needed.
                </Typography>
                <Button
                  component={RouterLink}
                  to="/settings/api-keys"
                  variant="outlined"
                  startIcon={<SecurityIcon />}
                  endIcon={<ArrowForwardIcon />}
                >
                  Manage API Keys
                </Button>
              </Box>
            </Stack>
          </CardContent>
        </Card>

        {/* Coming Soon Notice */}
        <Card elevation={2}>
          <CardContent>
            <Stack direction="row" spacing={2} alignItems="flex-start">
              <WarningIcon color="warning" sx={{ mt: 0.5 }} />
              <Box>
                <Typography variant="h6" gutterBottom>
                  Profile Features Coming Soon
                </Typography>
                <Divider sx={{ my: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Additional profile management features like password change, email
                  updates, and account deletion will be available in future updates.
                  Stay tuned for more personalization options!
                </Typography>
              </Box>
            </Stack>
          </CardContent>
        </Card>
      </Stack>
    </Container>
  );
};

export default ProfilePage;
