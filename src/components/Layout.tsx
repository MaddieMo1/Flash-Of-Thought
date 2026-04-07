import React, { useEffect } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Lightbulb, 
  BrainCircuit, 
  Network, 
  Bookmark, 
  Settings, 
  History,
  Bot,
  ChevronRight,
  ChevronLeft
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useLayoutStore } from '@/store/layoutStore';

export function Layout() {
  const { rightPanelOpen, rightPanelContent, rightPanelTitle, setRightPanelOpen } = useLayoutStore();
  const location = useLocation();

  // Ensure right panel resets or hides when navigating (optional, handled by page)

  const mainNavItems = [
    { name: '录入想法', path: '/dashboard/record', icon: Lightbulb },
    { name: '知识回顾', path: '/dashboard/review', icon: BrainCircuit },
    { name: '知识图谱', path: '/dashboard/graph', icon: Network },
  ];

  const auxNavItems = [
    { name: '收藏', path: '/dashboard/favorites', icon: Bookmark },
    { name: '历史记录', path: '/dashboard/history', icon: History },
    { name: '设置', path: '/dashboard/settings', icon: Settings },
  ];

  return (
    <div className="flex h-screen w-full overflow-hidden bg-background text-foreground">
      {/* Left Sidebar */}
      <aside className="w-[200px] flex-shrink-0 flex flex-col border-r border-white/5 bg-card/30 backdrop-blur-xl">
        <div className="p-6">
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-blue-400">
            FlashOfThought
          </h1>
        </div>
        
        <nav className="flex-1 px-3 py-4 space-y-8">
          <div className="space-y-1">
            <div className="px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              核心功能
            </div>
            {mainNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname.startsWith(item.path);
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                    isActive 
                      ? "bg-primary/10 text-primary shadow-[inset_0_1px_0_rgba(255,255,255,0.1)]" 
                      : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
                  )}
                >
                  <Icon size={18} className={cn(isActive && "text-primary")} />
                  {item.name}
                </NavLink>
              );
            })}
          </div>

          <div className="space-y-1">
            <div className="px-3 text-xs font-semibold text-muted-foreground uppercase tracking-wider mb-2">
              辅助功能
            </div>
            {auxNavItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname.startsWith(item.path);
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                    isActive 
                      ? "bg-primary/10 text-primary" 
                      : "text-muted-foreground hover:bg-white/5 hover:text-foreground"
                  )}
                >
                  <Icon size={18} />
                  {item.name}
                </NavLink>
              );
            })}
          </div>
        </nav>
        
        {/* User Profile Snippet */}
        <div className="p-4 border-t border-white/5">
          <div className="flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-white/5 cursor-pointer transition-colors">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-bold">
              U
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">User</p>
              <p className="text-xs text-muted-foreground truncate">user@example.com</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col relative min-w-0 bg-[#0A0A0B] overflow-hidden">
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            transition={{ duration: 0.2 }}
            className="flex-1 flex flex-col overflow-hidden"
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
      </main>

      {/* Right AI Panel */}
      <aside 
        className={cn(
          "flex-shrink-0 flex flex-col border-l border-white/5 bg-card/30 backdrop-blur-xl transition-all duration-300 relative",
          rightPanelOpen ? "w-[300px]" : "w-0 border-l-0"
        )}
      >
        <button 
          onClick={() => setRightPanelOpen(!rightPanelOpen)}
          className="absolute -left-3 top-1/2 -translate-y-1/2 w-6 h-12 bg-card border border-white/10 rounded-full flex items-center justify-center text-muted-foreground hover:text-foreground z-10 shadow-lg"
        >
          {rightPanelOpen ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
        </button>

        {rightPanelOpen && (
          <div className="flex-1 flex flex-col w-[300px] overflow-hidden">
            <div className="h-14 border-b border-white/5 flex items-center px-4 gap-2">
              <Bot className="text-primary" size={18} />
              <span className="font-medium text-sm">{rightPanelTitle}</span>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {rightPanelContent ? rightPanelContent : (
                <div className="p-4 rounded-xl bg-white/5 border border-white/5 text-sm text-muted-foreground">
                  我在这里随时准备帮您整理思路。
                </div>
              )}
            </div>
          </div>
        )}
      </aside>
    </div>
  );
}
