import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLayoutStore } from '@/store/layoutStore';
import { Layers, Box, ZoomIn, ZoomOut, Filter, Search, Loader2 } from 'lucide-react';
import ForceGraph2D from 'react-force-graph-2d';
import ForceGraph3D from 'react-force-graph-3d';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

export default function KnowledgeGraph() {
  const { setRightPanelOpen } = useLayoutStore();
  const [is3D, setIs3D] = useState(false);
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const [isLoading, setIsLoading] = useState(true);
  const containerRef = useRef<HTMLDivElement>(null);
  const fgRef = useRef<any>();

  useEffect(() => {
    setRightPanelOpen(false);
    return () => setRightPanelOpen(true);
  }, [setRightPanelOpen]);

  useEffect(() => {
    const fetchGraphData = async () => {
      setIsLoading(true);
      try {
        const res = await fetch('/api/v1/graph');
        if (!res.ok) throw new Error('Failed to fetch graph data');
        const data = await res.json();
        // Map the backend data format to react-force-graph format
        setGraphData({
          nodes: data.nodes || [],
          links: data.edges || [] // react-force-graph expects 'links' instead of 'edges'
        });
      } catch (err: any) {
        toast.error('加载图谱数据失败');
        setGraphData({ nodes: [], links: [] });
      } finally {
        setIsLoading(false);
      }
    };
    fetchGraphData();
  }, []);

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        setDimensions({
          width: containerRef.current.clientWidth,
          height: containerRef.current.clientHeight
        });
      }
    };
    
    updateDimensions();
    window.addEventListener('resize', updateDimensions);
    return () => window.removeEventListener('resize', updateDimensions);
  }, []);

  const handleZoomIn = useCallback(() => {
    if (fgRef.current) {
      if (is3D) {
        const distance = fgRef.current.cameraPosition().z;
        fgRef.current.cameraPosition({ z: distance * 0.8 }, null, 500);
      } else {
        fgRef.current.zoom(fgRef.current.zoom() * 1.2, 500);
      }
    }
  }, [is3D]);

  const handleZoomOut = useCallback(() => {
    if (fgRef.current) {
      if (is3D) {
        const distance = fgRef.current.cameraPosition().z;
        fgRef.current.cameraPosition({ z: distance * 1.2 }, null, 500);
      } else {
        fgRef.current.zoom(fgRef.current.zoom() * 0.8, 500);
      }
    }
  }, [is3D]);

  return (
    <div className="flex-1 relative overflow-hidden bg-black" ref={containerRef}>
      
      {/* Floating Control Panel */}
      <div className="absolute top-6 left-6 z-10 w-64 glass-panel rounded-2xl p-4 flex flex-col gap-4">
        <h2 className="text-sm font-bold tracking-wider uppercase text-muted-foreground mb-1">视图控制</h2>
        
        <div className="flex items-center gap-2 bg-white/5 p-1 rounded-lg">
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => setIs3D(false)}
            className={`flex-1 rounded-md text-xs h-8 ${!is3D ? 'bg-primary/20 text-primary hover:bg-primary/30' : 'text-muted-foreground'}`}
          >
            <Layers size={14} className="mr-2" /> 2D
          </Button>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => setIs3D(true)}
            className={`flex-1 rounded-md text-xs h-8 ${is3D ? 'bg-primary/20 text-primary hover:bg-primary/30' : 'text-muted-foreground'}`}
          >
            <Box size={14} className="mr-2" /> 3D
          </Button>
        </div>

        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" />
          <input 
            type="text" 
            placeholder="搜索节点..." 
            className="w-full bg-white/5 border border-white/10 rounded-lg pl-9 pr-3 py-1.5 text-xs text-foreground placeholder:text-muted-foreground/50 focus:outline-none focus:border-primary/50"
          />
        </div>

        <div className="flex items-center justify-between mt-2">
          <Button variant="ghost" size="icon" className="h-8 w-8 bg-white/5 border border-white/10 hover:bg-white/10" onClick={handleZoomIn}>
            <ZoomIn size={14} />
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8 bg-white/5 border border-white/10 hover:bg-white/10" onClick={handleZoomOut}>
            <ZoomOut size={14} />
          </Button>
          <Button variant="ghost" size="icon" className="h-8 w-8 bg-white/5 border border-white/10 hover:bg-white/10">
            <Filter size={14} />
          </Button>
        </div>
      </div>

      {/* Legend */}
      <div className="absolute bottom-6 left-6 z-10 glass-panel rounded-xl p-4">
        <h3 className="text-xs font-semibold text-muted-foreground mb-3 uppercase">图例</h3>
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs text-foreground">
            <span className="w-2.5 h-2.5 rounded-full bg-[#FF6A3D]"></span> 核心 Idea
          </div>
          <div className="flex items-center gap-2 text-xs text-foreground">
            <span className="w-2.5 h-2.5 rounded-full bg-[#A0E0FF]"></span> 笔记节点
          </div>
          <div className="flex items-center gap-2 text-xs text-foreground">
            <span className="w-2.5 h-2.5 rounded-full bg-[#BD00FF]"></span> 标签节点
          </div>
        </div>
      </div>

      {/* Graph Area */}
      <div className="w-full h-full flex items-center justify-center opacity-80 mix-blend-screen">
        {isLoading ? (
          <div className="flex flex-col items-center text-primary/50 gap-4">
            <Loader2 className="animate-spin" size={32} />
            <p className="text-sm">正在构建知识星系...</p>
          </div>
        ) : is3D ? (
          <ForceGraph3D
            ref={fgRef}
            width={dimensions.width}
            height={dimensions.height}
            graphData={graphData}
            nodeLabel="label"
            nodeColor="color"
            nodeVal="size"
            nodeRelSize={6}
            linkColor={() => 'rgba(255,255,255,0.1)'}
            backgroundColor="#0A0A0B"
          />
        ) : (
          <ForceGraph2D
            ref={fgRef}
            width={dimensions.width}
            height={dimensions.height}
            graphData={graphData}
            nodeLabel="label"
            nodeColor="color"
            nodeVal="size"
            nodeRelSize={6}
            linkColor={() => 'rgba(255,255,255,0.1)'}
            backgroundColor="#0A0A0B"
            linkDirectionalParticles={2}
            linkDirectionalParticleSpeed={0.005}
          />
        )}
      </div>
    </div>
  );
}
