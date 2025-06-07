import { IsOptional, IsInt, Min, Max, IsEnum, IsString } from 'class-validator';
import { Transform } from 'class-transformer';

/**
 * 查询聊天会话的数据传输对象
 */
export class QuerySessionsDto {
  /**
   * 页码 - 从1开始
   */
  @IsOptional()
  @Transform(({ value }) => parseInt(value))
  @IsInt({ message: '页码必须是整数' })
  @Min(1, { message: '页码必须大于0' })
  page?: number = 1;

  /**
   * 每页数量
   */
  @IsOptional()
  @Transform(({ value }) => parseInt(value))
  @IsInt({ message: '每页数量必须是整数' })
  @Min(1, { message: '每页数量必须大于0' })
  @Max(100, { message: '每页数量不能超过100' })
  limit?: number = 20;

  /**
   * 会话状态过滤
   */
  @IsOptional()
  @IsEnum(['active', 'archived', 'deleted'], { 
    message: '会话状态必须是 active、archived 或 deleted' 
  })
  status?: 'active' | 'archived' | 'deleted';

  /**
   * 搜索关键词 - 搜索会话标题和描述
   */
  @IsOptional()
  @IsString()
  search?: string;

  /**
   * 排序字段
   */
  @IsOptional()
  @IsEnum(['createdAt', 'updatedAt', 'lastMessageAt', 'messageCount'], { 
    message: '排序字段必须是 createdAt、updatedAt、lastMessageAt 或 messageCount' 
  })
  sortBy?: 'createdAt' | 'updatedAt' | 'lastMessageAt' | 'messageCount' = 'lastMessageAt';

  /**
   * 排序方向
   */
  @IsOptional()
  @IsEnum(['ASC', 'DESC'], { 
    message: '排序方向必须是 ASC 或 DESC' 
  })
  sortOrder?: 'ASC' | 'DESC' = 'DESC';
} 