import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { NotificationSnackbars } from '../Notifications';

describe('NotificationSnackbars', () => {
  const defaultProps = {
    showSuccess: false,
    showError: false,
    successMessage: '',
    errorMessage: '',
    onCloseSuccess: vi.fn(),
    onCloseError: vi.fn(),
  };

  it('should not render any snackbars when both are hidden', () => {
    render(<NotificationSnackbars {...defaultProps} />);
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it('should render success snackbar when showSuccess is true', () => {
    render(
      <NotificationSnackbars
        {...defaultProps}
        showSuccess={true}
        successMessage="Operation successful"
      />
    );

    expect(screen.getByText('Operation successful')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveClass('MuiAlert-standardSuccess');
  });

  it('should render error snackbar when showError is true', () => {
    render(
      <NotificationSnackbars
        {...defaultProps}
        showError={true}
        errorMessage="Something went wrong"
      />
    );

    expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveClass('MuiAlert-standardError');
  });

  it('should call onCloseSuccess when success alert is closed', async () => {
    const user = userEvent.setup();
    const onCloseSuccess = vi.fn();

    render(
      <NotificationSnackbars
        {...defaultProps}
        showSuccess={true}
        successMessage="Success"
        onCloseSuccess={onCloseSuccess}
      />
    );

    const closeButton = screen.getByLabelText('Close');
    await user.click(closeButton);

    expect(onCloseSuccess).toHaveBeenCalled();
  });

  it('should call onCloseError when error alert is closed', async () => {
    const user = userEvent.setup();
    const onCloseError = vi.fn();

    render(
      <NotificationSnackbars
        {...defaultProps}
        showError={true}
        errorMessage="Error"
        onCloseError={onCloseError}
      />
    );

    const closeButton = screen.getByLabelText('Close');
    await user.click(closeButton);

    expect(onCloseError).toHaveBeenCalled();
  });
});
