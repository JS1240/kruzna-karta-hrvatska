
import React, { useState } from 'react';
import { useToast } from '@/hooks/use-toast';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Form, FormField, FormItem, FormLabel, FormControl, FormMessage } from '@/components/ui/form';
import { Mail, Key, Github } from 'lucide-react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';

const formSchema = z.object({
  email: z.string().email({ message: 'Please enter a valid email address' }),
  password: z.string().min(6, { message: 'Password must be at least 6 characters' }),
});

type FormValues = z.infer<typeof formSchema>;

interface LoginFormProps {
  mode: 'login' | 'signup';
  onToggleMode: () => void;
  onClose: () => void;
}

const LoginForm = ({ mode, onToggleMode, onClose }: LoginFormProps) => {
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const handleSubmit = async (values: FormValues) => {
    setIsSubmitting(true);
    try {
      // Simulate API call
      await new Promise((resolve) => setTimeout(resolve, 1000));
      
      toast({
        title: mode === 'login' ? 'Logged in successfully!' : 'Account created successfully!',
        description: `Welcome, ${values.email}`,
      });
      
      onClose();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'An error occurred. Please try again.',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleGoogleAuth = async () => {
    setIsSubmitting(true);
    try {
      // Simulate API call for Google auth
      await new Promise((resolve) => setTimeout(resolve, 1000));
      
      toast({
        title: mode === 'login' ? 'Logged in with Google!' : 'Account created with Google!',
        description: 'Authentication successful',
      });
      
      onClose();
    } catch (error) {
      toast({
        title: 'Error',
        description: 'An error occurred with Google authentication',
        variant: 'destructive',
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6 py-4">
      <div className="space-y-2 text-center">
        <h3 className="text-2xl font-bold">
          {mode === 'login' ? 'Welcome back' : 'Create an account'}
        </h3>
        <p className="text-sm text-gray-500">
          {mode === 'login' 
            ? 'Enter your credentials to access your account' 
            : 'Enter your details to create your account'}
        </p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(handleSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input 
                      {...field} 
                      placeholder="your@email.com" 
                      type="email"
                      className="pl-10"
                    />
                  </div>
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
                  <div className="relative">
                    <Key className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
                    <Input 
                      {...field} 
                      type="password" 
                      placeholder="••••••••" 
                      className="pl-10"
                    />
                  </div>
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          
          <Button 
            type="submit" 
            className="w-full" 
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <span>Loading...</span>
            ) : mode === 'login' ? (
              'Log in'
            ) : (
              'Sign up'
            )}
          </Button>
        </form>
      </Form>
      
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <span className="w-full border-t" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-background px-2 text-muted-foreground">
            Or continue with
          </span>
        </div>
      </div>
      
      <Button 
        variant="outline" 
        type="button" 
        className="w-full"
        onClick={handleGoogleAuth}
        disabled={isSubmitting}
      >
        <Github className="mr-2 h-4 w-4" />
        {mode === 'login' ? 'Login with Github' : 'Sign up with Github'}
      </Button>
      
      <div className="text-center text-sm">
        {mode === 'login' ? (
          <>
            Don't have an account?{' '}
            <Button variant="link" className="p-0" onClick={onToggleMode}>
              Sign up
            </Button>
          </>
        ) : (
          <>
            Already have an account?{' '}
            <Button variant="link" className="p-0" onClick={onToggleMode}>
              Log in
            </Button>
          </>
        )}
      </div>
    </div>
  );
};

export default LoginForm;
