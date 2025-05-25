"use client";

import React, { useState, useRef, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Mic,
  MicOff,
  Phone,
  PhoneOff,
  Volume2,
  VolumeX,
  Loader2,
  Bot,
  User,
  Pause,
  Play,
  Trash2,
  RotateCcw,
  Settings,
} from "lucide-react";
import { formatTime } from "@/lib/utils";
import {
  cleanTextForSpeech,
  hasThinkTags,
  extractThinkContent,
} from "@/lib/text-utils";
import Navigation from "@/components/ui/navigation";
import VoiceListenerWS from "@/components/ui/wake-word-listener-ws";

interface VoiceMessage {
  id: string;
  content: string;
  isUser: boolean;
  timestamp: Date;
  duration?: number;
  audioUrl?: string;
  recognizedText?: string; // 添加识别的文本字段
}

type CallState =
  | "idle"
  | "connecting"
  | "connected"
  | "speaking"
  | "listening"
  | "processing";

export default function VoiceChatPage() {
  const [messages, setMessages] = useState<VoiceMessage[]>([]);
  const [callState, setCallState] = useState<CallState>("idle");
  const [isRecording, setIsRecording] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isAIPlaying, setIsAIPlaying] = useState(false);
  const [currentTranscript, setCurrentTranscript] = useState("");
  const [audioLevel, setAudioLevel] = useState(0);
  const [funAudioAvailable, setFunAudioAvailable] = useState(false);
  const [sessionId, setSessionId] = useState("default");
  const [conversationRounds, setConversationRounds] = useState(0);
  const [serviceStatus, setServiceStatus] = useState<any>(null);
  const [showConversationHistory, setShowConversationHistory] = useState(false); // 控制对话记录显示

  // 唤醒词相关状态
  const [wakeWordEnabled, setWakeWordEnabled] = useState(true);
  const [wakeWordDetected, setWakeWordDetected] = useState(false);
  const [lastWakeWord, setLastWakeWord] = useState("");

  // WebSocket模式状态（现在只使用WebSocket）
  const [voiceChatResponses, setVoiceChatResponses] = useState<any[]>([]); // 存储语音对话响应

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioStreamRef = useRef<MediaStream | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const silenceTimerRef = useRef<NodeJS.Timeout | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // 滚动到底部
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // 检查FunAudioLLM服务状态
  const checkFunAudioStatus = useCallback(async () => {
    try {
      console.log("🔍 检查FunAudioLLM服务状态...");
      const response = await fetch("/api/voice/engine");
      if (response.ok) {
        const data = await response.json();
        console.log("📊 服务响应:", data);
        setFunAudioAvailable(data.engine.status.available);
        setServiceStatus(data.engine.status);

        if (data.engine.status.available) {
          console.log("✅ FunAudioLLM语音服务可用");
          console.log("📊 服务状态:", data.engine.status);
          console.log("🌟 功能特性:", data.engine.features);
          return;
        }
      }
      console.log("⚠️ FunAudioLLM语音服务不可用，回退到Web Speech API");
      setFunAudioAvailable(false);
    } catch (error) {
      console.error("❌ 检查服务状态失败:", error);
      setFunAudioAvailable(false);
    }
  }, []);

  // 请求麦克风权限
  const requestMicrophonePermission = useCallback(async () => {
    try {
      console.log("🎤 请求麦克风权限...");
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      console.log("✅ 麦克风权限已获得");

      // 测试音频流
      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();
      source.connect(analyser);

      console.log("✅ 音频流测试成功");

      // 清理测试资源
      stream.getTracks().forEach((track) => track.stop());
      audioContext.close();

      return true;
    } catch (error) {
      console.error("❌ 麦克风权限请求失败:", error);
      alert(
        '请允许麦克风权限以使用语音功能。请在浏览器地址栏左侧点击麦克风图标，选择"允许"。'
      );
      return false;
    }
  }, []);

  useEffect(() => {
    const initializeVoiceFeatures = async () => {
      console.log("🚀 初始化语音功能...");

      // 1. 检查服务状态
      await checkFunAudioStatus();

      // 2. 请求麦克风权限
      await requestMicrophonePermission();

      // 3. 生成唯一的会话ID
      setSessionId(`voice-chat-${Date.now()}`);

      console.log("✅ 语音功能初始化完成");
    };

    initializeVoiceFeatures();
  }, [checkFunAudioStatus, requestMicrophonePermission]);

  // 处理用户语音输入
  const handleUserSpeech = useCallback(
    async (transcript: string, audioBlob?: Blob) => {
      if (!transcript.trim() && !audioBlob) return;

      setCurrentTranscript("");
      setCallState("processing");

      // 停止AI播放（如果正在播放）
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        setIsAIPlaying(false);
      }

      let userMessage: VoiceMessage;
      let aiResponse = "";

      try {
        // 优先使用FunAudioLLM的完整流程
        if (funAudioAvailable && audioBlob) {
          console.log("🎯 使用FunAudioLLM流程：高性能语音识别 + 智能对话");

          const formData = new FormData();
          formData.append("audio", audioBlob, "voice.wav");
          formData.append("session_id", sessionId);
          formData.append("language", "auto");

          const response = await fetch("/api/voice/chat", {
            method: "POST",
            body: formData,
          });

          if (response.ok) {
            const result = await response.json();

            if (result.success) {
              userMessage = {
                id: Date.now().toString(),
                content: result.recognized_text || "[语音输入]",
                isUser: true,
                timestamp: new Date(),
                recognizedText: result.recognized_text,
              };

              aiResponse = result.response;
              setConversationRounds(result.history_length || 0);

              console.log("✅ FunAudioLLM语音对话成功");
              console.log(`📊 对话轮数: ${result.history_length}`);
              console.log(`🎤 识别引擎: ${result.engine}`);
              console.log(`💭 情感信息: ${JSON.stringify(result.emotion)}`);
            } else {
              // 检查是否是"未识别到有效语音内容"
              const errorMsg = result.error || "";
              if (errorMsg.includes("未识别到有效语音内容")) {
                console.log("🔇 未检测到语音内容，自动结束通话");
                // 立即结束通话
                endCall();
                return;
              } else {
                throw new Error(result.error || "FunAudioLLM对话失败");
              }
            }
          } else {
            throw new Error("FunAudioLLM服务请求失败");
          }
        } else if (transcript.trim()) {
          // 回退到传统的文本对话流程
          console.log("💬 使用传统文本对话流程");

          userMessage = {
            id: Date.now().toString(),
            content: transcript,
            isUser: true,
            timestamp: new Date(),
          };

          // 发送到AI进行处理
          const response = await fetch("/api/chat/stream", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              message: transcript,
              history: [], // 可以后续添加历史记录
              temperature: 0.7,
              max_tokens: 200,
            }),
          });

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }

          // 处理流式响应
          const reader = response.body?.getReader();
          if (reader) {
            const decoder = new TextDecoder();
            let buffer = "";

            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              const chunk = decoder.decode(value, { stream: true });
              buffer += chunk;

              const lines = buffer.split("\n");
              buffer = lines.pop() || "";

              for (const line of lines) {
                if (line.trim() === "") continue;

                if (line.startsWith("data: ")) {
                  const data = line.slice(6).trim();

                  if (data === "[DONE]") {
                    break;
                  }

                  try {
                    const event = JSON.parse(data);
                    if (event.type === "content" && event.content) {
                      aiResponse += event.content;
                    }
                  } catch (e) {
                    // 忽略解析错误
                  }
                }
              }
            }
          }
        } else {
          throw new Error("无有效输入");
        }

        // 添加用户消息
        setMessages((prev) => [...prev, userMessage]);

        if (aiResponse) {
          const aiMessage: VoiceMessage = {
            id: Date.now().toString(),
            content: aiResponse,
            isUser: false,
            timestamp: new Date(),
          };

          setMessages((prev) => [...prev, aiMessage]);

          // 将AI回复转换为语音
          await speakText(aiResponse);
        }
      } catch (error) {
        console.error("❌ 处理语音失败:", error);

        // 添加用户消息（如果还没添加）
        if (!userMessage!) {
          userMessage = {
            id: Date.now().toString(),
            content: transcript || "[语音输入]",
            isUser: true,
            timestamp: new Date(),
          };
          setMessages((prev) => [...prev, userMessage]);
        }

        const errorMessage: VoiceMessage = {
          id: Date.now().toString(),
          content: "抱歉，处理您的语音时出现了问题。请稍后重试。",
          isUser: false,
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, errorMessage]);
      }

      setCallState("connected");
    },
    [funAudioAvailable, sessionId]
  );

  // 初始化录音（用于FunAudioLLM）
  const initRecording = useCallback(async () => {
    try {
      if (!audioStreamRef.current) {
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
        });
        audioStreamRef.current = stream;
      }

      // 创建MediaRecorder
      const mediaRecorder = new MediaRecorder(audioStreamRef.current, {
        mimeType: "audio/webm;codecs=opus",
      });

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        console.log("🎤 录音结束，处理音频数据");

        if (audioChunksRef.current.length > 0) {
          const audioBlob = new Blob(audioChunksRef.current, {
            type: "audio/webm",
          });

          // 验证音频数据
          if (audioBlob.size < 1000) {
            // 至少1KB
            console.warn("⚠️ 音频数据太小，跳过处理:", audioBlob.size, "bytes");
            // 清空录音数据并重新开始录音
            audioChunksRef.current = [];
            setTimeout(() => {
              // 检查录音器是否可用且AI没在说话
              if (
                mediaRecorderRef.current &&
                mediaRecorderRef.current.state === "inactive" &&
                !document.hidden
              ) {
                startRecording();
              }
            }, 500);
            return;
          }

          console.log("📊 音频数据大小:", audioBlob.size, "bytes");

          // 将webm转换为wav格式（如果需要）
          const wavBlob = await convertToWav(audioBlob);

          // 发送给多模态服务处理
          await handleUserSpeech("", wavBlob);
        } else {
          console.warn("⚠️ 没有录音数据");
          // 重新开始录音
          setTimeout(() => {
            if (
              mediaRecorderRef.current &&
              mediaRecorderRef.current.state === "inactive" &&
              !document.hidden
            ) {
              startRecording();
            }
          }, 500);
        }

        // 清空录音数据
        audioChunksRef.current = [];

        // 如果通话还在进行，开始新的录音
        if (callState === "connected" && !isAIPlaying) {
          setTimeout(() => {
            startRecording();
          }, 500);
        }
      };

      console.log("✅ 录音器初始化完成");
    } catch (error) {
      console.error("❌ 录音初始化失败:", error);
      alert("录音初始化失败，请检查麦克风权限");
    }
  }, [callState, isAIPlaying, handleUserSpeech]);

  // 开始录音
  const startRecording = useCallback(() => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state === "inactive"
    ) {
      console.log("🎤 开始录音");
      setCallState("listening");
      mediaRecorderRef.current.start();
      setIsRecording(true);

      // 设置录音时长限制（比如10秒）
      setTimeout(() => {
        if (
          mediaRecorderRef.current &&
          mediaRecorderRef.current.state === "recording"
        ) {
          stopRecording();
        }
      }, 10000);
    }
  }, []);

  // 停止录音
  const stopRecording = useCallback(() => {
    if (
      mediaRecorderRef.current &&
      mediaRecorderRef.current.state === "recording"
    ) {
      console.log("🔇 停止录音");
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setCallState("processing");
    }
  }, []);

  // 音频格式转换（webm转wav）
  const convertToWav = async (webmBlob: Blob): Promise<Blob> => {
    // 这里可以使用Web Audio API进行格式转换
    // 为了简化，直接返回原始blob
    // 实际应用中可能需要更复杂的转换逻辑
    return webmBlob;
  };

  // 初始化音频分析器
  const initAudioAnalyser = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });

      audioStreamRef.current = stream;

      const audioContext = new AudioContext();
      const analyser = audioContext.createAnalyser();
      const microphone = audioContext.createMediaStreamSource(stream);

      analyser.fftSize = 256;
      microphone.connect(analyser);

      audioContextRef.current = audioContext;
      analyserRef.current = analyser;

      // 开始音频级别监测
      const updateAudioLevel = () => {
        if (analyserRef.current && callState === "connected") {
          const dataArray = new Uint8Array(
            analyserRef.current.frequencyBinCount
          );
          analyserRef.current.getByteFrequencyData(dataArray);

          const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
          setAudioLevel(average);

          requestAnimationFrame(updateAudioLevel);
        }
      };
      updateAudioLevel();
    } catch (error) {
      console.error("❌ 音频初始化失败:", error);
    }
  }, [callState]);

  // 文本转语音
  const speakText = async (text: string) => {
    try {
      // 清理文本，移除think标签和表情符号等不适合语音的内容
      const cleanedText = cleanTextForSpeech(text);

      console.log("🔊 开始语音合成:", cleanedText.substring(0, 50) + "...");

      // 如果清理后的文本为空，则不进行语音合成
      if (!cleanedText.trim()) {
        console.warn("⚠️ 清理后的文本为空，跳过语音合成");
        setIsAIPlaying(false);
        setCallState("connected");
        return;
      }

      // 检查原文本是否包含think标签（用于调试）
      if (hasThinkTags(text)) {
        const thinkContent = extractThinkContent(text);
        console.log("🤔 检测到思考过程标签，已过滤:", thinkContent);
      }

      setIsAIPlaying(true);
      setCallState("speaking");

      try {
        // 使用后端TTS API进行语音合成
        const response = await fetch("/api/voice/speech/synthesize", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            text: cleanedText,
            voice: "zh-CN-XiaoxiaoNeural",
            rate: 0.9,
            pitch: 1.1,
          }),
        });

        if (response.ok) {
          const audioBuffer = await response.arrayBuffer();
          const audioBlob = new Blob([audioBuffer], { type: "audio/wav" });
          const audioUrl = URL.createObjectURL(audioBlob);

          const audio = new Audio(audioUrl);
          audio.volume = isMuted ? 0 : 0.8;

          audio.onplay = () => {
            console.log("✅ AI语音播放开始");
          };

          audio.onended = () => {
            console.log("✅ AI语音播放结束");
            setIsAIPlaying(false);
            setCallState("connected");
            URL.revokeObjectURL(audioUrl);

            // 语音播放结束后，重新开始录音
            setTimeout(() => {
              if (funAudioAvailable) {
                startRecording();
              }
            }, 500);
          };

          audio.onerror = (event) => {
            console.error("❌ 音频播放错误:", event);
            setIsAIPlaying(false);
            setCallState("connected");
            URL.revokeObjectURL(audioUrl);
          };

          await audio.play();
        } else {
          console.warn("⚠️ 后端TTS服务不可用，跳过语音合成");
          setIsAIPlaying(false);
          setCallState("connected");
        }
      } catch (error) {
        console.error("❌ TTS API调用失败:", error);
        setIsAIPlaying(false);
        setCallState("connected");
      }
    } catch (error) {
      console.error("❌ 语音合成失败:", error);
      setIsAIPlaying(false);
      setCallState("connected");
    }
  };

  // 开始通话
  const startCall = async () => {
    // 检查FunAudioLLM语音功能可用性
    if (!funAudioAvailable) {
      console.log("⚠️ 检测到FunAudioLLM服务不可用，尝试重新检查状态...");

      // 重新检查服务状态
      await refreshServiceStatus();

      // 等待状态更新
      await new Promise((resolve) => setTimeout(resolve, 1000));
    }

    try {
      setCallState("connecting");

      await initAudioAnalyser();

      // 使用FunAudioLLM录音模式
      console.log("🎤 启动FunAudioLLM录音模式");
      await initRecording();

      setCallState("connected");

      // 开始录音
      setTimeout(() => {
        startRecording();
      }, 1000);

      // 不添加欢迎消息，直接开始监听
      setMessages([]);
    } catch (error) {
      console.error("❌ 开始通话失败:", error);
      setCallState("idle");
      alert("开始通话失败，请检查麦克风权限并重试");
    }
  };

  // 结束通话
  const endCall = () => {
    setCallState("idle");
    setIsRecording(false);
    setIsAIPlaying(false);
    setCurrentTranscript("");

    // 停止音频流
    if (audioStreamRef.current) {
      audioStreamRef.current.getTracks().forEach((track) => track.stop());
    }

    // 关闭音频上下文
    if (audioContextRef.current) {
      audioContextRef.current.close();
    }

    // 停止当前播放的音频
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
    }
  };

  // 清除对话历史
  const clearConversationHistory = async () => {
    try {
      const response = await fetch(`/api/voice/conversation/${sessionId}`, {
        method: "DELETE",
      });

      if (response.ok) {
        setMessages([]);
        setConversationRounds(0);
        console.log("✅ 对话历史已清除");
      } else {
        console.error("❌ 清除对话历史失败");
      }
    } catch (error) {
      console.error("❌ 清除对话历史错误:", error);
    }
  };

  // 重新开始会话
  const restartSession = () => {
    setSessionId(`voice-chat-${Date.now()}`);
    setMessages([]);
    setConversationRounds(0);
    console.log("🔄 会话已重新开始");
  };

  // 切换静音
  const toggleMute = () => {
    setIsMuted(!isMuted);
    // 如果正在播放，停止当前音频
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      setIsAIPlaying(false);
    }
  };

  // 中断AI说话
  const interruptAI = () => {
    if (isAIPlaying) {
      // 停止当前音频播放
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
      }
      setIsAIPlaying(false);
      setCallState("connected");

      // 重新开始监听
      if (funAudioAvailable) {
        setTimeout(() => {
          startRecording();
        }, 500);
      }
    }
  };

  // 获取状态显示文本
  const getStatusText = () => {
    switch (callState) {
      case "idle":
        return "未连接";
      case "connecting":
        return "正在连接...";
      case "connected":
        return "已连接";
      case "listening":
        return "正在听您说话...";
      case "speaking":
        return "AI正在回复...";
      case "processing":
        return "正在处理...";
      default:
        return "未知状态";
    }
  };

  // 获取状态颜色
  const getStatusColor = () => {
    switch (callState) {
      case "idle":
        return "secondary";
      case "connecting":
        return "default";
      case "connected":
        return "default";
      case "listening":
        return "default";
      case "speaking":
        return "default";
      case "processing":
        return "default";
      default:
        return "secondary";
    }
  };

  // 刷新服务状态
  const refreshServiceStatus = useCallback(async () => {
    console.log("🔄 刷新FunAudioLLM服务状态...");
    await checkFunAudioStatus();
  }, [checkFunAudioStatus]);

  // 处理唤醒词检测
  const handleWakeWordDetected = useCallback(
    async (detectedWord: string, confidence: number) => {
      console.log(`🎯 检测到唤醒词: ${detectedWord}, 置信度: ${confidence}`);
      setWakeWordDetected(true);
      setLastWakeWord(detectedWord);

      // 播放确认音效（简单的beep音）
      try {
        const audioContext = new AudioContext();
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);

        oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
        oscillator.frequency.setValueAtTime(
          1000,
          audioContext.currentTime + 0.1
        );

        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(
          0.01,
          audioContext.currentTime + 0.3
        );

        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.3);
      } catch (error) {
        console.warn("播放唤醒音效失败:", error);
      }

      // 自动开始语音通话
      if (callState === "idle") {
        console.log("🚀 唤醒词触发，自动开始语音通话");

        // 唤醒成功说明服务可用，重新检查状态确保最新
        await refreshServiceStatus();

        // 等待状态更新完成
        setTimeout(async () => {
          await startCall();
        }, 500);
      }

      // 重置唤醒状态
      setTimeout(() => {
        setWakeWordDetected(false);
      }, 3000);
    },
    [callState, startCall, refreshServiceStatus]
  );

  // 处理唤醒词检测错误
  const handleWakeWordError = useCallback((error: string) => {
    console.error("❌ 唤醒词检测错误:", error);
    // 可以在这里显示错误提示
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <div className="container mx-auto p-4">
        <Navigation />
        <div className="max-w-3xl mx-auto space-y-6">
          {/* 唤醒词监听组件 */}
          <VoiceListenerWS
            onWakeWordDetected={handleWakeWordDetected}
            onError={handleWakeWordError}
            enabled={wakeWordEnabled}
            config={{
              wake_words: ["小智小智", "小智", "智能助手", "hey xiaozhi"],
              confidence_threshold: 0.6,
              audio_chunk_duration: 1500,
              silence_timeout: 3000,
              wake_up_message: "我在，请说话",
            }}
          />

          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Phone className="h-5 w-5" />
                  AI语音通话
                </CardTitle>
                <div className="flex items-center gap-2">
                  <Badge variant={getStatusColor() as any}>
                    {getStatusText()}
                  </Badge>
                  {callState === "connected" && (
                    <div className="flex items-center gap-1">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                      <span className="text-sm text-muted-foreground">
                        在线
                      </span>
                    </div>
                  )}
                  {conversationRounds > 0 && (
                    <Badge variant="outline" className="text-xs">
                      {conversationRounds}轮
                    </Badge>
                  )}
                  {funAudioAvailable && (
                    <Badge variant="default" className="text-xs bg-blue-600">
                      FunAudioLLM
                    </Badge>
                  )}
                  {!funAudioAvailable && (
                    <Badge variant="destructive" className="text-xs">
                      语音不可用
                    </Badge>
                  )}
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-6">
              {/* 通话控制区域 */}
              <div className="flex justify-center">
                <div className="flex items-center gap-4">
                  {callState === "idle" ? (
                    <>
                      <Button
                        onClick={startCall}
                        size="lg"
                        className="rounded-full w-16 h-16 bg-green-600 hover:bg-green-700"
                        disabled={!funAudioAvailable}
                      >
                        <Phone className="h-6 w-6" />
                      </Button>

                      {/* 会话管理 */}
                      <div className="flex flex-col items-center gap-2">
                        <span className="text-xs text-muted-foreground">
                          会话管理
                        </span>
                        <div className="flex gap-1">
                          <Button
                            onClick={clearConversationHistory}
                            variant="outline"
                            size="sm"
                            className="text-xs px-2 py-1"
                            disabled={messages.length === 0}
                          >
                            <Trash2 className="h-3 w-3 mr-1" />
                            清除历史
                          </Button>
                          <Button
                            onClick={restartSession}
                            variant="outline"
                            size="sm"
                            className="text-xs px-2 py-1"
                          >
                            <RotateCcw className="h-3 w-3 mr-1" />
                            新会话
                          </Button>
                        </div>
                      </div>
                    </>
                  ) : (
                    <>
                      {/* 结束通话 */}
                      <Button
                        onClick={endCall}
                        size="lg"
                        variant="destructive"
                        className="rounded-full w-16 h-16"
                      >
                        <PhoneOff className="h-6 w-6" />
                      </Button>

                      {/* 静音控制 */}
                      <Button
                        onClick={toggleMute}
                        size="lg"
                        variant={isMuted ? "destructive" : "outline"}
                        className="rounded-full w-12 h-12"
                      >
                        {isMuted ? (
                          <VolumeX className="h-5 w-5" />
                        ) : (
                          <Volume2 className="h-5 w-5" />
                        )}
                      </Button>

                      {/* 中断AI */}
                      {isAIPlaying && (
                        <Button
                          onClick={interruptAI}
                          size="lg"
                          variant="outline"
                          className="rounded-full w-12 h-12"
                        >
                          <Pause className="h-5 w-5" />
                        </Button>
                      )}
                    </>
                  )}
                </div>
              </div>

              {/* 音频级别指示器 */}
              {callState === "connected" && (
                <div className="flex justify-center">
                  <div className="flex items-center gap-1">
                    {[...Array(10)].map((_, i) => (
                      <div
                        key={i}
                        className={`w-1 h-8 rounded-full transition-all duration-100 ${
                          audioLevel > i * 25 ? "bg-blue-500" : "bg-gray-300"
                        }`}
                      />
                    ))}
                  </div>
                </div>
              )}

              {/* 当前识别文本 */}
              {currentTranscript && (
                <Card className="bg-blue-50 dark:bg-blue-950/20 border-blue-200 dark:border-blue-800">
                  <CardContent className="p-3">
                    <div className="flex items-center gap-2">
                      <Mic className="h-4 w-4 text-blue-600 animate-pulse" />
                      <span className="text-sm text-blue-800 dark:text-blue-200">
                        正在识别: {currentTranscript}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* 对话历史 - 只在通话结束后显示 */}
              {callState === "idle" && messages.length > 0 && (
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-lg">对话记录</CardTitle>
                      {conversationRounds > 0 && (
                        <Badge variant="outline">
                          {conversationRounds} 轮对话
                        </Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    <ScrollArea className="h-96">
                      <div className="space-y-4">
                        {messages.length === 0 ? (
                          <div className="text-center text-muted-foreground py-8">
                            点击通话按钮开始语音对话
                          </div>
                        ) : (
                          messages.map((message) => (
                            <div
                              key={message.id}
                              className={`flex gap-3 ${
                                message.isUser ? "justify-end" : "justify-start"
                              }`}
                            >
                              <div
                                className={`flex gap-2 max-w-[80%] ${
                                  message.isUser
                                    ? "flex-row-reverse"
                                    : "flex-row"
                                }`}
                              >
                                <div className="flex-shrink-0">
                                  {message.isUser ? (
                                    <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                                      <User className="h-4 w-4 text-primary-foreground" />
                                    </div>
                                  ) : (
                                    <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center">
                                      <Bot className="h-4 w-4 text-white" />
                                    </div>
                                  )}
                                </div>

                                <div
                                  className={`space-y-1 ${
                                    message.isUser ? "text-right" : "text-left"
                                  }`}
                                >
                                  <Card
                                    className={
                                      message.isUser
                                        ? "bg-primary text-primary-foreground"
                                        : ""
                                    }
                                  >
                                    <CardContent className="p-3">
                                      <div className="text-sm">
                                        {message.content}
                                      </div>
                                      {message.recognizedText &&
                                        message.recognizedText !==
                                          message.content && (
                                          <div className="text-xs opacity-70 mt-1 italic">
                                            识别: {message.recognizedText}
                                          </div>
                                        )}
                                    </CardContent>
                                  </Card>
                                  <div className="text-xs text-muted-foreground">
                                    {formatTime(message.timestamp)}
                                  </div>
                                </div>
                              </div>
                            </div>
                          ))
                        )}
                        <div ref={messagesEndRef} />
                      </div>
                    </ScrollArea>
                  </CardContent>
                </Card>
              )}

              {/* 使用说明 */}
              <Card className="bg-muted/50">
                <CardContent className="p-4">
                  <h4 className="font-semibold mb-2">使用说明：</h4>
                  {funAudioAvailable && serviceStatus && (
                    <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
                      <h5 className="font-semibold text-sm mb-2 flex items-center gap-2">
                        <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
                        FunAudioLLM语音服务：
                      </h5>
                      <ul className="list-disc list-inside space-y-1 text-xs text-blue-800 dark:text-blue-200">
                        <li>
                          🎤 语音识别：{serviceStatus.audio_model?.name} (
                          {serviceStatus.audio_model?.available
                            ? "可用"
                            : "不可用"}
                          )
                        </li>
                        <li>
                          💬 对话处理：{serviceStatus.chat_model?.name} (
                          {serviceStatus.chat_model?.available
                            ? "可用"
                            : "不可用"}
                          )
                        </li>
                        <li>🔄 连续对话：支持上下文记忆</li>
                        <li>🎯 多会话：支持独立会话管理</li>
                        <li>⚡ 本地化处理：响应更快，隐私更安全</li>
                      </ul>

                      <div className="mt-2 p-2 bg-green-100 dark:bg-green-900/30 rounded text-xs">
                        <strong>✅ 服务状态：</strong> {serviceStatus.message}
                      </div>
                    </div>
                  )}

                  <div className="mt-4 p-3 bg-yellow-50 dark:bg-yellow-950/20 rounded-lg">
                    <h5 className="font-semibold text-sm mb-2">
                      WebSocket统一语音模式：
                    </h5>
                    <ul className="list-disc list-inside space-y-1 text-xs text-muted-foreground">
                      <li>🎯 基于FunAudioLLM高性能语音识别引擎</li>
                      <li>⚡ WebSocket实时连接，延迟更低</li>
                      <li>🔄 自动重连机制，连接更稳定</li>
                      <li>💡 心跳检测，实时监控连接状态</li>
                      <li>🎤 统一支持唤醒词检测和语音对话</li>
                      <li>🌐 推荐使用Chrome、Edge或Safari浏览器</li>
                      <li>🔧 确保LM Studio中正确加载了SenseVoice模型</li>
                      <li>📡 确保网络连接稳定以获得最佳体验</li>
                      <li>💬 支持语音打断和连续对话功能</li>
                      <li>🍎 Apple Silicon用户享受MPS硬件加速</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>

              {/* 语音功能不可用提示 */}
              {!funAudioAvailable && (
                <Card className="bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800">
                  <CardContent className="p-4">
                    <div className="flex items-center gap-2 text-red-800 dark:text-red-200">
                      <Mic className="h-4 w-4" />
                      <div>
                        <h4 className="font-semibold">语音功能不可用</h4>
                        <p className="text-sm mt-1">
                          检测到语音功能不可用。请尝试以下解决方案：
                        </p>
                        <div className="text-sm mt-2">
                          <h6 className="font-semibold">
                            FunAudioLLM服务方案（推荐）：
                          </h6>
                          <ul className="list-disc list-inside ml-2">
                            <li>确保LM Studio正在运行</li>
                            <li>加载SenseVoice和LM Studio聊天模型</li>
                            <li>检查后端服务连接</li>
                          </ul>
                          <h6 className="font-semibold mt-2">浏览器方案：</h6>
                          <ul className="list-disc list-inside ml-2">
                            <li>使用Chrome、Edge或Safari浏览器</li>
                            <li>确保浏览器版本是最新的</li>
                            <li>检查是否允许了麦克风权限</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
