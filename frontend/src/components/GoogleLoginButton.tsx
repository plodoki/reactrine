import { CredentialResponse, GoogleLogin } from '@react-oauth/google';
import React from 'react';
import useAppStore from '../stores/useAppStore';

interface GoogleLoginButtonProps {
  onError?: (error: string) => void;
}

const GoogleLoginButton: React.FC<GoogleLoginButtonProps> = ({ onError }) => {
  const { loginWithGoogle, isLoading } = useAppStore();

  // Check if Google OAuth is properly configured
  const googleClientId = import.meta.env.VITE_GOOGLE_OAUTH_CLIENT_ID || '';
  const isGoogleConfigured =
    googleClientId && googleClientId !== 'your_google_client_id_here';

  const handleSuccess = (credentialResponse: CredentialResponse) => {
    (async () => {
      try {
        if (credentialResponse.credential) {
          await loginWithGoogle(credentialResponse.credential);
        } else {
          const errorMsg = 'No credential received from Google';
          console.error(errorMsg);
          onError?.(errorMsg);
        }
      } catch (error) {
        const errorMsg = error instanceof Error ? error.message : 'Google login failed';
        console.error('Google login error:', error);
        onError?.(errorMsg);
      }
    })();
  };

  const handleError = () => {
    const errorMsg = 'Google login failed';
    console.error(errorMsg);
    onError?.(errorMsg);
  };

  // Show disabled state if Google OAuth is not configured
  if (!isGoogleConfigured) {
    return (
      <div className="w-full">
        <div className="w-full h-11 bg-gray-50 border border-gray-300 rounded-lg flex items-center justify-center">
          <div className="flex items-center space-x-2">
            <svg className="w-5 h-5 text-gray-400" viewBox="0 0 24 24">
              <path
                fill="currentColor"
                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
              />
              <path
                fill="currentColor"
                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
              />
              <path
                fill="currentColor"
                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
              />
              <path
                fill="currentColor"
                d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
              />
            </svg>
            <span className="text-sm text-gray-400 font-medium">
              Continue with Google
            </span>
          </div>
        </div>
        <p className="mt-2 text-xs text-gray-500 text-center">
          Google OAuth configuration required
        </p>
      </div>
    );
  }

  return (
    <div className="w-full">
      {!isLoading ? (
        <div className="w-full [&>div]:w-full [&>div>div]:w-full [&>div>div]:justify-center">
          <GoogleLogin
            onSuccess={handleSuccess}
            onError={handleError}
            useOneTap={false}
            size="large"
            width="100%"
            text="continue_with"
            shape="rectangular"
            theme="outline"
          />
        </div>
      ) : (
        <div className="w-full h-11 bg-gray-50 border border-gray-300 rounded-lg flex items-center justify-center">
          <div className="flex items-center space-x-2">
            <svg
              className="animate-spin h-4 w-4 text-gray-600"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            <span className="text-sm text-gray-600 font-medium">Signing in...</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default GoogleLoginButton;
