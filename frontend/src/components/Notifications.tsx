import { Alert, Snackbar } from '@mui/material';

interface NotificationSnackbarsProps {
  showSuccess: boolean;
  showError: boolean;
  successMessage: string;
  errorMessage: string;
  onCloseSuccess: () => void;
  onCloseError: () => void;
}

export const NotificationSnackbars = ({
  showSuccess,
  showError,
  successMessage,
  errorMessage,
  onCloseSuccess,
  onCloseError,
}: NotificationSnackbarsProps) => {
  return (
    <>
      <Snackbar
        open={showSuccess}
        autoHideDuration={4000}
        onClose={onCloseSuccess}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={onCloseSuccess} severity="success" sx={{ width: '100%' }}>
          {successMessage}
        </Alert>
      </Snackbar>

      <Snackbar
        open={showError}
        autoHideDuration={6000}
        onClose={onCloseError}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={onCloseError} severity="error" sx={{ width: '100%' }}>
          {errorMessage}
        </Alert>
      </Snackbar>
    </>
  );
};
