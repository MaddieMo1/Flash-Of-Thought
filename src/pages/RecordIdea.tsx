import React, { useEffect, useState, useRef } from 'react';
import { useLayoutStore } from '@/store/layoutStore';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Mic, FileText, Upload, Zap, Sparkles, Send, Square, Loader2, Save, Trash2, BrainCircuit, Target, Lightbulb, ChevronRight } from 'lucide-react';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

export default function RecordIdea() {
  const { setRightPanelContent, setRightPanelOpen } = useLayoutStore();
  const [textInput, setTextInput] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [processedNote, setProcessedNote] = useState<any>(null);
  const [sourceUrl, setSourceUrl] = useState<string>('');
  const [relatedNotes, setRelatedNotes] = useState<any[]>([]);
  const [quickCommand, setQuickCommand] = useState('');
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  const fetchWithTimeout = async (url: string, options: RequestInit, timeoutMs = 45000) => {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);
    try {
      return await fetch(url, { ...options, signal: controller.signal });
    } finally {
      clearTimeout(timer);
    }
  };

  const fetchRelatedNotes = async (text: string) => {
    try {
      const res = await fetch('/api/v1/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: text, limit: 3 })
      });
      if (res.ok) {
        const data = await res.json();
        setRelatedNotes(data.results || []);
      }
    } catch (e) {
      console.error('Failed to fetch related notes:', e);
    }
  };

  const handleProcess = async (text: string, srcUrl: string = '') => {
    if (!text.trim()) return;
    
    setIsProcessing(true);
    setSourceUrl(srcUrl);
    toast.info('正在由 AI 整理您的想法...');
    
    try {
      const processRes = await fetchWithTimeout('/api/v1/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: text })
      }, 60000);
      
      if (!processRes.ok) throw new Error('处理失败');
      const noteStructure = await processRes.json();
      
      setProcessedNote(noteStructure);
      setTextInput(text);
      toast.success('AI整理完成！请查看并保存。');
      
      // 异步获取相关笔记
      fetchRelatedNotes(noteStructure.summary || text);
      
    } catch (err: any) {
      if (err?.name === 'AbortError') {
        toast.error('请求超时，请稍后重试');
      } else {
        toast.error(err.message || '操作失败，请重试');
      }
    } finally {
      setIsProcessing(false);
    }
  };

  const handleConfirmSave = async () => {
    if (!processedNote || !textInput.trim()) return;
    
    setIsSaving(true);
    try {
      const saveRes = await fetchWithTimeout('/api/v1/save', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          note: processedNote,
          raw_text: textInput,
          source_url: sourceUrl
        })
      }, 30000);

      if (!saveRes.ok) throw new Error('保存失败');
      
      toast.success('已保存到知识库！');
      handleDiscard();
    } catch (err: any) {
      toast.error(err.message || '保存失败，请重试');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDiscard = () => {
    setProcessedNote(null);
    setTextInput('');
    setSourceUrl('');
    setRelatedNotes([]);
  };

  const handleSave = () => {
    if (!textInput.trim()) {
      toast.error('请输入内容');
      return;
    }
    handleProcess(textInput);
  };

  const handleFileUpload = async (file: File) => {
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);

    setIsProcessing(true);
    toast.info('正在上传并转写音频...');

    try {
      const res = await fetch('/api/v1/upload', {
        method: 'POST',
        body: formData,
      });
      
      if (!res.ok) throw new Error('上传或转写失败');
      const data = await res.json();
      
      await handleProcess(data.raw_text, data.file_url);
    } catch (err: any) {
      toast.error(err.message || '上传处理失败');
      setIsProcessing(false);
    }
  };

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFileUpload(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFileUpload(file);
  };

  const handleVoiceRecord = async () => {
    if (!isRecording) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        audioChunksRef.current = [];

        mediaRecorder.ondataavailable = (e) => {
          if (e.data.size > 0) audioChunksRef.current.push(e.data);
        };

        mediaRecorder.onstop = async () => {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
          const file = new File([audioBlob], `recording_${Date.now()}.wav`, { type: 'audio/wav' });
          await handleFileUpload(file);
        };

        mediaRecorder.start();
        setIsRecording(true);
        setRecordingTime(0);
      } catch (err) {
        toast.error('无法访问麦克风，请检查权限');
      }
    } else {
      mediaRecorderRef.current?.stop();
      setIsRecording(false);
      mediaRecorderRef.current?.stream.getTracks().forEach(track => track.stop());
    }
  };

  const handleQuickCommand = async (cmdText?: string) => {
    const cmd = cmdText || quickCommand;
    if (!cmd.trim()) return;

    let content = cmd;
    if (cmd.startsWith('闪念') || cmd.startsWith('记录')) {
      content = cmd.replace(/^(闪念|记录)/, '').replace(/^[，,。.]+/, '');
    }

    const contextText = textInput.trim() 
      ? `指令: ${content}\n内容上下文: ${textInput}`
      : content;

    toast.info(`执行指令: ${content}`);
    await handleProcess(contextText);
    setQuickCommand('');
  };

  useEffect(() => {
    setRightPanelOpen(false);
    setRightPanelContent(null);
  }, [setRightPanelContent, setRightPanelOpen]);

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isRecording) {
      interval = setInterval(() => setRecordingTime(t => t + 1), 1000);
    }
    return () => clearInterval(interval);
  }, [isRecording]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60).toString().padStart(2, '0');
    const s = (seconds % 60).toString().padStart(2, '0');
    return `${m}:${s}`;
  };

  return (
    <div className="flex-1 overflow-y-auto bg-[radial-gradient(circle_at_top_left,rgba(0,212,255,0.08),transparent_55%),radial-gradient(circle_at_80%_0%,rgba(99,102,241,0.08),transparent_40%),linear-gradient(180deg,#05080f_0%,#080c16_100%)]">
      <div className="mx-auto w-full max-w-6xl p-8 space-y-6">
        <h1 className="text-5xl md:text-6xl font-black tracking-tight text-white mb-8">记录你的灵感</h1>
        
        {processedNote ? (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* 左侧主展示区 */}
            <div className="lg:col-span-2 space-y-6">
              <div className="rounded-2xl border border-white/10 bg-[#0a1019]/85 p-8 shadow-[0_12px_60px_rgba(0,0,0,0.45)] backdrop-blur">
                <div className="space-y-6">
                  {/* 标题与标签 */}
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-3 flex items-center gap-2">
                      <FileText className="text-primary" />
                      {processedNote.title}
                    </h2>
                    <div className="flex flex-wrap gap-2">
                      {processedNote.tags?.map((tag: string, i: number) => (
                        <span key={i} className="px-2.5 py-1 text-xs rounded-md bg-white/5 text-white/60 border border-white/10">
                          #{tag}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* 核心摘要 (类似 st.info) */}
                  <div className="rounded-xl border border-primary/20 bg-primary/10 px-5 py-4 flex gap-3">
                    <Lightbulb className="text-primary shrink-0 mt-0.5" size={20} />
                    <div className="space-y-1">
                      <h4 className="text-sm font-semibold text-primary">核心摘要</h4>
                      <p className="text-sm text-white/80 leading-relaxed">
                        {processedNote.summary}
                      </p>
                    </div>
                  </div>

                  {/* 双列明细 */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-4 border-t border-white/5">
                    <div className="space-y-4">
                      <div className="flex items-center gap-2 text-white">
                        <Target className="text-rose-400" size={18} />
                        <h4 className="font-semibold">核心观点</h4>
                      </div>
                      <ul className="space-y-2">
                        {processedNote.core_ideas?.map((idea: string, i: number) => (
                          <li key={i} className="text-sm text-white/70 flex items-start gap-2">
                            <span className="text-white/30 mt-1">•</span>
                            <span className="leading-relaxed">{idea}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div className="space-y-4">
                      <div className="flex items-center gap-2 text-white">
                        <BrainCircuit className="text-indigo-400" size={18} />
                        <h4 className="font-semibold">可能应用</h4>
                      </div>
                      <ul className="space-y-2">
                        {processedNote.possible_applications?.map((app: string, i: number) => (
                          <li key={i} className="text-sm text-white/70 flex items-start gap-2">
                            <span className="text-white/30 mt-1">•</span>
                            <span className="leading-relaxed">{app}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              {/* 底部操作按钮 */}
              <div className="flex gap-4">
                <Button 
                  onClick={handleConfirmSave} 
                  disabled={isSaving}
                  className="h-12 flex-1 rounded-xl bg-primary text-base font-semibold text-primary-foreground shadow-[0_0_30px_rgba(0,212,255,0.25)] hover:bg-primary/90"
                >
                  {isSaving ? <Loader2 className="mr-2 animate-spin" /> : <Save className="mr-2" size={18} />}
                  保存到知识库
                </Button>
                <Button 
                  onClick={handleDiscard}
                  disabled={isSaving}
                  variant="outline"
                  className="h-12 px-8 rounded-xl border-white/10 bg-white/5 text-white/70 hover:bg-white/10 hover:text-white"
                >
                  <Trash2 className="mr-2" size={18} />
                  放弃并清除
                </Button>
              </div>
            </div>

            {/* 右侧第二大脑关联区 */}
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-lg font-bold text-white">
                <BrainCircuit className="text-pink-400" />
                第二大脑关联
              </div>
              <div className="rounded-xl border border-white/10 bg-[#0a1019]/85 p-4 shadow-lg backdrop-blur">
                <p className="text-sm text-emerald-400 mb-4">发现相关想法：</p>
                {relatedNotes.length > 0 ? (
                  <div className="space-y-2">
                    {relatedNotes.map((note, idx) => (
                      <div key={idx} className="group rounded-lg border border-white/5 bg-white/5 p-3 transition-colors hover:bg-white/10 cursor-pointer">
                        <div className="flex items-center gap-2 text-sm text-white/90">
                          <ChevronRight size={14} className="text-white/40" />
                          <span className="truncate">{note.title || '无标题笔记'}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-sm text-white/40 py-4 text-center border border-dashed border-white/10 rounded-lg">
                    暂未发现强关联笔记
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="rounded-2xl border border-white/10 bg-[#0a1019]/85 p-6 shadow-[0_12px_60px_rgba(0,0,0,0.45)] backdrop-blur animate-in fade-in duration-300">
            <Tabs defaultValue="file" className="w-full flex-col gap-0">
            <div className="border-b border-white/10 pb-3">
              <TabsList variant="line" className="h-auto gap-2 bg-transparent p-0">
                <TabsTrigger value="file" className="rounded-none border-none px-1 py-2 text-base data-[state=active]:text-primary">
                  <Upload size={15} className="mr-1.5" /> 上传文件
                </TabsTrigger>
                <TabsTrigger value="voice" className="rounded-none border-none px-1 py-2 text-base data-[state=active]:text-primary">
                  <Mic size={15} className="mr-1.5" /> 麦克风录音
                </TabsTrigger>
                <TabsTrigger value="text" className="rounded-none border-none px-1 py-2 text-base data-[state=active]:text-primary">
                  <FileText size={15} className="mr-1.5" /> 文字输入
                </TabsTrigger>
                <TabsTrigger value="quick" className="rounded-none border-none px-1 py-2 text-base data-[state=active]:text-primary">
                  <Zap size={15} className="mr-1.5" /> 语音指令
                </TabsTrigger>
              </TabsList>
            </div>

            <div className="pt-6">
              <TabsContent value="file" className="mt-0">
                <div className="space-y-3">
                  <p className="text-sm text-white/75">拖拽或选择音频文件</p>
                  <div 
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className={cn(
                      "flex items-center justify-between gap-4 rounded-xl border px-4 py-5 transition-all",
                      isDragging 
                        ? "border-primary/50 bg-primary/5 shadow-[0_0_15px_rgba(0,212,255,0.15)]" 
                        : "border-white/10 bg-[#121824]"
                    )}
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-white/10 bg-white/5 text-primary">
                        <Upload size={18} />
                      </div>
                      <div>
                        <p className="text-lg font-medium text-white">Drag and drop file here</p>
                        <p className="text-sm text-white/50">Limit 200MB per file • MP3, WAV, M4A, AAC</p>
                      </div>
                    </div>
                    <input 
                      type="file" 
                      ref={fileInputRef} 
                      onChange={onFileChange} 
                      className="hidden" 
                      accept="audio/*" 
                    />
                    <Button 
                      onClick={() => fileInputRef.current?.click()}
                      disabled={isProcessing}
                      className="h-10 rounded-lg border border-white/20 bg-white/5 px-5 text-white hover:bg-white/10"
                    >
                      Browse files
                    </Button>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="voice" className="mt-0">
                <div className="space-y-4">
                  <div className="rounded-xl border border-white/10 bg-[#121824] px-4 py-3 text-primary">
                    {isProcessing ? '正在处理音频...' : (isRecording ? '正在录音，点击按钮结束' : '请点击下方麦克风按钮开始录音')}
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-white/80">录制语音</p>
                    <div className="flex items-center gap-4 rounded-xl border border-white/10 bg-[#121824] px-4 py-4">
                      <button
                        onClick={handleVoiceRecord}
                        disabled={isProcessing}
                        className={cn(
                          "flex h-11 w-11 items-center justify-center rounded-full border transition-all disabled:opacity-50",
                          isRecording
                            ? "border-rose-400/60 bg-rose-500/20 text-rose-300"
                            : "border-white/20 bg-white/5 text-white/80 hover:bg-white/10"
                        )}
                      >
                        {isRecording ? <Square size={16} fill="currentColor" /> : <Mic size={18} />}
                      </button>
                      <div className="h-px flex-1 bg-[radial-gradient(circle,rgba(255,255,255,0.4)_1px,transparent_1px)] bg-[length:8px_1px] bg-repeat-x" />
                      <span className="w-14 text-right font-mono text-white/70">{formatTime(recordingTime)}</span>
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="text" className="mt-0">
                <div className="space-y-4">
                  <div className="flex items-center justify-between text-sm text-white/60">
                    <p>直接输入文字想法，AI将为您自动整理</p>
                    <span>{textInput.length} 字</span>
                  </div>
                  <Textarea
                    value={textInput}
                    onChange={(e) => setTextInput(e.target.value)}
                    placeholder="输入想法..."
                    className="min-h-[220px] resize-none rounded-xl border border-white/10 bg-[#121824] text-base leading-7 text-white placeholder:text-white/35 focus-visible:ring-primary/50"
                  />
                  <Button
                    onClick={handleSave}
                    disabled={isProcessing || !textInput.trim()}
                    className="h-11 rounded-xl bg-primary px-6 text-[15px] font-semibold text-primary-foreground shadow-[0_0_30px_rgba(0,212,255,0.25)] hover:bg-primary/90"
                  >
                    {isProcessing ? (
                      <>
                        <Loader2 className="mr-2 animate-spin" size={16} />
                        处理中
                      </>
                    ) : (
                      <>
                        开始整理（文字）
                        <Send size={15} className="ml-2" />
                      </>
                    )}
                  </Button>
                </div>
              </TabsContent>

              <TabsContent value="quick" className="mt-0">
                <div className="space-y-4">
                  <div className="rounded-xl border border-primary/20 bg-primary/5 px-4 py-3 text-sm text-white/80">
                    说一句指令，让 AI 快速处理最近输入内容
                  </div>
                  <div className="relative">
                    <input
                      type="text"
                      value={quickCommand}
                      onChange={(e) => setQuickCommand(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') handleQuickCommand();
                      }}
                      placeholder="例如：帮我提炼三个执行动作"
                      className="h-12 w-full rounded-xl border border-white/10 bg-[#121824] px-4 pr-12 text-[15px] text-white outline-none transition focus:border-primary/40 focus:ring-2 focus:ring-primary/30"
                    />
                    <button 
                      onClick={() => handleQuickCommand()}
                      disabled={isProcessing || !quickCommand.trim()}
                      className="absolute right-2 top-1/2 -translate-y-1/2 rounded-lg p-1.5 text-white/50 hover:bg-white/10 hover:text-white disabled:opacity-50"
                    >
                      {isProcessing ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {['@整理会议纪要', '@提炼核心观点', '@生成待办事项'].map((cmd) => (
                      <button 
                        key={cmd} 
                        onClick={() => handleQuickCommand(cmd)}
                        disabled={isProcessing}
                        className="rounded-md border border-white/15 bg-white/5 px-3 py-1.5 text-sm text-white/80 hover:bg-white/10 disabled:opacity-50"
                      >
                        {cmd}
                      </button>
                    ))}
                  </div>
                </div>
              </TabsContent>
            </div>
          </Tabs>
        </div>
        )}
      </div>
    </div>
  );
}
