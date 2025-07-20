import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import LoginIcon from '@mui/icons-material/Login';
import LogoutIcon from '@mui/icons-material/Logout';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import SecurityIcon from '@mui/icons-material/Security';
import SettingsIcon from '@mui/icons-material/Settings';
import {
  AppBar,
  Box,
  Button,
  Divider,
  IconButton,
  Menu,
  MenuItem,
  Toolbar,
  Typography,
} from '@mui/material';
import { useState } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import useAppStore from '../stores/useAppStore';
import ThemeToggle from './ThemeToggle';

const NavBar = () => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);
  const navigate = useNavigate();

  const { isAuthenticated, user, logout, registrationAllowed } = useAppStore();
  const isAdmin = user?.role?.name === 'admin';

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/');
    } catch (error) {
      console.error('Logout failed:', error);
    }
    handleClose();
  };

  return (
    <AppBar position="static">
      <Toolbar>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          FastStack
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <Button color="inherit" component={RouterLink} to="/">
            Home
          </Button>
          <Button color="inherit" component={RouterLink} to="/haiku">
            Haiku Generator
          </Button>
          <Button color="inherit" component={RouterLink} to="/components">
            Components
          </Button>

          {/* Admin-only navigation items */}
          {isAuthenticated && isAdmin && (
            <Button
              color="inherit"
              component={RouterLink}
              to="/admin/users"
              sx={{ textTransform: 'none' }}
            >
              User Management
            </Button>
          )}

          {/* Theme Toggle */}
          <ThemeToggle />

          {/* Authentication-dependent navigation */}
          {isAuthenticated ? (
            <>
              <IconButton
                size="large"
                aria-label="user menu"
                aria-controls="user-menu-appbar"
                aria-haspopup="true"
                onClick={handleMenu}
                color="inherit"
              >
                <AccountCircleIcon />
              </IconButton>
              <Menu
                id="user-menu-appbar"
                anchorEl={anchorEl}
                anchorOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                keepMounted
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                open={open}
                onClose={handleClose}
              >
                <MenuItem disabled>
                  <Typography variant="body2" color="text.secondary">
                    {user?.email}
                  </Typography>
                </MenuItem>
                <Divider />
                <MenuItem component={RouterLink} to="/profile" onClick={handleClose}>
                  <AccountCircleIcon sx={{ mr: 1 }} />
                  Profile
                </MenuItem>

                {/* LLM Settings - Admin only */}
                {isAdmin && (
                  <MenuItem
                    component={RouterLink}
                    to="/settings/llm"
                    onClick={handleClose}
                  >
                    <SettingsIcon sx={{ mr: 1 }} />
                    LLM Settings
                  </MenuItem>
                )}

                {/* Admin Panel - Admin only */}
                {isAdmin && (
                  <MenuItem
                    component={RouterLink}
                    to="/admin/users"
                    onClick={handleClose}
                  >
                    <AdminPanelSettingsIcon sx={{ mr: 1 }} />
                    User Management
                  </MenuItem>
                )}

                <MenuItem
                  component={RouterLink}
                  to="/settings/api-keys"
                  onClick={handleClose}
                >
                  <SecurityIcon sx={{ mr: 1 }} />
                  API Keys
                </MenuItem>
                <Divider />
                <MenuItem onClick={handleLogout}>
                  <LogoutIcon sx={{ mr: 1 }} />
                  Sign Out
                </MenuItem>
              </Menu>
            </>
          ) : (
            <>
              <Button
                color="inherit"
                component={RouterLink}
                to="/login"
                startIcon={<LoginIcon />}
              >
                Sign In
              </Button>
              {registrationAllowed && (
                <Button
                  color="inherit"
                  component={RouterLink}
                  to="/register"
                  startIcon={<PersonAddIcon />}
                >
                  Sign Up
                </Button>
              )}
            </>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default NavBar;
