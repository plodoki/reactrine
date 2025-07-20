import { useState } from 'react';
import {
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Typography,
  Tooltip,
} from '@mui/material';
import {
  Delete as DeleteIcon,
  Block as BlockIcon,
  CheckCircle as EnableIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNotifications } from '../../hooks/useNotifications';
import { adminService } from './services/adminService';
import type { UserWithRole, UserRoleUpdate } from '../../lib/api-client';
import { useAppStore } from '../../stores/useAppStore';

export default function AdminUsersPage() {
  const [searchEmail, setSearchEmail] = useState('');
  const [selectedUser, setSelectedUser] = useState<UserWithRole | null>(null);
  const [selectedRole, setSelectedRole] = useState('');
  const [isRoleDialogOpen, setIsRoleDialogOpen] = useState(false);
  const [deleteConfirmDialog, setDeleteConfirmDialog] = useState<{
    open: boolean;
    user: UserWithRole | null;
  }>({ open: false, user: null });

  const { user: currentUser } = useAppStore();
  const { showSuccessNotification, showErrorNotification } = useNotifications();
  const queryClient = useQueryClient();

  // Fetch users
  const { data: userList } = useQuery({
    queryKey: ['admin', 'users', { email: searchEmail }],
    queryFn: () => adminService.getUsers({ email: searchEmail || undefined }),
  });

  // Fetch roles
  const { data: roleList } = useQuery({
    queryKey: ['admin', 'roles'],
    queryFn: () => adminService.getRoles(),
  });

  // Update user role mutation
  const updateRoleMutation = useMutation({
    mutationFn: ({
      userId,
      roleUpdate,
    }: {
      userId: number;
      roleUpdate: UserRoleUpdate;
    }) => adminService.updateUserRole(userId, roleUpdate),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      showSuccessNotification('User role updated successfully');
      setIsRoleDialogOpen(false);
      setSelectedUser(null);
    },
    onError: (error: Error) => {
      showErrorNotification(error, 'Failed to update user role');
    },
  });

  // Update user status mutation
  const updateStatusMutation = useMutation({
    mutationFn: ({ userId, isActive }: { userId: number; isActive: boolean }) =>
      adminService.updateUserStatus(userId, isActive),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      showSuccessNotification('User status updated successfully');
      setDeleteConfirmDialog({ open: false, user: null });
    },
    onError: (error: Error) => {
      showErrorNotification(error, 'Failed to update user status');
    },
  });

  // Delete user mutation
  const deleteUserMutation = useMutation({
    mutationFn: (userId: number) => adminService.deleteUser(userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'users'] });
      showSuccessNotification('User deleted successfully');
      setDeleteConfirmDialog({ open: false, user: null });
    },
    onError: (error: Error) => {
      showErrorNotification(error, 'Failed to delete user');
    },
  });

  const handleRoleChange = () => {
    if (selectedUser && selectedRole) {
      updateRoleMutation.mutate({
        userId: selectedUser.id,
        roleUpdate: { role_name: selectedRole },
      });
    }
  };

  const handleStatusChange = (isActive: boolean) => {
    if (selectedUser) {
      updateStatusMutation.mutate({
        userId: selectedUser.id,
        isActive: isActive,
      });
    }
  };

  const handleDeleteConfirm = () => {
    if (selectedUser) {
      deleteUserMutation.mutate(selectedUser.id);
    }
  };

  const openRoleDialog = (user: UserWithRole) => {
    setSelectedUser(user);
    setSelectedRole(user.role?.name || '');
    setIsRoleDialogOpen(true);
  };

  const openDeleteConfirmDialog = (user: UserWithRole) => {
    setSelectedUser(user);
    setDeleteConfirmDialog({ open: true, user: user });
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        User Management
      </Typography>

      {/* Search */}
      <Box sx={{ mb: 3 }}>
        <TextField
          label="Search by email"
          value={searchEmail}
          onChange={e => setSearchEmail(e.target.value)}
          sx={{ minWidth: 300 }}
        />
      </Box>

      {/* Users Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Email</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Provider</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {userList?.users.map(user => (
              <TableRow key={user.id}>
                <TableCell>{user.email}</TableCell>
                <TableCell>
                  <Chip
                    label={user.role?.name || 'No Role'}
                    color={user.role?.name === 'admin' ? 'secondary' : 'default'}
                    size="small"
                  />
                </TableCell>
                <TableCell>{user.auth_provider}</TableCell>
                <TableCell>
                  <Chip
                    label={user.is_active ? 'Active' : 'Inactive'}
                    color={user.is_active ? 'success' : 'error'}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                    <Button
                      size="small"
                      onClick={() => openRoleDialog(user)}
                      disabled={updateRoleMutation.isPending}
                    >
                      Change Role
                    </Button>

                    {/* Status Toggle */}
                    <Tooltip title={user.is_active ? 'Disable User' : 'Enable User'}>
                      <span>
                        <IconButton
                          size="small"
                          onClick={() => {
                            setSelectedUser(user);
                            handleStatusChange(!user.is_active);
                          }}
                          disabled={
                            user.id === currentUser?.id ||
                            updateStatusMutation.isPending
                          }
                          color={user.is_active ? 'warning' : 'success'}
                        >
                          {user.is_active ? <BlockIcon /> : <EnableIcon />}
                        </IconButton>
                      </span>
                    </Tooltip>

                    {/* Delete Button */}
                    <Tooltip title="Delete User">
                      <span>
                        <IconButton
                          size="small"
                          onClick={() => openDeleteConfirmDialog(user)}
                          disabled={
                            user.id === currentUser?.id || deleteUserMutation.isPending
                          }
                          color="error"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </span>
                    </Tooltip>
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Role Change Dialog */}
      <Dialog open={isRoleDialogOpen} onClose={() => setIsRoleDialogOpen(false)}>
        <DialogTitle>Change User Role</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <Typography variant="body2" gutterBottom>
              User: {selectedUser?.email}
            </Typography>
            <Typography variant="body2" gutterBottom>
              Current Role: {selectedUser?.role?.name || 'No Role'}
            </Typography>

            <FormControl fullWidth sx={{ mt: 2 }}>
              <InputLabel>New Role</InputLabel>
              <Select
                value={selectedRole}
                onChange={e => setSelectedRole(e.target.value)}
                label="New Role"
              >
                {roleList?.roles.map(role => (
                  <MenuItem key={role.id} value={role.name}>
                    {role.name} - {role.description}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setIsRoleDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleRoleChange}
            disabled={updateRoleMutation.isPending || !selectedRole}
            variant="contained"
          >
            Update Role
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteConfirmDialog.open}
        onClose={() => setDeleteConfirmDialog({ open: false, user: null })}
        aria-labelledby="delete-dialog-title"
        aria-describedby="delete-dialog-description"
      >
        <DialogTitle id="delete-dialog-title">Confirm Deletion</DialogTitle>
        <DialogContent>
          <Typography id="delete-dialog-description">
            Are you sure you want to delete user "{deleteConfirmDialog.user?.email}"?
            This action cannot be undone.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmDialog({ open: false, user: null })}>
            Cancel
          </Button>
          <Button
            onClick={handleDeleteConfirm}
            color="error"
            variant="contained"
            startIcon={<DeleteIcon />}
          >
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
