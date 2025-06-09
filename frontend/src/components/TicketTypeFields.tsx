import React from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";

export interface TicketType {
  name: string;
  description: string;
  price: number;
  currency: string;
  total_quantity: number;
  min_purchase: number;
  max_purchase: number;
}

interface TicketTypeFieldsProps {
  ticket: TicketType;
  index: number;
  errors: Record<string, string>;
  onChange: (index: number, field: keyof TicketType, value: string | number) => void;
  onRemove: () => void;
  removable: boolean;
}

const TicketTypeFields: React.FC<TicketTypeFieldsProps> = ({
  ticket,
  index,
  errors,
  onChange,
  onRemove,
  removable,
}) => (
  <div className="space-y-4 border p-4 rounded-md">
    <div className="flex justify-between items-center">
      <h4 className="font-medium">Ticket Type {index + 1}</h4>
      {removable && (
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={onRemove}
          className="text-red-500 hover:text-red-700"
        >
          <X className="h-4 w-4" />
        </Button>
      )}
    </div>

    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <Label>Ticket Name *</Label>
        <Input
          value={ticket.name}
          onChange={(e) => onChange(index, "name", e.target.value)}
          placeholder="e.g., General Admission, VIP, Student"
          className={errors[`ticket_${index}_name`] ? "border-red-500" : ""}
        />
        {errors[`ticket_${index}_name`] && (
          <p className="text-sm text-red-500 mt-1">{errors[`ticket_${index}_name`]}</p>
        )}
      </div>

      <div>
        <Label>Price (EUR) *</Label>
        <Input
          type="number"
          min="0"
          step="0.01"
          value={ticket.price}
          onChange={(e) => onChange(index, "price", parseFloat(e.target.value) || 0)}
          className={errors[`ticket_${index}_price`] ? "border-red-500" : ""}
        />
        {errors[`ticket_${index}_price`] && (
          <p className="text-sm text-red-500 mt-1">{errors[`ticket_${index}_price`]}</p>
        )}
      </div>
    </div>

    <div>
      <Label>Description (Optional)</Label>
      <Textarea
        value={ticket.description}
        onChange={(e) => onChange(index, "description", e.target.value)}
        placeholder="Describe what's included with this ticket type"
        rows={2}
      />
    </div>

    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div>
        <Label>Total Quantity *</Label>
        <Input
          type="number"
          min="1"
          value={ticket.total_quantity}
          onChange={(e) => onChange(index, "total_quantity", parseInt(e.target.value) || 1)}
          className={errors[`ticket_${index}_quantity`] ? "border-red-500" : ""}
        />
        {errors[`ticket_${index}_quantity`] && (
          <p className="text-sm text-red-500 mt-1">{errors[`ticket_${index}_quantity`]}</p>
        )}
      </div>

      <div>
        <Label>Min Purchase</Label>
        <Input
          type="number"
          min="1"
          value={ticket.min_purchase}
          onChange={(e) => onChange(index, "min_purchase", parseInt(e.target.value) || 1)}
        />
      </div>

      <div>
        <Label>Max Purchase</Label>
        <Input
          type="number"
          min="1"
          value={ticket.max_purchase}
          onChange={(e) => onChange(index, "max_purchase", parseInt(e.target.value) || 10)}
        />
      </div>
    </div>
  </div>
);

export default TicketTypeFields;
