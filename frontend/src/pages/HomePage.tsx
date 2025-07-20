import { generateHaiku } from '@/features/HaikuGenerator/services/haikuService';
import { HealthService } from '@/lib/api-client';
import '@/lib/api-client-config'; // Ensure the client is configured
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Typography,
  styled,
} from '@mui/material';
import { useState } from 'react';

const CodeBlock = styled(Box)(({ theme }) => ({
  fontFamily: 'monospace',
  backgroundColor:
    theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.12)' : 'rgba(0, 0, 0, 0.08)',
  padding: theme.spacing(1),
  borderRadius: theme.shape.borderRadius,
}));

const HomePage = () => {
  const [healthStatus, setHealthStatus] = useState<string>('');
  const [haiku, setHaiku] = useState<string>('');
  const [loading, setLoading] = useState<{
    health: boolean;
    haiku: boolean;
  }>({
    health: false,
    haiku: false,
  });
  const [errors, setErrors] = useState<{
    health: string;
    haiku: string;
  }>({
    health: '',
    haiku: '',
  });

  const checkHealth = async () => {
    setLoading(prev => ({ ...prev, health: true }));
    setErrors(prev => ({ ...prev, health: '' }));
    try {
      const response = await HealthService.healthCheckApiV1HealthGet();
      setHealthStatus(
        `Status: ${response.status} | Database: ${response.details.database}`
      );
    } catch {
      setErrors(prev => ({ ...prev, health: 'Failed to check health' }));
    } finally {
      setLoading(prev => ({ ...prev, health: false }));
    }
  };

  const generateHaikuMethod = async () => {
    setLoading(prev => ({ ...prev, haiku: true }));
    setErrors(prev => ({ ...prev, haiku: '' }));
    try {
      const response = await generateHaiku({ topic: 'technology', style: 'modern' });
      setHaiku(response.haiku);
    } catch {
      setErrors(prev => ({
        ...prev,
        haiku: 'Failed to generate haiku',
      }));
    } finally {
      setLoading(prev => ({ ...prev, haiku: false }));
    }
  };

  return (
    <Box sx={{ p: 3, width: '100%' }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Welcome to FastStack!
      </Typography>
      <Typography variant="body1" sx={{ mb: 3 }}>
        This is the boilerplate homepage. The demo below shows the generated type-safe
        client in action.
      </Typography>

      <Box
        sx={{
          display: 'grid',
          gap: 2,
          gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
        }}
      >
        {/* Health Check with Generated Client */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Health Check
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Uses generated HealthService
            </Typography>
            <Button
              variant="contained"
              onClick={checkHealth}
              disabled={loading.health}
              fullWidth
              sx={{ mb: 2 }}
            >
              {loading.health ? <CircularProgress size={20} /> : 'Check Health'}
            </Button>
            {errors.health && (
              <Alert severity="error" sx={{ mb: 1 }}>
                {errors.health}
              </Alert>
            )}
            {healthStatus && <CodeBlock>{healthStatus}</CodeBlock>}
          </CardContent>
        </Card>

        {/* Haiku with Generated Client */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Haiku Generator
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Uses generated HaikuService
            </Typography>
            <Button
              variant="contained"
              onClick={generateHaikuMethod}
              disabled={loading.haiku}
              fullWidth
              sx={{ mb: 2 }}
            >
              {loading.haiku ? <CircularProgress size={20} /> : 'Generate Haiku'}
            </Button>
            {errors.haiku && (
              <Alert severity="error" sx={{ mb: 1 }}>
                {errors.haiku}
              </Alert>
            )}
            {haiku && (
              <CodeBlock sx={{ fontStyle: 'italic', whiteSpace: 'pre-line' }}>
                {haiku}
              </CodeBlock>
            )}
          </CardContent>
        </Card>
      </Box>

      <Box sx={{ mt: 3 }}>
        <Typography variant="h6" gutterBottom>
          Type-Safe API Client Benefits
        </Typography>
        <Typography variant="body2" component="div">
          <ul>
            <li>
              <strong>Type Safety:</strong> All API calls are fully typed at compile
              time
            </li>
            <li>
              <strong>Auto-completion:</strong> IDE provides intelligent suggestions for
              all endpoints
            </li>
            <li>
              <strong>Error Prevention:</strong> Catch API mismatches before runtime
            </li>
            <li>
              <strong>Consistency:</strong> Same authentication and error handling as
              existing API
            </li>
            <li>
              <strong>Generated from OpenAPI:</strong> Always in sync with backend
              changes
            </li>
          </ul>
        </Typography>
      </Box>
    </Box>
  );
};

export default HomePage;
