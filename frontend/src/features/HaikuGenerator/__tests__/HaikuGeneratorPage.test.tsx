import { mockHaikuResponse } from '@/test/factories';
import { renderWithProviders } from '@/test/utils';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import HaikuGeneratorPage from '../HaikuGeneratorPage';

// Mock the hook
vi.mock('../hooks/useHaikuGenerator', () => ({
  useHaikuGenerator: vi.fn(),
}));

import { useHaikuGenerator } from '../hooks/useHaikuGenerator';

describe('HaikuGeneratorPage Component', () => {
  const mockUseHaikuGenerator = useHaikuGenerator as ReturnType<typeof vi.fn>;

  const defaultHookReturn = {
    mutate: vi.fn(),
    data: null,
    isPending: false,
    isError: false,
    error: null,
    isSuccess: false,
    isIdle: true,
    reset: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
    mockUseHaikuGenerator.mockReturnValue(defaultHookReturn);
  });

  describe('Component Rendering', () => {
    it('should render the main heading and description', () => {
      renderWithProviders(<HaikuGeneratorPage />);

      expect(
        screen.getByRole('heading', { name: /haiku generator/i })
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          'Enter a topic below and let our AI create a beautiful haiku for you.'
        )
      ).toBeInTheDocument();
    });

    it('should render the form elements', () => {
      renderWithProviders(<HaikuGeneratorPage />);

      expect(screen.getByLabelText(/haiku topic/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /generate/i })).toBeInTheDocument();
    });

    it('should have the topic input field as required', () => {
      renderWithProviders(<HaikuGeneratorPage />);

      const topicInput = screen.getByLabelText(/haiku topic/i);
      expect(topicInput).toBeRequired();
    });
  });

  describe('Form Interactions', () => {
    it('should update topic input value when user types', async () => {
      const user = userEvent.setup();
      renderWithProviders(<HaikuGeneratorPage />);

      const topicInput = screen.getByLabelText(/haiku topic/i);
      await user.type(topicInput, 'nature');

      expect(topicInput).toHaveValue('nature');
    });

    it('should disable generate button when topic is empty', () => {
      renderWithProviders(<HaikuGeneratorPage />);

      const generateButton = screen.getByRole('button', { name: /generate/i });
      expect(generateButton).toBeDisabled();
    });

    it('should enable generate button when topic has content', async () => {
      const user = userEvent.setup();
      renderWithProviders(<HaikuGeneratorPage />);

      const topicInput = screen.getByLabelText(/haiku topic/i);
      const generateButton = screen.getByRole('button', { name: /generate/i });

      await user.type(topicInput, 'nature');
      expect(generateButton).toBeEnabled();
    });

    it('should disable generate button when topic is only whitespace', async () => {
      const user = userEvent.setup();
      renderWithProviders(<HaikuGeneratorPage />);

      const topicInput = screen.getByLabelText(/haiku topic/i);
      const generateButton = screen.getByRole('button', { name: /generate/i });

      await user.type(topicInput, '   ');
      expect(generateButton).toBeDisabled();
    });

    it('should call mutate with trimmed topic when form is submitted', async () => {
      const mockMutate = vi.fn();
      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        mutate: mockMutate,
      });

      const user = userEvent.setup();
      renderWithProviders(<HaikuGeneratorPage />);

      const topicInput = screen.getByLabelText(/haiku topic/i);
      const generateButton = screen.getByRole('button', { name: /generate/i });

      await user.type(topicInput, '  nature  ');
      await user.click(generateButton);

      expect(mockMutate).toHaveBeenCalledWith({ topic: 'nature' });
    });

    it('should call mutate when form is submitted via Enter key', async () => {
      const mockMutate = vi.fn();
      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        mutate: mockMutate,
      });

      const user = userEvent.setup();
      renderWithProviders(<HaikuGeneratorPage />);

      const topicInput = screen.getByLabelText(/haiku topic/i);
      await user.type(topicInput, 'ocean');
      await user.keyboard('{Enter}');

      expect(mockMutate).toHaveBeenCalledWith({ topic: 'ocean' });
    });

    it('should not call mutate when form is submitted with empty topic', async () => {
      const mockMutate = vi.fn();
      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        mutate: mockMutate,
      });

      const user = userEvent.setup();
      renderWithProviders(<HaikuGeneratorPage />);

      // Don't type anything, just try to submit
      await user.keyboard('{Enter}');

      expect(mockMutate).not.toHaveBeenCalled();
    });
  });

  describe('Loading State', () => {
    it('should show loading spinner when isPending is true', () => {
      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        isPending: true,
      });

      renderWithProviders(<HaikuGeneratorPage />);

      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('should disable generate button when isPending is true', () => {
      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        isPending: true,
      });

      renderWithProviders(<HaikuGeneratorPage />);

      // When isPending is true, the button shows a spinner and has no text
      const generateButton = screen.getByRole('button');
      expect(generateButton).toBeDisabled();
    });

    it('should disable generate button when isPending is true even with valid topic', async () => {
      const user = userEvent.setup();
      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        isPending: true,
      });

      renderWithProviders(<HaikuGeneratorPage />);

      const topicInput = screen.getByLabelText(/haiku topic/i);
      await user.type(topicInput, 'nature');

      // When isPending is true, the button shows a spinner and has no text
      const generateButton = screen.getByRole('button');
      expect(generateButton).toBeDisabled();
    });
  });

  describe('Error Handling', () => {
    it('should display error message when isError is true', () => {
      const mockError = new Error('Failed to generate haiku');
      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        isError: true,
        error: mockError,
      });

      renderWithProviders(<HaikuGeneratorPage />);

      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText('Failed to generate haiku')).toBeInTheDocument();
    });

    it('should display generic error message for non-Error objects', () => {
      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        isError: true,
        error: 'Some string error',
      });

      renderWithProviders(<HaikuGeneratorPage />);

      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByText('An unexpected error occurred.')).toBeInTheDocument();
    });

    it('should not display error message when isError is false', () => {
      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        isError: false,
        error: null,
      });

      renderWithProviders(<HaikuGeneratorPage />);

      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });

  describe('Haiku Display', () => {
    it('should display generated haiku when data is available', () => {
      const mockHaiku = mockHaikuResponse({
        lines: [
          'Cherry blossoms fall',
          'Gently on the morning dew',
          'Spring awakens now',
        ],
        syllables: [5, 7, 5],
        model_used: 'gpt-4o-mini',
        provider_used: 'openai',
      });

      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        data: mockHaiku,
      });

      renderWithProviders(<HaikuGeneratorPage />);

      expect(screen.getByRole('heading', { name: /your haiku/i })).toBeInTheDocument();
      expect(screen.getByText('Cherry blossoms fall (5)')).toBeInTheDocument();
      expect(screen.getByText('Gently on the morning dew (7)')).toBeInTheDocument();
      expect(screen.getByText('Spring awakens now (5)')).toBeInTheDocument();
      expect(
        screen.getByText('Generated by: openai (gpt-4o-mini)')
      ).toBeInTheDocument();
    });

    it('should display each line with syllable count', () => {
      const mockHaiku = mockHaikuResponse({
        lines: ['Line one', 'Line two here', 'Line three'],
        syllables: [3, 4, 3],
        model_used: 'gpt-4',
        provider_used: 'openai',
      });

      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        data: mockHaiku,
      });

      renderWithProviders(<HaikuGeneratorPage />);

      expect(screen.getByText('Line one (3)')).toBeInTheDocument();
      expect(screen.getByText('Line two here (4)')).toBeInTheDocument();
      expect(screen.getByText('Line three (3)')).toBeInTheDocument();
    });

    it('should not display haiku when data is null', () => {
      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        data: null,
      });

      renderWithProviders(<HaikuGeneratorPage />);

      expect(
        screen.queryByRole('heading', { name: /your haiku/i })
      ).not.toBeInTheDocument();
    });

    it('should not display haiku when lines array is missing', () => {
      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        data: {
          ...mockHaikuResponse(),
          lines: undefined,
        },
      });

      renderWithProviders(<HaikuGeneratorPage />);

      expect(
        screen.queryByRole('heading', { name: /your haiku/i })
      ).not.toBeInTheDocument();
    });

    it('should not display haiku when syllables array is missing', () => {
      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        data: {
          ...mockHaikuResponse(),
          syllables: undefined,
        },
      });

      renderWithProviders(<HaikuGeneratorPage />);

      expect(
        screen.queryByRole('heading', { name: /your haiku/i })
      ).not.toBeInTheDocument();
    });

    it('should not display haiku when lines and syllables arrays have different lengths', () => {
      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        data: {
          ...mockHaikuResponse(),
          lines: ['Line one', 'Line two'],
          syllables: [5, 7, 5], // Different length
        },
      });

      renderWithProviders(<HaikuGeneratorPage />);

      expect(
        screen.queryByRole('heading', { name: /your haiku/i })
      ).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper form labeling', () => {
      renderWithProviders(<HaikuGeneratorPage />);

      const topicInput = screen.getByLabelText(/haiku topic/i);
      expect(topicInput).toBeRequired();
    });

    it('should have proper heading hierarchy', () => {
      renderWithProviders(<HaikuGeneratorPage />);

      const mainHeading = screen.getByRole('heading', { name: /haiku generator/i });
      expect(mainHeading).toHaveProperty('tagName', 'H1');
    });

    it('should have proper heading hierarchy for generated haiku', () => {
      const mockHaiku = mockHaikuResponse();
      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        data: mockHaiku,
      });

      renderWithProviders(<HaikuGeneratorPage />);

      const haikuHeading = screen.getByRole('heading', { name: /your haiku/i });
      expect(haikuHeading).toHaveProperty('tagName', 'H2');
    });

    it('should have proper alert role for error messages', () => {
      const mockError = new Error('Test error');
      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        isError: true,
        error: mockError,
      });

      renderWithProviders(<HaikuGeneratorPage />);

      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();
    });

    it('should have proper button type for form submission', () => {
      renderWithProviders(<HaikuGeneratorPage />);

      const generateButton = screen.getByRole('button', { name: /generate/i });
      expect(generateButton).toHaveAttribute('type', 'submit');
    });
  });

  describe('Form Validation', () => {
    it('should prevent form submission with empty topic', async () => {
      const mockMutate = vi.fn();
      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        mutate: mockMutate,
      });

      const user = userEvent.setup();
      renderWithProviders(<HaikuGeneratorPage />);

      // Try to submit without typing anything
      await user.keyboard('{Enter}');

      expect(mockMutate).not.toHaveBeenCalled();
    });

    it('should prevent form submission with only whitespace topic', async () => {
      const mockMutate = vi.fn();
      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        mutate: mockMutate,
      });

      const user = userEvent.setup();
      renderWithProviders(<HaikuGeneratorPage />);

      const topicInput = screen.getByLabelText(/haiku topic/i);
      await user.type(topicInput, '   ');
      await user.keyboard('{Enter}');

      expect(mockMutate).not.toHaveBeenCalled();
    });
  });

  describe('Edge Cases', () => {
    it('should handle missing hook data gracefully', () => {
      mockUseHaikuGenerator.mockReturnValue({
        mutate: vi.fn(),
        data: undefined,
        isPending: false,
        isError: false,
        error: undefined,
        isSuccess: false,
        isIdle: true,
        reset: vi.fn(),
      });

      expect(() => renderWithProviders(<HaikuGeneratorPage />)).not.toThrow();
    });

    it('should not display haiku when lines array is empty', () => {
      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        data: {
          ...mockHaikuResponse(),
          lines: [],
          syllables: [],
        },
      });

      renderWithProviders(<HaikuGeneratorPage />);

      expect(
        screen.queryByRole('heading', { name: /your haiku/i })
      ).not.toBeInTheDocument();
    });

    it('should handle provider and model information display', () => {
      const mockHaiku = mockHaikuResponse({
        model_used: 'claude-3-sonnet',
        provider_used: 'bedrock',
      });

      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        data: mockHaiku,
      });

      renderWithProviders(<HaikuGeneratorPage />);

      expect(
        screen.getByText('Generated by: bedrock (claude-3-sonnet)')
      ).toBeInTheDocument();
    });

    it('should handle long topics gracefully', async () => {
      const mockMutate = vi.fn();
      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        mutate: mockMutate,
      });

      const user = userEvent.setup();
      renderWithProviders(<HaikuGeneratorPage />);

      const longTopic = 'a'.repeat(1000);
      const topicInput = screen.getByLabelText(/haiku topic/i);
      await user.type(topicInput, longTopic);
      await user.keyboard('{Enter}');

      expect(mockMutate).toHaveBeenCalledWith({ topic: longTopic });
    });

    it('should handle special characters in topic', async () => {
      const mockMutate = vi.fn();
      mockUseHaikuGenerator.mockReturnValue({
        ...defaultHookReturn,
        mutate: mockMutate,
      });

      const user = userEvent.setup();
      renderWithProviders(<HaikuGeneratorPage />);

      const specialTopic = 'nature & seasons! 🌸';
      const topicInput = screen.getByLabelText(/haiku topic/i);
      await user.type(topicInput, specialTopic);
      await user.keyboard('{Enter}');

      expect(mockMutate).toHaveBeenCalledWith({ topic: specialTopic });
    });
  });

  describe('User Experience', () => {
    it('should not auto-focus on topic input', () => {
      renderWithProviders(<HaikuGeneratorPage />);

      const topicInput = screen.getByLabelText(/haiku topic/i);
      // The input should not be focused by default
      expect(topicInput).not.toHaveFocus();
    });

    it('should maintain topic input value during component lifecycle', async () => {
      const user = userEvent.setup();
      renderWithProviders(<HaikuGeneratorPage />);

      const topicInput = screen.getByLabelText(/haiku topic/i);
      await user.type(topicInput, 'nature');

      // Topic should remain in input
      expect(topicInput).toHaveValue('nature');
    });
  });
});
