import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Loader2, Clock, CheckCircle2, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface SimProgressProps {
  value: number;
  status: 'idle' | 'running' | 'completed' | 'failed' | 'queued' | 'processing';
  className?: string;
}

export function SimProgress({ value, status, className }: SimProgressProps) {
  const getStatusLabel = () => {
    switch (status) {
      case 'queued': return 'Queued';
      case 'processing':
      case 'running': return 'Running';
      case 'completed': return 'Completed';
      case 'failed': return 'Failed';
      default: return 'Idle';
    }
  };

  const getStatusIcon = () => {
    switch (status) {
      case 'queued': return <Clock className="w-4 h-4 text-amber-500" />;
      case 'processing':
      case 'running': return <Loader2 className="w-4 h-4 animate-spin text-blue-500" />;
      case 'completed': return <CheckCircle2 className="w-4 h-4 text-emerald-500" />;
      case 'failed': return <AlertCircle className="w-4 h-4 text-red-500" />;
      default: return null;
    }
  };

  const getBadgeVariant = () => {
    if (status === 'completed') return 'default';
    if (status === 'failed') return 'destructive';
    if (status === 'running' || status === 'processing') return 'outline';
    return 'secondary';
  };

  return (
    <div className={cn("p-6 border rounded-xl bg-card shadow-sm space-y-4", className)}>
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-medium flex items-center gap-2">
          {getStatusIcon()}
          Solver Status
        </h3>
        <Badge variant={getBadgeVariant() as any}>
          {getStatusLabel().toUpperCase()}
        </Badge>
      </div>
      
      <Progress value={value} className="h-2" />
      
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{value}% of perturbations complete</span>
        <span>Estimated time: ~45s</span>
      </div>
    </div>
  );
}
