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
import { FcGoogle } from "react-icons/fc";
import { toast } from "../hooks/use-toast";
import { login, signup, googleLogin } from "../lib/auth";
import { debugError } from "../lib/debug";

interface LoginFormProps {
  mode: "login" | "signup";
  onToggleMode: () => void;
  onClose: () => void;
  onLoginSuccess: () => void;
}

const loginSchema = z.object({
  email: z.string().email({ message: "Please enter a valid email address" }),
  password: z
    .string()
    .min(6, { message: "Password must be at least 6 characters" }),
});

const LoginForm = ({
  mode,
  onToggleMode,
  onClose,
  onLoginSuccess,
}: LoginFormProps) => {
  const [isLoading, setIsLoading] = useState(false);

  const form = useForm<z.infer<typeof loginSchema>>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: "",
      password: "",
    },
  });

  const onSubmit = async (values: z.infer<typeof loginSchema>) => {
    setIsLoading(true);
    try {
      if (mode === "signup") {
        await signup(values.email, values.password);
        toast({
          title: "Account Created",
          description: "Your account has been created successfully.",
        });
      } else {
        await login(values.email, values.password);
        toast({
          title: "Login Successful",
          description: "Welcome back to EventMap Croatia!",
        });
      }
      onLoginSuccess();
    } catch (error: unknown) {
      debugError("Authentication error:", error);
      const errorMessage =
        error instanceof Error
          ? error.message
          : "There was a problem with your login attempt.";
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
      debugError("Google authentication error:", error);
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
          {mode === "login" ? "Login to your account" : "Create an account"}
        </h2>
        <p className="text-sm text-gray-500 mt-1">
          {mode === "login"
            ? "Enter your credentials to access your account"
            : "Fill out the form to create your account"}
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
            {isLoading ? "Loading..." : mode === "login" ? "Login" : "Sign Up"}
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
        <FcGoogle className="mr-2 h-5 w-5" />
        {mode === "login" ? "Login with Google" : "Sign up with Google"}
      </Button>

      <div className="text-center">
        <Button variant="link" onClick={onToggleMode}>
          {mode === "login"
            ? "Don't have an account? Sign up"
            : "Already have an account? Login"}
        </Button>
      </div>
    </div>
  );
};

export default LoginForm;
