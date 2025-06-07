import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  OneToMany,
  Index,
} from 'typeorm';
import { ChatMessage } from './chat-message.entity';

/**
 * 聊天会话实体
 * 用于管理用户的聊天会话，每个会话包含多条消息
 */
@Entity('chat_sessions')
@Index(['userId', 'createdAt'])
export class ChatSession {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  /**
   * 用户ID - 对应若依系统的用户ID
   */
  @Column({ name: 'user_id', type: 'bigint' })
  @Index()
  userId: number;

  /**
   * 会话标题 - 通常是第一条消息的摘要
   */
  @Column({ length: 200, default: '新的对话' })
  title: string;

  /**
   * 会话描述 - 可选的会话描述信息
   */
  @Column({ type: 'text', nullable: true })
  description?: string;

  /**
   * 会话状态 - active: 活跃, archived: 已归档, deleted: 已删除
   */
  @Column({ 
    type: 'enum', 
    enum: ['active', 'archived', 'deleted'], 
    default: 'active' 
  })
  status: 'active' | 'archived' | 'deleted';

  /**
   * 会话标签 - JSON格式存储标签数组
   */
  @Column({ type: 'json', nullable: true })
  tags?: string[];

  /**
   * 最后一条消息时间 - 用于排序
   */
  @Column({ name: 'last_message_at', type: 'timestamp', nullable: true })
  lastMessageAt?: Date;

  /**
   * 消息数量 - 冗余字段，提高查询性能
   */
  @Column({ name: 'message_count', type: 'int', default: 0 })
  messageCount: number;

  /**
   * 创建时间
   */
  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  /**
   * 更新时间
   */
  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  /**
   * 关联的聊天消息
   */
  @OneToMany(() => ChatMessage, (message) => message.session, {
    cascade: true,
    onDelete: 'CASCADE',
  })
  messages: ChatMessage[];
} 