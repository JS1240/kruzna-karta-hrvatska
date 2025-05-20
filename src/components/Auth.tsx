
import React, { useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { UserCircle } from 'lucide-react';
import LoginForm from './LoginForm';

const Auth = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [mode, setMode] = useState<'login' | 'signup'>('login');

  const handleToggleMode = () => {
    setMode(mode === 'login' ? 'signup' : 'login');
  };

  const handleClose = () => {
    setIsOpen(false);
  };

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogTrigger asChild>
        <Button variant="ghost" className="gap-2">
          <UserCircle className="h-5 w-5" />
          <span>{mode === 'login' ? 'Login' : 'Sign up'}</span>
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <LoginForm 
          mode={mode} 
          onToggleMode={handleToggleMode} 
          onClose={handleClose}
        />
      </DialogContent>
    </Dialog>
  );
};

export default Auth;
