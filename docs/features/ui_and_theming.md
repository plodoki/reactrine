# UI Components and Theming

The frontend of the Reactrine is built using **Material-UI (MUI)**, a comprehensive and popular React UI framework. This provides a rich set of pre-built, accessible, and customizable components to accelerate your development process.

## Component Library

The project includes a wide range of MUI components, from basic elements like buttons and inputs to more complex components like data grids and date pickers. You can find the full list of available components and their usage in the [official MUI documentation](https://mui.com/material-ui/all-components/).

## Theming System

The application features a robust, centralized theming system that supports both **light and dark modes** out of the box.

### How It Works

The theming system is built around a `ThemeModeProvider` that uses React Context to manage and distribute the current theme to all components in the application. This provider is configured in `frontend/src/providers/AppThemeProvider.tsx`.

The core theme logic resides in `frontend/src/assets/styles/theme.ts`. This file contains the `getDesignTokens` function, which defines the specific color palettes, typography settings, and component style overrides for both light and dark modes.

### Switching Themes

The application includes a `ThemeToggle` component that allows users to switch between light mode, dark mode, or sync with their system's theme preference. The user's choice is automatically persisted in their browser's `localStorage`, so their preference is remembered across sessions.

### Customizing the Theme

You can easily customize the look and feel of your application by modifying the theme configuration.

To change the color scheme, typography, or the default styles of a component, simply edit the `getDesignTokens` function in `frontend/src/assets/styles/theme.ts`.

For example, to change the primary color for the light theme, you would modify the `primary` object within the `light` mode palette:

```typescript
// frontend/src/assets/styles/theme.ts

const getDesignTokens = (mode: PaletteMode): ThemeOptions => ({
  palette: {
    mode,
    ...(mode === "light"
      ? {
          // Light mode palette
          primary: {
            main: "#007acc", // Change this to your desired color
            light: "#3399d6",
            dark: "#005a9e",
          },
          // ... other light mode colors
        }
      : {
          // Dark mode palette
          // ...
        }),
  },
  // ... other theme settings
});
```

By leveraging this centralized theming system, you can ensure a consistent and polished design throughout your entire application.
