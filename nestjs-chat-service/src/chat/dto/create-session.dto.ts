import { IsString, IsOptional, IsArray, MaxLength } from 'class-validator';

/**
 * 创建聊天会话的数据传输对象
 */
export class CreateSessionDto {
  /**
   * 会话标题
   */
  @IsString()
  @MaxLength(200, { message: '会话标题不能超过200个字符' })
  @IsOptional()
  title?: string = '新的对话';

  /**
   * 会话描述
   */
  @IsString()
  @IsOptional()
  description?: string;

  /**
   * 会话标签
   */
  @IsArray()
  @IsString({ each: true })
  @IsOptional()
  tags?: string[];
} 