import { create } from 'zustand';
import React from 'react';

interface LayoutState {
  rightPanelOpen: boolean;
  rightPanelContent: React.ReactNode | null;
  rightPanelTitle: string;
  setRightPanelOpen: (open: boolean) => void;
  setRightPanelContent: (content: React.ReactNode | null, title?: string) => void;
}

export const useLayoutStore = create<LayoutState>((set) => ({
  rightPanelOpen: true,
  rightPanelContent: null,
  rightPanelTitle: 'AI 辅助面板',
  setRightPanelOpen: (open) => set({ rightPanelOpen: open }),
  setRightPanelContent: (content, title = 'AI 辅助面板') => set({ rightPanelContent: content, rightPanelTitle: title }),
}));
