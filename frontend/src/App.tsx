import AppProviders from '@/providers/AppProviders';
import AppRoutes from '@/routes';

const App = () => {
  return (
    <AppProviders>
      <AppRoutes />
    </AppProviders>
  );
};

export default App;
