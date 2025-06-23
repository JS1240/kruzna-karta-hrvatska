import React, { useState } from "react";
import { Button } from "./ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "./ui/form";
import { Input } from "./ui/input";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import * as z from "zod";
import { Separator } from "./ui/separator";
import { logger } from "../lib/logger";
import { FcGoogle } from "react-icons/fc";
import { toast } from "../hooks/use-toast";
import { login, signup, googleLogin, sendPasswordReset } from "../lib/auth";

interface LoginFormProps {
  mode: "login" | "signup" | "reset";
  onToggleMode: () => void;
  onClose: () => void;
  onLoginSuccess: () => void;
  onModeChange: (mode: "login" | "signup" | "reset") => void;
}

const loginSchema = z.object({
  email: z.string().email({ message: "Please enter a valid email address" }),
  password: z
    .string()
    .min(6, { message: "Password must be at least 6 characters" }),
});

const signupSchema = z.object({
  email: z.string().email({ message: "Please enter a valid email address" }),
  password: z
    .string()
    .min(6, { message: "Password must be at least 6 characters" }),
  name: z.string().min(2, { message: "Name must be at least 2 characters" }),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

const resetSchema = z.object({
  email: z.string().email({ message: "Please enter a valid email address" }),
});

const LoginForm = ({
  mode,
  onToggleMode,
  onClose,
  onLoginSuccess,
  onModeChange,
}: LoginFormProps) => {
  const [isLoading, setIsLoading] = useState(false);

  const getSchema = () => {
    switch (mode) {
      case 'signup': return signupSchema;
      case 'reset': return resetSchema;
      default: return loginSchema;
    }
  };

  const getDefaultValues = () => {
    switch (mode) {
      case 'signup': return { email: "", password: "", name: "", confirmPassword: "" };
      case 'reset': return { email: "" };
      default: return { email: "", password: "" };
    }
  };

  const form = useForm({
    resolver: zodResolver(getSchema()),
    defaultValues: getDefaultValues(),
  });

  // Reset form when mode changes
  React.useEffect(() => {
    form.reset(getDefaultValues());
  }, [mode]);

  const onSubmit = async (values: any) => {
    setIsLoading(true);
    try {
      if (mode === "signup") {
        await signup(values.email, values.password, values.name);
        toast({
          title: "Account Created",
          description: "Your account has been created successfully. Please check your email to verify your account.",
        });
        onLoginSuccess();
      } else if (mode === "reset") {
        await sendPasswordReset(values.email);
        toast({
          title: "Reset Email Sent",
          description: "Please check your email for password reset instructions.",
        });
        onModeChange("login");
      } else {
        await login(values.email, values.password);
        toast({
          title: "Login Successful",
          description: "Welcome back to EventMap Croatia!",
        });
        onLoginSuccess();
      }
    } catch (error: unknown) {
      logger.error("Authentication error:", error);
      const errorMessage =
        error instanceof Error
          ? error.message
          : "There was a problem with your request.";
      toast({
        title: "Authentication Failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setIsLoading(true);
    try {
      const user = await googleLogin();
      toast({
        title: "Google Authentication",
        description: `Welcome, ${user.name || user.email}!`,
      });
      onLoginSuccess();
    } catch (error: unknown) {
      logger.error("Google authentication error:", error);
      const errorMessage =
        error instanceof Error
          ? error.message
          : "There was a problem with your Google login attempt.";
      toast({
        title: "Authentication Failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="text-center">
        <h2 className="text-2xl font-bold">
          {mode === "login" && "Login to your account"}
          {mode === "signup" && "Create an account"}
          {mode === "reset" && "Reset your password"}
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          {mode === "login" && "Enter your credentials to access your account"}
          {mode === "signup" && "Fill out the form to create your account"}
          {mode === "reset" && "Enter your email to receive reset instructions"}
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

          {mode === "signup" && (
            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Name</FormLabel>
                  <FormControl>
                    <Input placeholder="Your full name" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          )}

          {mode !== "reset" && (
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
          )}

          {mode === "signup" && (
            <FormField
              control={form.control}
              name="confirmPassword"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Confirm Password</FormLabel>
                  <FormControl>
                    <Input type="password" placeholder="******" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
          )}

          {mode === "login" && (
            <div className="text-right">
              <Button 
                type="button" 
                variant="link" 
                className="p-0 h-auto text-sm"
                onClick={() => onModeChange("reset")}
              >
                Forgot password?
              </Button>
            </div>
          )}

          <Button type="submit" className="w-full" disabled={isLoading}>
            {isLoading && "Loading..."}
            {!isLoading && mode === "login" && "Login"}
            {!isLoading && mode === "signup" && "Sign Up"}
            {!isLoading && mode === "reset" && "Send Reset Email"}
          </Button>
        </form>
      </Form>

      {mode !== "reset" && (
        <>
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
            <FcGoogle className="mr-2 h-5 w-5" />
            {mode === "login" ? "Login with Google" : "Sign up with Google"}
          </Button>
        </>
      )}

      <div className="text-center">
        {mode === "login" && (
          <Button variant="link" onClick={() => onModeChange("signup")}>
            Don't have an account? Sign up
          </Button>
        )}
        {mode === "signup" && (
          <Button variant="link" onClick={() => onModeChange("login")}>
            Already have an account? Login
          </Button>
        )}
        {mode === "reset" && (
          <Button variant="link" onClick={() => onModeChange("login")}>
            Back to login
          </Button>
        )}
      </div>
    </div>
  );
};

export default LoginForm;
