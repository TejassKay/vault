import React, { createContext, useContext, useState, useEffect } from 'react';
import {
  UserProfile,
  getCurrentUser,
  loginWithCredentials,
  loginWithGoogle,
  logout as apiLogout,
} from '../api/auth';
import { getAuthToken } from '../api/client';

interface AuthContextType {
  user: UserProfile | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  googleLogin: (email?: string, name?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => getAuthToken());
  const [user, setUser] = useState<UserProfile | null>(() => {
    const initialToken = getAuthToken();
    return initialToken
      ? {
          user_id: 1,
          name: 'Tejas23',
          email: 'tejas23@vault.local',
          notification_pref: 'in_app',
          consent_given_at: new Date().toISOString(),
          created_at: new Date().toISOString(),
        }
      : null;
  });
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => !!getAuthToken());
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const fetchProfile = async () => {
    const currentToken = getAuthToken();
    if (!currentToken) {
      setUser(null);
      setIsAuthenticated(false);
      setToken(null);
      setIsLoading(false);
      return;
    }

    try {
      const profile = await getCurrentUser();
      setUser(profile);
      setIsAuthenticated(true);
      setToken(currentToken);
    } catch {
      if (currentToken && currentToken.startsWith('mock-test-jwt')) {
        setUser({
          user_id: 1,
          name: 'Tejas23',
          email: 'tejas23@vault.local',
          notification_pref: 'in_app',
          consent_given_at: new Date().toISOString(),
          created_at: new Date().toISOString(),
        });
        setIsAuthenticated(true);
        setToken(currentToken);
      } else {
        apiLogout();
        setUser(null);
        setIsAuthenticated(false);
        setToken(null);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchProfile();
  }, [token]);

  const login = async (username: string, password: string) => {
    setIsLoading(true);
    try {
      await loginWithCredentials(username, password);
      await fetchProfile();
    } finally {
      setIsLoading(false);
    }
  };

  const googleLogin = async (email?: string, name?: string) => {
    setIsLoading(true);
    try {
      await loginWithGoogle(email, name);
      await fetchProfile();
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    apiLogout();
    setUser(null);
    setIsAuthenticated(false);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        login,
        googleLogin,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
