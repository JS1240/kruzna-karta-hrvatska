
import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { zodResolver } from '@hookform/resolvers/zod';
import { useForm } from 'react-hook-form';
import * as z from 'zod';
import { Separator } from '@/components/ui/separator';
import { Github } from 'lucide-react';
import { toast } from '@/hooks/use-toast';

interface LoginFormProps {
  mode: 'login' | 'signup';
  onToggleMode: () => void;
  onClose: () => void;
  onLoginSuccess: () => void;
}

const loginSchema = z.object({
  email: z.string().email({ message: 'Please enter a valid email address' }),
  password: z.string().min(6, { message: 'Password must be at least 6 characters' }),
});

const LoginForm = ({ mode, onToggleMode, onClose, onLoginSuccess }: LoginFormProps) => {
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<z.infer<typeof loginSchema>>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const onSubmit = async (values: z.infer<typeof loginSchema>) => {
    setIsLoading(true);
    
    try {
      // Simulate API call with timeout
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Mock successful authentication
      console.log('Authentication values:', values);
      
      toast({
        title: mode === 'login' ? 'Login Successful' : 'Account Created',
        description: mode === 'login' 
          ? 'Welcome back to EventMap Croatia!' 
          : 'Your account has been created successfully.',
      });
      
      onLoginSuccess();
    } catch (error) {
      console.error('Authentication error:', error);
      toast({
        title: 'Authentication Failed',
        description: 'There was a problem with your login attempt.',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setIsLoading(true);
    
    try {
      // Simulate API call with timeout
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      toast({
        title: 'Google Authentication',
        description: 'Successfully authenticated with Google',
      });
      
      onLoginSuccess();
    } catch (error) {
      console.error('Google authentication error:', error);
      toast({
        title: 'Authentication Failed',
        description: 'There was a problem with your Google login attempt.',
        variant: 'destructive',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="text-center">
        <h2 className="text-2xl font-bold">
          {mode === 'login' ? 'Login to your account' : 'Create an account'}
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          {mode === 'login' 
            ? 'Enter your credentials to access your account' 
            : 'Fill out the form to create your account'}
        </p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input placeholder="your.email@example.com" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          
          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Password</FormLabel>
                <FormControl>
                  <Input type="password" placeholder="******" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          
          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading ? 'Loading...' : mode === 'login' ? 'Login' : 'Sign Up'}
          </Button>
        </form>
      </Form>
      
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <Separator className="w-full" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-background px-2 text-muted-foreground">
            Or continue with
          </span>
        </div>
      </div>
      
      <Button 
        variant="outline" 
        className="w-full" 
        onClick={handleGoogleLogin}
        disabled={isLoading}
      >
        <Github className="mr-2 h-4 w-4" />
        {mode === 'login' ? 'Login with Google' : 'Sign up with Google'}
      </Button>
      
      <div className="text-center">
        <Button variant="link" onClick={onToggleMode}>
          {mode === 'login' 
            ? "Don't have an account? Sign up" 
            : 'Already have an account? Login'}
        </Button>
      </div>
    </div>
  );
};

export default LoginForm;
