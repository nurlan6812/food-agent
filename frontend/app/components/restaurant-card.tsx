'use client';

import { MapPin, Phone, Utensils } from 'lucide-react';
import { Card, CardContent } from '@/components/ui/card';
import type { RestaurantCardInfo } from '@/lib/types';

interface RestaurantCardProps {
  restaurant: RestaurantCardInfo;
}

export function RestaurantCard({ restaurant }: RestaurantCardProps) {
  return (
    <Card className="overflow-hidden border-primary/20">
      <CardContent className="p-0">
        <div className="p-4 space-y-3">
          <div>
            <h3 className="font-bold text-lg text-foreground text-balance">
              {restaurant.name}
            </h3>
            {restaurant.category && (
              <div className="flex items-center gap-2 mt-1">
                <Utensils className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm text-muted-foreground">{restaurant.category}</span>
              </div>
            )}
          </div>

          <div className="space-y-2 pt-2 border-t border-border">
            {restaurant.address && (
              <div className="flex items-start gap-2">
                <MapPin className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                <span className="text-sm text-foreground">{restaurant.address}</span>
              </div>
            )}
            {restaurant.phone && (
              <div className="flex items-center gap-2">
                <Phone className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                <span className="text-sm text-foreground">{restaurant.phone}</span>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
