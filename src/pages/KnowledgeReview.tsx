import React, { useState, useEffect } from 'react';
import { useLayoutStore } from '@/store/layoutStore';
import { Search, Filter, Calendar, Heart, MoreHorizontal, MessageSquare, BarChart2, Share, Trash, Edit, Star, GitMerge, FileText, Loader2 } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';

export default function KnowledgeReview() {
  const { setRightPanelContent, setRightPanelOpen } = useLayoutStore();
  const [notes, setNotes] = useState<any[]>([]);
  const [selectedNote, setSelectedNote] = useState<any>(null);
  const [searchFocused, setSearchFocused] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const fetchNotes = async (query = '') => {
    setIsLoading(true);
    try {
      const endpoint = query 
        ? '/api/v1/search' 
        : '/api/v1/notes?limit=50';
      
      const res = await fetch(endpoint, {
        method: query ? 'POST' : 'GET',
        headers: { 'Content-Type': 'application/json' },
        ...(query && { body: JSON.stringify({ query, limit: 20 }) })
      });
      
      if (!res.ok) throw new Error('Failed to fetch notes');
      const data = await res.json();
      setNotes(data);
      if (data.length > 0 && !selectedNote) {
        setSelectedNote(data[0]);
      }
    } catch (err: any) {
      toast.error('加载笔记失败');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchNotes();
  }, []);

  useEffect(() => {
    const debounce = setTimeout(() => {
      if (searchQuery !== undefined) {
        fetchNotes(searchQuery);
      }
    }, 500);
    return () => clearTimeout(debounce);
  }, [searchQuery]);

  useEffect(() => {
    setRightPanelOpen(false);
    return () => setRightPanelOpen(true);
  }, [setRightPanelOpen]);

  const handleDelete = async (id: string) => {
    if (!confirm('确定删除此笔记？')) return;
    try {
      const res = await fetch(`/api/v1/notes/${id}`, { method: 'DELETE' });
      if (!res.ok) throw new Error('删除失败');
      toast.success('删除成功');
      setNotes(notes.filter(n => n.id !== id));
      if (selectedNote?.id === id) setSelectedNote(null);
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const handleAnalyze = async (type: 'expand' | 'score' | 'roadmap') => {
    if (!selectedNote) return;
    toast.info(`正在生成${type}...`);
    try {
      const res = await fetch(`/api/v1/analyze/${type}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: selectedNote.document })
      });
      if (!res.ok) throw new Error('分析失败');
      const result = await res.json();
      toast.success('分析完成');
      // Just a mock update to trigger re-render or you can update the note in DB
      // In a real app we'd update the note's metadata
    } catch (err: any) {
      toast.error(err.message);
    }
  };

  const parseTags = (tagsStr: string) => {
    if (!tagsStr) return [];
    return tagsStr.split(',').filter(Boolean);
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Top Toolbar */}
      <div className="h-16 border-b border-white/5 flex items-center justify-between px-6 flex-shrink-0 bg-background/50 backdrop-blur-md z-10">
        <div className="flex items-center gap-4 flex-1">
          <div className={cn(
            "flex items-center gap-2 px-3 py-2 rounded-lg border transition-all duration-300 w-96",
            searchFocused ? "border-primary bg-primary/5 shadow-[0_0_15px_rgba(0,212,255,0.1)]" : "border-white/10 bg-white/5"
          )}>
            <Search size={16} className={searchFocused ? "text-primary" : "text-muted-foreground"} />
            <input 
              type="text" 
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="智能搜索知识库..." 
              className="bg-transparent border-none outline-none flex-1 text-sm text-foreground placeholder:text-muted-foreground/50"
              onFocus={() => setSearchFocused(true)}
              onBlur={() => setSearchFocused(false)}
            />
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
            <MessageSquare size={16} className="mr-2" /> 聊天回顾
          </Button>
          <Button variant="ghost" size="sm" className="text-muted-foreground hover:text-foreground">
            <BarChart2 size={16} className="mr-2" /> AI 周报
          </Button>
          <div className="w-px h-4 bg-white/10 mx-2"></div>
          <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground">
            <Filter size={16} />
          </Button>
          <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground">
            <Calendar size={16} />
          </Button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left: Notes List */}
        <div className="w-[360px] border-r border-white/5 flex flex-col bg-card/10">
          <div className="p-4 flex items-center justify-between border-b border-white/5">
            <h2 className="font-semibold text-sm">全部笔记 <span className="text-muted-foreground font-normal">({notes.length})</span></h2>
            <Button variant="ghost" size="icon" className="h-6 w-6">
              <Filter size={14} />
            </Button>
          </div>
          <div className="flex-1 overflow-y-auto p-3 space-y-3">
            {isLoading ? (
              <div className="flex justify-center p-8"><Loader2 className="animate-spin text-primary" /></div>
            ) : notes.length === 0 ? (
              <div className="text-center p-8 text-sm text-muted-foreground">暂无笔记</div>
            ) : (
              notes.map(note => (
                <div 
                  key={note.id}
                  onClick={() => setSelectedNote(note)}
                  className={cn(
                    "p-4 rounded-xl cursor-pointer transition-all duration-200 border",
                    selectedNote?.id === note.id 
                      ? "bg-primary/10 border-primary/30 shadow-[0_4px_20px_-4px_rgba(0,212,255,0.15)]" 
                      : "bg-white/5 border-transparent hover:bg-white/10 hover:-translate-y-0.5 hover:shadow-lg"
                  )}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className={cn("font-medium line-clamp-1", selectedNote?.id === note.id ? "text-primary" : "text-foreground")}>
                      {note.metadata?.title || '无标题'}
                    </h3>
                  </div>
                  <p className="text-xs text-muted-foreground line-clamp-2 mb-3 leading-relaxed">
                    {note.metadata?.summary}
                  </p>
                  <div className="flex items-center justify-between">
                    <div className="flex gap-1.5 flex-wrap">
                      {parseTags(note.metadata?.tags).slice(0,3).map((tag: string) => (
                        <span key={tag} className="px-1.5 py-0.5 rounded text-[10px] bg-white/10 text-muted-foreground">
                          {tag}
                        </span>
                      ))}
                    </div>
                    <span className="text-[10px] text-muted-foreground/60 shrink-0 ml-2">{note.metadata?.created_at?.slice(5, 16) || '刚刚'}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right: Note Detail */}
        <div className="flex-1 overflow-y-auto bg-background">
          {selectedNote ? (
            <div className="max-w-4xl mx-auto p-8 pb-24 animate-in fade-in duration-300">
              {/* Detail Header */}
              <div className="flex items-start justify-between mb-8">
                <div>
                  <div className="flex items-center gap-3 mb-3">
                    <span className="text-sm text-muted-foreground">{selectedNote.metadata?.created_at || '刚刚'}</span>
                    <div className="flex gap-2">
                      {parseTags(selectedNote.metadata?.tags).map((tag: string) => (
                        <span key={tag} className="px-2 py-0.5 rounded-md text-xs bg-primary/10 text-primary border border-primary/20">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                  <h1 className="text-3xl font-bold tracking-tight">{selectedNote.metadata?.title || '无标题'}</h1>
                </div>
                <div className="flex items-center gap-2">
                  <Button variant="ghost" size="icon" className="text-muted-foreground">
                    <Edit size={18} />
                  </Button>
                  <Button variant="ghost" size="icon" className="text-destructive hover:bg-destructive/10" onClick={() => handleDelete(selectedNote.id)}>
                    <Trash size={18} />
                  </Button>
                </div>
              </div>

              {/* Basic Content */}
              <div className="glass-panel p-6 rounded-2xl mb-8">
                <div className="flex items-center gap-2 mb-4 text-foreground font-medium border-b border-white/10 pb-2">
                  <FileText size={18} className="text-primary" />
                  <h2>详细内容</h2>
                </div>
                <div className="prose prose-invert max-w-none text-muted-foreground leading-loose whitespace-pre-wrap">
                  <p>{selectedNote.document}</p>
                </div>
              </div>

              {/* AI Deep Analysis (if available) */}
              {(selectedNote.metadata?.expanded_idea || selectedNote.metadata?.score) ? (
                <div className="grid grid-cols-2 gap-6">
                  {selectedNote.metadata?.expanded_idea && (
                    <div className="glass-panel p-6 rounded-2xl">
                      <div className="flex items-center gap-2 mb-4 text-foreground font-medium">
                        <GitMerge size={18} className="text-purple-400" />
                        <h2>扩展想法 & 路线</h2>
                      </div>
                      <ul className="space-y-3">
                        {selectedNote.metadata.expanded_idea.map((item: string, i: number) => (
                          <li key={i} className="flex items-start gap-3 text-sm text-muted-foreground bg-white/5 p-3 rounded-lg border border-white/5">
                            <span className="w-5 h-5 rounded-full bg-purple-500/20 text-purple-400 flex items-center justify-center flex-shrink-0 text-xs">{i+1}</span>
                            <span className="leading-relaxed">{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {selectedNote.metadata?.score && (
                    <div className="glass-panel p-6 rounded-2xl">
                      <div className="flex items-center gap-2 mb-6 text-foreground font-medium">
                        <BarChart2 size={18} className="text-green-400" />
                        <h2>灵感评分</h2>
                      </div>
                      <div className="space-y-5">
                        {Object.entries({
                          '创新性': selectedNote.metadata.score.innovation,
                          '商业价值': selectedNote.metadata.score.business,
                          '技术难度': selectedNote.metadata.score.technical,
                          '可行性': selectedNote.metadata.score.feasibility,
                        }).map(([label, score]) => (
                          <div key={label} className="space-y-2">
                            <div className="flex justify-between text-xs font-medium">
                              <span className="text-muted-foreground">{label}</span>
                              <span className="text-foreground">{score as number}/100</span>
                            </div>
                            <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-gradient-to-r from-green-500 to-emerald-400 rounded-full"
                                style={{ width: `${score}%` }}
                              ></div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex items-center justify-center p-8 border border-dashed border-white/10 rounded-xl bg-white/5">
                  <div className="text-center space-y-4">
                    <p className="text-sm text-muted-foreground">暂无深度分析数据</p>
                    <div className="flex gap-4 justify-center">
                      <Button variant="outline" size="sm" onClick={() => handleAnalyze('expand')}>生成扩展想法</Button>
                      <Button variant="outline" size="sm" onClick={() => handleAnalyze('score')}>进行灵感评分</Button>
                    </div>
                  </div>
                </div>
              )}

            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              {isLoading ? '加载中...' : '请选择一条笔记查看详情'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
