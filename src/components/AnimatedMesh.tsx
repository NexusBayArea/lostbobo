import { useEffect, useRef } from 'react';
import { useTheme } from '@/hooks/useTheme';

export function AnimatedMesh() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const themeContext = useTheme();
  const theme = themeContext?.theme ?? 'light';
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      canvas.width = canvas.offsetWidth * dpr;
      canvas.height = canvas.offsetHeight * dpr;
      ctx.scale(dpr, dpr);
    };
    resize();
    window.addEventListener('resize', resize);

    // Mesh parameters
    const rows = 12;
    const cols = 16;
    const nodes: { x: number; y: number; baseX: number; baseY: number; phase: number }[] = [];
    
    // Initialize nodes
    const cellWidth = canvas.offsetWidth / (cols - 1);
    const cellHeight = canvas.offsetHeight / (rows - 1);
    
    for (let row = 0; row < rows; row++) {
      for (let col = 0; col < cols; col++) {
        nodes.push({
          x: col * cellWidth,
          y: row * cellHeight,
          baseX: col * cellWidth,
          baseY: row * cellHeight,
          phase: Math.random() * Math.PI * 2,
        });
      }
    }

    let time = 0;

    const animate = () => {
      time += 0.008;
      
      ctx.clearRect(0, 0, canvas.offsetWidth, canvas.offsetHeight);

      // Update node positions with gentle wave motion
      nodes.forEach((node, i) => {
        const row = Math.floor(i / cols);
        const col = i % cols;
        
        // Skip edge nodes to keep mesh anchored
        if (row > 0 && row < rows - 1 && col > 0 && col < cols - 1) {
          node.x = node.baseX + Math.sin(time + node.phase) * 8;
          node.y = node.baseY + Math.cos(time + node.phase * 0.7) * 6;
        }
      });

      // Draw mesh lines
      const isDark = theme === 'dark';
      const lineColor = isDark ? 'rgba(148, 163, 184, 0.15)' : 'rgba(71, 85, 105, 0.12)';
      const nodeColor = isDark ? 'rgba(96, 165, 250, 0.4)' : 'rgba(59, 130, 246, 0.35)';

      ctx.strokeStyle = lineColor;
      ctx.lineWidth = 1;

      // Draw horizontal lines
      for (let row = 0; row < rows; row++) {
        ctx.beginPath();
        for (let col = 0; col < cols; col++) {
          const node = nodes[row * cols + col];
          if (col === 0) {
            ctx.moveTo(node.x, node.y);
          } else {
            ctx.lineTo(node.x, node.y);
          }
        }
        ctx.stroke();
      }

      // Draw vertical lines
      for (let col = 0; col < cols; col++) {
        ctx.beginPath();
        for (let row = 0; row < rows; row++) {
          const node = nodes[row * cols + col];
          if (row === 0) {
            ctx.moveTo(node.x, node.y);
          } else {
            ctx.lineTo(node.x, node.y);
          }
        }
        ctx.stroke();
      }

      // Draw diagonal lines (for triangular mesh look)
      for (let row = 0; row < rows - 1; row++) {
        for (let col = 0; col < cols - 1; col++) {
          const node1 = nodes[row * cols + col];
          const node2 = nodes[(row + 1) * cols + (col + 1)];
          ctx.beginPath();
          ctx.moveTo(node1.x, node1.y);
          ctx.lineTo(node2.x, node2.y);
          ctx.stroke();
        }
      }

      // Draw nodes
      nodes.forEach((node, i) => {
        const row = Math.floor(i / cols);
        const col = i % cols;
        
        // Only draw some nodes for cleaner look
        if ((row + col) % 2 === 0) {
          ctx.beginPath();
          ctx.arc(node.x, node.y, 2.5, 0, Math.PI * 2);
          ctx.fillStyle = nodeColor;
          ctx.fill();
        }
      });

      // Add thermal gradient overlay
      const gradient = ctx.createRadialGradient(
        canvas.offsetWidth * 0.7,
        canvas.offsetHeight * 0.3,
        0,
        canvas.offsetWidth * 0.7,
        canvas.offsetHeight * 0.3,
        canvas.offsetWidth * 0.5
      );
      
      if (isDark) {
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.08)');
        gradient.addColorStop(0.5, 'rgba(139, 92, 246, 0.04)');
        gradient.addColorStop(1, 'transparent');
      } else {
        gradient.addColorStop(0, 'rgba(59, 130, 246, 0.06)');
        gradient.addColorStop(0.5, 'rgba(139, 92, 246, 0.03)');
        gradient.addColorStop(1, 'transparent');
      }
      
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, canvas.offsetWidth, canvas.offsetHeight);

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', resize);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [theme]);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full"
      style={{ opacity: 0.8 }}
    />
  );
}
