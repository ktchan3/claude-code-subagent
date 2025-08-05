'use client';

import React from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Mail } from 'lucide-react';

interface UserProfileCardProps {
  /** The user's full name */
  name: string;
  /** The user's job title or role */
  role: string;
  /** Optional avatar image URL */
  avatarUrl?: string;
  /** Optional email address (currently unused but available for future features) */
  email?: string;
  /** Callback function when contact button is clicked */
  onContact?: () => void;
  /** Optional CSS class name for custom styling */
  className?: string;
}

export function UserProfileCard({
  name,
  role,
  avatarUrl,
  email,
  onContact,
  className,
}: UserProfileCardProps) {
  const initials = React.useMemo(() => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  }, [name]);

  return (
    <Card className={`w-full max-w-sm overflow-hidden transition-all duration-200 hover:shadow-lg focus-within:ring-2 focus-within:ring-blue-500 focus-within:ring-offset-2 ${className || ''}`}>
      <div className="relative h-24 sm:h-32 bg-gradient-to-br from-blue-500 to-purple-600" />
      <CardContent className="relative px-4 pb-6 sm:px-6">
        <div className="flex flex-col items-center -mt-12 sm:-mt-16">
          <Avatar className="h-24 w-24 sm:h-32 sm:w-32 border-4 border-white shadow-xl">
            <AvatarImage 
              src={avatarUrl} 
              alt={`${name}'s profile picture`}
              loading="lazy"
            />
            <AvatarFallback 
              className="text-lg sm:text-2xl font-semibold bg-gradient-to-br from-blue-500 to-purple-600 text-white"
              aria-label={`${name}'s initials`}
            >
              {initials}
            </AvatarFallback>
          </Avatar>
          
          <div className="mt-3 sm:mt-4 text-center">
            <h3 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white">
              {name}
            </h3>
            <p className="text-sm sm:text-base text-gray-600 dark:text-gray-400 mt-1">
              {role}
            </p>
          </div>

          {onContact && (
            <Button
              onClick={onContact}
              className="mt-4 sm:mt-6 w-full sm:w-auto min-h-[44px]"
              size="lg"
              aria-label={`Contact ${name}`}
            >
              <Mail className="mr-2 h-4 w-4" aria-hidden="true" />
              Contact
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}