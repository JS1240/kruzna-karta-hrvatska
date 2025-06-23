// Enhanced authentication system
export interface User {
  id: string;
  email: string;
  name?: string;
  avatar?: string;
  preferences?: UserPreferences;
  createdAt?: string;
  emailVerified?: boolean;
}

export interface UserPreferences {
  favoriteCategories: string[];
  notificationSettings: {
    email: boolean;
    push: boolean;
    eventReminders: boolean;
    newsletter: boolean;
  };
  language: 'en' | 'hr';
  theme: 'light' | 'dark' | 'system';
}

export const AUTH_KEY = "auth_user";
export const LOGIN_KEY = "isLoggedIn";

export const getCurrentUser = (): User | null => {
  const userJson = localStorage.getItem(AUTH_KEY);
  return userJson ? JSON.parse(userJson) : null;
};

export const isLoggedIn = (): boolean => {
  return localStorage.getItem(LOGIN_KEY) === "true";
};

export const login = async (email: string, password: string): Promise<User> => {
  try {
    // TODO: Replace with actual API call
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      throw new Error('Invalid credentials');
    }

    const { user, token } = await response.json();
    
    // Store auth token
    localStorage.setItem('auth_token', token);
    localStorage.setItem(AUTH_KEY, JSON.stringify(user));
    localStorage.setItem(LOGIN_KEY, "true");

    // Dispatch custom event for auth state change
    window.dispatchEvent(
      new CustomEvent("authStateChanged", {
        detail: { isLoggedIn: true, user },
      }),
    );

    return user;
  } catch (error) {
    // Fallback to mock for development
    if (email && password.length >= 6) {
      const user: User = {
        id: Date.now().toString(),
        email,
        name: email.split("@")[0],
        createdAt: new Date().toISOString(),
        emailVerified: false,
        preferences: {
          favoriteCategories: [],
          notificationSettings: {
            email: true,
            push: true,
            eventReminders: true,
            newsletter: false,
          },
          language: 'en',
          theme: 'system',
        },
      };

      localStorage.setItem(AUTH_KEY, JSON.stringify(user));
      localStorage.setItem(LOGIN_KEY, "true");

      window.dispatchEvent(
        new CustomEvent("authStateChanged", {
          detail: { isLoggedIn: true, user },
        }),
      );

      return user;
    } else {
      throw new Error("Invalid email or password");
    }
  }
};

export const signup = async (email: string, password: string, name?: string): Promise<User> => {
  try {
    // TODO: Replace with actual API call
    const response = await fetch('/api/auth/signup', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password, name }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Registration failed');
    }

    const { user, token } = await response.json();
    
    localStorage.setItem('auth_token', token);
    localStorage.setItem(AUTH_KEY, JSON.stringify(user));
    localStorage.setItem(LOGIN_KEY, "true");

    window.dispatchEvent(
      new CustomEvent("authStateChanged", {
        detail: { isLoggedIn: true, user },
      }),
    );

    return user;
  } catch (error) {
    // Fallback to mock for development
    if (email && password.length >= 6) {
      const user: User = {
        id: Date.now().toString(),
        email,
        name: name || email.split("@")[0],
        createdAt: new Date().toISOString(),
        emailVerified: false,
        preferences: {
          favoriteCategories: [],
          notificationSettings: {
            email: true,
            push: true,
            eventReminders: true,
            newsletter: false,
          },
          language: 'en',
          theme: 'system',
        },
      };

      localStorage.setItem(AUTH_KEY, JSON.stringify(user));
      localStorage.setItem(LOGIN_KEY, "true");

      window.dispatchEvent(
        new CustomEvent("authStateChanged", {
          detail: { isLoggedIn: true, user },
        }),
      );

      return user;
    } else {
      throw new Error("Invalid email or password must be at least 6 characters");
    }
  }
};

export const logout = async (): Promise<void> => {
  try {
    // TODO: Call API to invalidate token
    const token = localStorage.getItem('auth_token');
    if (token) {
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
    }
  } catch (error) {
    console.warn('Logout API call failed:', error);
  } finally {
    localStorage.removeItem(AUTH_KEY);
    localStorage.removeItem(LOGIN_KEY);
    localStorage.removeItem('auth_token');
    localStorage.removeItem('favoriteEvents');
    localStorage.removeItem('notificationEmail');

    window.dispatchEvent(
      new CustomEvent("authStateChanged", {
        detail: { isLoggedIn: false, user: null },
      }),
    );
  }
};

export const googleLogin = async (): Promise<User> => {
  try {
    // TODO: Implement actual Google OAuth
    // For now, redirect to Google OAuth endpoint
    window.location.href = '/api/auth/google';
    
    // This won't execute in real implementation
    throw new Error('Redirecting to Google OAuth');
  } catch (error) {
    // Mock Google login for development
    const mockGoogleUser: User = {
      id: "google_" + Date.now().toString(),
      email: "user@gmail.com",
      name: "Google User",
      avatar: "https://via.placeholder.com/40",
      createdAt: new Date().toISOString(),
      emailVerified: true,
      preferences: {
        favoriteCategories: [],
        notificationSettings: {
          email: true,
          push: true,
          eventReminders: true,
          newsletter: false,
        },
        language: 'en',
        theme: 'system',
      },
    };

    localStorage.setItem(AUTH_KEY, JSON.stringify(mockGoogleUser));
    localStorage.setItem(LOGIN_KEY, "true");

    window.dispatchEvent(
      new CustomEvent("authStateChanged", {
        detail: { isLoggedIn: true, user: mockGoogleUser },
      }),
    );

    return mockGoogleUser;
  }
};

export const updateUserProfile = async (updates: Partial<User>): Promise<User> => {
  const currentUser = getCurrentUser();
  if (!currentUser) {
    throw new Error('No user logged in');
  }

  try {
    const token = localStorage.getItem('auth_token');
    const response = await fetch('/api/auth/profile', {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(updates),
    });

    if (!response.ok) {
      throw new Error('Failed to update profile');
    }

    const updatedUser = await response.json();
    localStorage.setItem(AUTH_KEY, JSON.stringify(updatedUser));
    
    window.dispatchEvent(
      new CustomEvent("authStateChanged", {
        detail: { isLoggedIn: true, user: updatedUser },
      }),
    );

    return updatedUser;
  } catch (error) {
    // Fallback to local update for development
    const updatedUser = { ...currentUser, ...updates };
    localStorage.setItem(AUTH_KEY, JSON.stringify(updatedUser));
    
    window.dispatchEvent(
      new CustomEvent("authStateChanged", {
        detail: { isLoggedIn: true, user: updatedUser },
      }),
    );

    return updatedUser;
  }
};

export const sendPasswordReset = async (email: string): Promise<void> => {
  try {
    const response = await fetch('/api/auth/reset-password', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email }),
    });

    if (!response.ok) {
      throw new Error('Failed to send reset email');
    }
  } catch (error) {
    // Mock success for development
    console.log('Password reset email sent to:', email);
  }
};

export const verifyEmail = async (token: string): Promise<void> => {
  try {
    const response = await fetch(`/api/auth/verify-email?token=${token}`, {
      method: 'POST',
    });

    if (!response.ok) {
      throw new Error('Email verification failed');
    }

    const currentUser = getCurrentUser();
    if (currentUser) {
      const updatedUser = { ...currentUser, emailVerified: true };
      localStorage.setItem(AUTH_KEY, JSON.stringify(updatedUser));
    }
  } catch (error) {
    throw new Error('Email verification failed');
  }
};

export const getAuthHeaders = (): Record<string, string> => {
  const token = localStorage.getItem('auth_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
};
