import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Checkbox,
  Chip,
  CircularProgress,
  Container,
  Divider,
  FormControlLabel,
  Grid,
  LinearProgress,
  Paper,
  Radio,
  RadioGroup,
  Switch,
  TextField,
  Typography,
} from '@mui/material';
import React, { useState } from 'react';

const ComponentShowcasePage: React.FC = () => {
  const [radioValue, setRadioValue] = useState('option1');
  const [checkedState, setCheckedState] = useState(true);
  const [switchState, setSwitchState] = useState(false);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h2" component="h1" gutterBottom align="center">
        MUI Component Showcase
      </Typography>
      <Typography variant="subtitle1" align="center" sx={{ mb: 4 }}>
        Demonstrating Material-UI components with light/dark theming
      </Typography>

      {/* Note: Using Grid v1 API - warnings about deprecated props are expected */}
      <Grid container spacing={3}>
        {/* Form Components */}
        <Grid xs={12} sm={6} md={4}>
          <Card>
            <CardHeader title="Form Components" />
            <CardContent>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <TextField
                  label="Email"
                  type="email"
                  variant="outlined"
                  fullWidth
                  placeholder="Enter your email"
                />
                <TextField
                  label="Message"
                  multiline
                  rows={3}
                  variant="outlined"
                  fullWidth
                  placeholder="Enter your message"
                />
                <TextField
                  label="Password"
                  type="password"
                  variant="outlined"
                  fullWidth
                  placeholder="Enter your password"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Input Controls */}
        <Grid xs={12} sm={6} md={4}>
          <Card>
            <CardHeader title="Input Controls" />
            <CardContent>
              <RadioGroup
                value={radioValue}
                onChange={e => setRadioValue(e.target.value)}
              >
                <FormControlLabel
                  value="option1"
                  control={<Radio />}
                  label="Option 1"
                />
                <FormControlLabel
                  value="option2"
                  control={<Radio />}
                  label="Option 2"
                />
                <FormControlLabel
                  value="option3"
                  control={<Radio />}
                  label="Option 3"
                />
              </RadioGroup>
              <Divider sx={{ my: 2 }} />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={checkedState}
                    onChange={e => setCheckedState(e.target.checked)}
                  />
                }
                label="Checkbox option"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={switchState}
                    onChange={e => setSwitchState(e.target.checked)}
                  />
                }
                label="Switch option"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Buttons and Actions */}
        <Grid xs={12} sm={6} md={4}>
          <Card>
            <CardHeader title="Buttons & Actions" />
            <CardContent>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Button variant="contained">Contained</Button>
                  <Button variant="outlined">Outlined</Button>
                  <Button variant="text">Text</Button>
                </Box>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Button variant="contained" color="secondary">
                    Secondary
                  </Button>
                  <Button variant="contained" color="error">
                    Error
                  </Button>
                  <Button variant="contained" color="success">
                    Success
                  </Button>
                </Box>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Chip label="Default Chip" />
                  <Chip label="Primary Chip" color="primary" />
                  <Chip label="Secondary Chip" color="secondary" />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Feedback Components */}
        <Grid xs={12} sm={6} md={4}>
          <Card>
            <CardHeader title="Feedback & Progress" />
            <CardContent>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Alert severity="success">This is a success alert!</Alert>
                <Alert severity="warning">This is a warning alert!</Alert>
                <Alert severity="error">This is an error alert!</Alert>
                <Box>
                  <Typography variant="body2" gutterBottom>
                    Linear Progress
                  </Typography>
                  <LinearProgress variant="determinate" value={60} />
                </Box>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Typography variant="body2">Circular Progress</Typography>
                  <CircularProgress size={24} />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Typography Showcase */}
        <Grid xs={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h3" gutterBottom>
              Typography Showcase
            </Typography>
            <Typography variant="h4" gutterBottom>
              Heading 4
            </Typography>
            <Typography variant="h5" gutterBottom>
              Heading 5
            </Typography>
            <Typography variant="h6" gutterBottom>
              Heading 6
            </Typography>
            <Typography variant="body1" gutterBottom>
              Body 1: Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do
              eiusmod tempor incididunt ut labore et dolore magna aliqua.
            </Typography>
            <Typography variant="body2" gutterBottom>
              Body 2: Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris
              nisi ut aliquip ex ea commodo consequat.
            </Typography>
            <Typography variant="caption" display="block">
              Caption text
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default ComponentShowcasePage;
