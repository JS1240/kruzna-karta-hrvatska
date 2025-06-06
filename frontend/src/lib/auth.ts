// Simple authentication system to replace Firebase
export interface User {
  id: string;
  email: string;
  name?: string;
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

export const login = (email: string, password: string): Promise<User> => {
  return new Promise((resolve, reject) => {
    // Simple mock authentication - replace with real authentication later
    if (email && password.length >= 6) {
      const user: User = {
        id: Date.now().toString(),
        email,
        name: email.split("@")[0],
      };

      localStorage.setItem(AUTH_KEY, JSON.stringify(user));
      localStorage.setItem(LOGIN_KEY, "true");

      // Dispatch custom event for auth state change
      window.dispatchEvent(
        new CustomEvent("authStateChanged", {
          detail: { isLoggedIn: true, user },
        }),
      );

      resolve(user);
    } else {
      reject(new Error("Invalid email or password"));
    }
  });
};

export const signup = (email: string, password: string): Promise<User> => {
  return new Promise((resolve, reject) => {
    // Simple mock signup - replace with real authentication later
    if (email && password.length >= 6) {
      const user: User = {
        id: Date.now().toString(),
        email,
        name: email.split("@")[0],
      };

      localStorage.setItem(AUTH_KEY, JSON.stringify(user));
      localStorage.setItem(LOGIN_KEY, "true");

      // Dispatch custom event for auth state change
      window.dispatchEvent(
        new CustomEvent("authStateChanged", {
          detail: { isLoggedIn: true, user },
        }),
      );

      resolve(user);
    } else {
      reject(
        new Error("Invalid email or password must be at least 6 characters"),
      );
    }
  });
};

export const logout = (): void => {
  localStorage.removeItem(AUTH_KEY);
  localStorage.removeItem(LOGIN_KEY);

  // Dispatch custom event for auth state change
  window.dispatchEvent(
    new CustomEvent("authStateChanged", {
      detail: { isLoggedIn: false, user: null },
    }),
  );
};

export const googleLogin = (): Promise<User> => {
  return new Promise((resolve, reject) => {
    // Mock Google login - replace with real Google OAuth later
    const mockGoogleUser: User = {
      id: "google_" + Date.now().toString(),
      email: "user@gmail.com",
      name: "Google User",
    };

    localStorage.setItem(AUTH_KEY, JSON.stringify(mockGoogleUser));
    localStorage.setItem(LOGIN_KEY, "true");

    // Dispatch custom event for auth state change
    window.dispatchEvent(
      new CustomEvent("authStateChanged", {
        detail: { isLoggedIn: true, user: mockGoogleUser },
      }),
    );

    resolve(mockGoogleUser);
  });
};
