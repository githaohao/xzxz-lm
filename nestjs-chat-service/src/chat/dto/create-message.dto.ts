import { IsString, IsEnum, IsOptional, IsObject, IsUUID } from 'class-validator';

/**
 * 创建聊天消息的数据传输对象
 */
export class CreateMessageDto {
  /**
   * 会话ID
   */
  @IsUUID(4, { message: '会话ID格式不正确' })
  sessionId: string;

  /**
   * 消息角色
   */
  @IsEnum(['user', 'assistant', 'system'], { 
    message: '消息角色必须是 user、assistant 或 system' 
  })
  role: 'user' | 'assistant' | 'system';

  /**
   * 消息内容
   */
  @IsString()
  content: string;

  /**
   * 消息类型
   */
  @IsEnum(['text', 'voice', 'image', 'file', 'multimodal'], { 
    message: '消息类型必须是 text、voice、image、file 或 multimodal' 
  })
  @IsOptional()
  messageType?: 'text' | 'voice' | 'image' | 'file' | 'multimodal' = 'text';

  /**
   * 消息元数据
   */
  @IsObject()
  @IsOptional()
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
   * 父消息ID - 用于回复功能
   */
  @IsUUID(4, { message: '父消息ID格式不正确' })
  @IsOptional()
  parentMessageId?: string;
} 