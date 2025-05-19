
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from '@/hooks/use-toast';
import { Google } from 'lucide-react';

interface LoginFormProps {
  mode: 'login' | 'signup';
  onToggleMode: () => void;
}

const LoginForm = ({ mode, onToggleMode }: LoginFormProps) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      setLoading(false);
      if (mode === 'login') {
        toast({
          title: "Login successful",
          description: "Welcome back to EventMap Croatia!",
        });
      } else {
        toast({
          title: "Sign up successful",
          description: "Welcome to EventMap Croatia!",
        });
      }
    }, 1000);
  };

  const handleGoogleAuth = () => {
    setLoading(true);

    // Simulate Google auth
    setTimeout(() => {
      setLoading(false);
      toast({
        title: "Google Authentication",
        description: "Successfully authenticated with Google",
      });
    }, 1000);
  };

  return (
    <div className="space-y-4 py-2 pb-4">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input 
            id="email" 
            type="email" 
            placeholder="Enter your email" 
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input 
            id="password" 
            type="password" 
            placeholder={mode === 'login' ? 'Enter your password' : 'Create a password'} 
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        {mode === 'login' && (
          <div className="text-right">
            <a 
              href="#" 
              className="text-sm font-medium text-medium-blue hover:underline"
              onClick={(e) => e.preventDefault()}
            >
              Forgot password?
            </a>
          </div>
        )}

        <Button 
          type="submit" 
          className="w-full bg-navy-blue hover:bg-medium-blue"
          disabled={loading}
        >
          {loading ? 'Loading...' : mode === 'login' ? 'Log in' : 'Sign up'}
        </Button>
      </form>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t border-gray-300"></span>
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-white px-2 text-gray-500">Or continue with</span>
        </div>
      </div>

      <Button 
        type="button" 
        variant="outline" 
        className="w-full border-gray-300 hover:bg-gray-50"
        onClick={handleGoogleAuth}
        disabled={loading}
      >
        <Google className="mr-2 h-4 w-4" />
        {mode === 'login' ? 'Log in with Google' : 'Sign up with Google'}
      </Button>

      <div className="text-center text-sm text-gray-500">
        {mode === 'login' ? "Don't have an account? " : "Already have an account? "}
        <a 
          href="#" 
          className="font-semibold text-medium-blue hover:underline"
          onClick={(e) => {
            e.preventDefault();
            onToggleMode();
          }}
        >
          {mode === 'login' ? 'Sign up' : 'Log in'}
        </a>
      </div>
    </div>
  );
};

export default LoginForm;
