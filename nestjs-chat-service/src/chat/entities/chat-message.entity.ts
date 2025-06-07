import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  ManyToOne,
  JoinColumn,
  Index,
} from 'typeorm';
import { ChatSession } from './chat-session.entity';

/**
 * 聊天消息实体
 * 存储聊天会话中的每条消息
 */
@Entity('chat_messages')
@Index(['sessionId', 'createdAt'])
@Index(['userId', 'createdAt'])
export class ChatMessage {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  /**
   * 会话ID - 关联到聊天会话
   */
  @Column({ name: 'session_id', type: 'uuid' })
  @Index()
  sessionId: string;

  /**
   * 用户ID - 对应若依系统的用户ID
   */
  @Column({ name: 'user_id', type: 'bigint' })
  @Index()
  userId: number;

  /**
   * 消息角色 - user: 用户, assistant: AI助手, system: 系统
   */
  @Column({ 
    type: 'enum', 
    enum: ['user', 'assistant', 'system'], 
    default: 'user' 
  })
  role: 'user' | 'assistant' | 'system';

  /**
   * 消息内容 - 主要的文本内容
   */
  @Column({ type: 'text' })
  content: string;

  /**
   * 消息类型 - text: 纯文本, voice: 语音, image: 图片, file: 文件, multimodal: 多模态
   */
  @Column({ 
    type: 'enum', 
    enum: ['text', 'voice', 'image', 'file', 'multimodal'], 
    default: 'text' 
  })
  messageType: 'text' | 'voice' | 'image' | 'file' | 'multimodal';

  /**
   * 消息元数据 - JSON格式存储额外信息
   * 例如：文件路径、语音时长、图片尺寸等
   */
  @Column({ type: 'json', nullable: true })
  metadata?: {
    filePath?: string;
    fileName?: string;
    fileSize?: number;
    duration?: number;
    imageWidth?: number;
    imageHeight?: number;
    voiceUrl?: string;
    attachments?: Array<{
      type: string;
      url: string;
      name: string;
      size?: number;
    }>;
    [key: string]: any;
  };

  /**
   * 消息状态 - sent: 已发送, delivered: 已送达, read: 已读, failed: 失败
   */
  @Column({ 
    type: 'enum', 
    enum: ['sent', 'delivered', 'read', 'failed'], 
    default: 'sent' 
  })
  status: 'sent' | 'delivered' | 'read' | 'failed';

  /**
   * 父消息ID - 用于回复功能
   */
  @Column({ name: 'parent_message_id', type: 'uuid', nullable: true })
  parentMessageId?: string;

  /**
   * 消息序号 - 在会话中的顺序
   */
  @Column({ name: 'sequence_number', type: 'int', default: 0 })
  sequenceNumber: number;

  /**
   * 创建时间
   */
  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  /**
   * 关联的聊天会话
   */
  @ManyToOne(() => ChatSession, (session) => session.messages, {
    onDelete: 'CASCADE',
  })
  @JoinColumn({ name: 'session_id' })
  session: ChatSession;
} 