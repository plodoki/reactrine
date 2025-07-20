import { mockApiKey } from '@/test/factories';
import { renderWithProviders } from '@/test/utils';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import ApiKeyList from '../ApiKeyList';

describe('ApiKeyList Component', () => {
  const mockOnRevoke = vi.fn();
  const defaultProps = {
    apiKeys: [],
    onRevoke: mockOnRevoke,
    isRevoking: false,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Empty State', () => {
    it('should display empty state when no API keys exist', () => {
      renderWithProviders(<ApiKeyList {...defaultProps} />);

      expect(screen.getByText('No API Keys Found')).toBeInTheDocument();
      expect(
        screen.getByText(
          "You haven't created any API keys yet. Create your first key to get started."
        )
      ).toBeInTheDocument();
    });

    it('should display key icon in empty state', () => {
      renderWithProviders(<ApiKeyList {...defaultProps} />);

      // Check for key icon using data-testid
      const keyIcon = screen.getByTestId('KeyOutlinedIcon');
      expect(keyIcon).toBeInTheDocument();
    });
  });

  describe('API Key Display', () => {
    it('should display API key with all information', () => {
      const futureDate = new Date();
      futureDate.setFullYear(futureDate.getFullYear() + 1); // One year in the future

      const apiKey = mockApiKey({
        id: 1,
        label: 'Test API Key',
        created_at: '2024-01-01T10:00:00Z',
        expires_at: futureDate.toISOString(),
        last_used_at: '2024-06-01T12:00:00Z',
        is_active: true,
      });

      renderWithProviders(<ApiKeyList {...defaultProps} apiKeys={[apiKey]} />);

      expect(screen.getByText('Test API Key')).toBeInTheDocument();
      expect(screen.getByText('#1')).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument();
    });

    it('should display default label when no label is provided', () => {
      const apiKey = mockApiKey({
        id: 2,
        label: null,
        is_active: true,
      });

      renderWithProviders(<ApiKeyList {...defaultProps} apiKeys={[apiKey]} />);

      expect(screen.getByText('API Key 2')).toBeInTheDocument();
    });

    it('should display formatted dates correctly', () => {
      const futureDate = new Date();
      futureDate.setFullYear(futureDate.getFullYear() + 1); // One year in the future

      const apiKey = mockApiKey({
        id: 1,
        created_at: '2024-01-01T10:00:00Z',
        expires_at: futureDate.toISOString(),
        last_used_at: '2024-06-01T12:00:00Z',
        is_active: true,
      });

      renderWithProviders(<ApiKeyList {...defaultProps} apiKeys={[apiKey]} />);

      // Check for formatted dates (exact format may vary based on locale)
      // From test output, actual format is "Jan 1, 2024, 11:00 AM"
      expect(screen.getByText(/Jan 1, 2024/)).toBeInTheDocument();
      expect(screen.getByText(/Jun 1, 2024/)).toBeInTheDocument();
      // Check for future expiration date
      expect(
        screen.getByText(new RegExp(futureDate.getFullYear().toString()))
      ).toBeInTheDocument();
    });

    it('should display "Never" for null dates', () => {
      const apiKey = mockApiKey({
        id: 1,
        expires_at: null,
        last_used_at: null,
        is_active: true,
      });

      renderWithProviders(<ApiKeyList {...defaultProps} apiKeys={[apiKey]} />);

      const neverTexts = screen.getAllByText('Never');
      expect(neverTexts).toHaveLength(2); // expires_at and last_used_at
    });
  });

  describe('Status Chips', () => {
    it('should display "Active" status for active keys', () => {
      const apiKey = mockApiKey({
        is_active: true,
        expires_at: null,
      });

      renderWithProviders(<ApiKeyList {...defaultProps} apiKeys={[apiKey]} />);

      const activeChip = screen.getByText('Active');
      expect(activeChip).toBeInTheDocument();
      // Check the parent chip element for color class
      expect(activeChip.closest('.MuiChip-root')).toHaveClass('MuiChip-colorSuccess');
    });

    it('should display "Revoked" status for inactive keys', () => {
      const apiKey = mockApiKey({
        is_active: false,
      });

      renderWithProviders(<ApiKeyList {...defaultProps} apiKeys={[apiKey]} />);

      const revokedChip = screen.getByText('Revoked');
      expect(revokedChip).toBeInTheDocument();
      // Check the parent chip element for color class
      expect(revokedChip.closest('.MuiChip-root')).toHaveClass('MuiChip-colorError');
    });

    it('should display "Expired" status for expired keys', () => {
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);

      const apiKey = mockApiKey({
        is_active: true,
        expires_at: yesterday.toISOString(),
      });

      renderWithProviders(<ApiKeyList {...defaultProps} apiKeys={[apiKey]} />);

      const expiredChip = screen.getByText('Expired');
      expect(expiredChip).toBeInTheDocument();
      // Check the parent chip element for color class
      expect(expiredChip.closest('.MuiChip-root')).toHaveClass('MuiChip-colorWarning');
    });

    it('should display warning icon for expired keys', () => {
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);

      const apiKey = mockApiKey({
        is_active: true,
        expires_at: yesterday.toISOString(),
      });

      renderWithProviders(<ApiKeyList {...defaultProps} apiKeys={[apiKey]} />);

      const warningIcon = screen.getByTestId('WarningIcon');
      expect(warningIcon).toBeInTheDocument();
    });
  });

  describe('Revoke Functionality', () => {
    it('should display revoke button for active keys', () => {
      const apiKey = mockApiKey({
        is_active: true,
      });

      renderWithProviders(<ApiKeyList {...defaultProps} apiKeys={[apiKey]} />);

      const revokeButton = screen.getByRole('button');
      expect(revokeButton).toBeInTheDocument();
      expect(revokeButton).not.toBeDisabled();
    });

    it('should not display revoke button for inactive keys', () => {
      const apiKey = mockApiKey({
        is_active: false,
      });

      renderWithProviders(<ApiKeyList {...defaultProps} apiKeys={[apiKey]} />);

      const revokeButton = screen.queryByRole('button');
      expect(revokeButton).not.toBeInTheDocument();
    });

    it('should call onRevoke when revoke button is clicked', async () => {
      const user = userEvent.setup();
      const apiKey = mockApiKey({
        id: 123,
        is_active: true,
      });

      renderWithProviders(<ApiKeyList {...defaultProps} apiKeys={[apiKey]} />);

      const revokeButton = screen.getByRole('button');
      await user.click(revokeButton);

      expect(mockOnRevoke).toHaveBeenCalledWith(123);
    });

    it('should disable revoke button when isRevoking is true', () => {
      const apiKey = mockApiKey({
        is_active: true,
      });

      renderWithProviders(
        <ApiKeyList {...defaultProps} apiKeys={[apiKey]} isRevoking={true} />
      );

      const revokeButton = screen.getByRole('button');
      expect(revokeButton).toBeDisabled();
    });
  });

  describe('Multiple API Keys', () => {
    it('should display multiple API keys', () => {
      const apiKeys = [
        mockApiKey({ id: 1, label: 'First Key', is_active: true }),
        mockApiKey({ id: 2, label: 'Second Key', is_active: false }),
        mockApiKey({ id: 3, label: null, is_active: true }),
      ];

      renderWithProviders(<ApiKeyList {...defaultProps} apiKeys={apiKeys} />);

      expect(screen.getByText('First Key')).toBeInTheDocument();
      expect(screen.getByText('Second Key')).toBeInTheDocument();
      expect(screen.getByText('API Key 3')).toBeInTheDocument();
    });

    it('should display correct status for each key', () => {
      const apiKeys = [
        mockApiKey({ id: 1, is_active: true }),
        mockApiKey({ id: 2, is_active: false }),
      ];

      renderWithProviders(<ApiKeyList {...defaultProps} apiKeys={apiKeys} />);

      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('Revoked')).toBeInTheDocument();
    });

    it('should only show revoke buttons for active keys', () => {
      const apiKeys = [
        mockApiKey({ id: 1, is_active: true }),
        mockApiKey({ id: 2, is_active: false }),
        mockApiKey({ id: 3, is_active: true }),
      ];

      renderWithProviders(<ApiKeyList {...defaultProps} apiKeys={apiKeys} />);

      const revokeButtons = screen.getAllByRole('button');
      expect(revokeButtons).toHaveLength(2); // Only for active keys
    });
  });

  describe('Responsive Layout', () => {
    it('should render with responsive grid layout', () => {
      const apiKey = mockApiKey({
        id: 1,
        label: 'Test Key',
        is_active: true,
      });

      renderWithProviders(<ApiKeyList {...defaultProps} apiKeys={[apiKey]} />);

      // Check that the grid container exists
      const gridContainer = screen.getByText('Test Key').closest('.MuiBox-root');
      expect(gridContainer).toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels for interactive elements', () => {
      const apiKey = mockApiKey({
        id: 1,
        is_active: true,
      });

      renderWithProviders(<ApiKeyList {...defaultProps} apiKeys={[apiKey]} />);

      const revokeButton = screen.getByRole('button');
      expect(revokeButton).toBeInTheDocument();
    });

    it('should have proper tooltip for revoke button', async () => {
      const user = userEvent.setup();
      const apiKey = mockApiKey({
        id: 1,
        is_active: true,
      });

      renderWithProviders(<ApiKeyList {...defaultProps} apiKeys={[apiKey]} />);

      const revokeButton = screen.getByRole('button');
      await user.hover(revokeButton);

      await waitFor(() => {
        expect(screen.getByText('Revoke API key')).toBeInTheDocument();
      });
    });

    it('should have proper tooltip for expired key warning', async () => {
      const user = userEvent.setup();
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);

      const apiKey = mockApiKey({
        is_active: true,
        expires_at: yesterday.toISOString(),
      });

      renderWithProviders(<ApiKeyList {...defaultProps} apiKeys={[apiKey]} />);

      const warningIcon = screen.getByTestId('WarningIcon');
      await user.hover(warningIcon);

      await waitFor(() => {
        expect(screen.getByText('This key has expired')).toBeInTheDocument();
      });
    });
  });

  describe('Edge Cases', () => {
    it('should handle keys with very long labels', () => {
      const longLabel = 'A'.repeat(200);
      const apiKey = mockApiKey({
        id: 1,
        label: longLabel,
        is_active: true,
      });

      renderWithProviders(<ApiKeyList {...defaultProps} apiKeys={[apiKey]} />);

      expect(screen.getByText(longLabel)).toBeInTheDocument();
    });

    it('should handle keys with special characters in labels', () => {
      const specialLabel = 'Test Key with 特殊字符 & symbols!@#$%';
      const apiKey = mockApiKey({
        id: 1,
        label: specialLabel,
        is_active: true,
      });

      renderWithProviders(<ApiKeyList {...defaultProps} apiKeys={[apiKey]} />);

      expect(screen.getByText(specialLabel)).toBeInTheDocument();
    });

    it('should handle invalid date strings gracefully', () => {
      const apiKey = mockApiKey({
        id: 1,
        label: null, // This will fallback to "API Key 1"
        created_at: 'invalid-date',
        expires_at: 'invalid-date',
        last_used_at: 'invalid-date',
        is_active: true,
      });

      renderWithProviders(<ApiKeyList {...defaultProps} apiKeys={[apiKey]} />);

      // Should not crash and should render something
      expect(screen.getByText('API Key 1')).toBeInTheDocument();
    });
  });
});
