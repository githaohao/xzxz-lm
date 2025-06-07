import { Injectable, NotFoundException, ForbiddenException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, Like, FindManyOptions } from 'typeorm';
import { ChatSession } from './entities/chat-session.entity';
import { ChatMessage } from './entities/chat-message.entity';
import { CreateSessionDto } from './dto/create-session.dto';
import { CreateMessageDto } from './dto/create-message.dto';
import { QuerySessionsDto } from './dto/query-sessions.dto';

/**
 * 聊天服务类
 * 提供聊天会话和消息的CRUD操作
 */
@Injectable()
export class ChatService {
  constructor(
    @InjectRepository(ChatSession)
    private readonly sessionRepository: Repository<ChatSession>,
    @InjectRepository(ChatMessage)
    private readonly messageRepository: Repository<ChatMessage>,
  ) {}

  /**
   * 创建新的聊天会话
   */
  async createSession(userId: number, createSessionDto: CreateSessionDto): Promise<ChatSession> {
    const session = this.sessionRepository.create({
      ...createSessionDto,
      userId,
    });

    return await this.sessionRepository.save(session);
  }

  /**
   * 获取用户的聊天会话列表
   */
  async getUserSessions(userId: number, queryDto: QuerySessionsDto) {
    const { page = 1, limit = 20, status, search, sortBy = 'lastMessageAt', sortOrder = 'DESC' } = queryDto;
    
    const queryBuilder = this.sessionRepository.createQueryBuilder('session')
      .where('session.userId = :userId', { userId });

    // 状态过滤
    if (status) {
      queryBuilder.andWhere('session.status = :status', { status });
    } else {
      // 默认不显示已删除的会话
      queryBuilder.andWhere('session.status != :deletedStatus', { deletedStatus: 'deleted' });
    }

    // 搜索过滤
    if (search) {
      queryBuilder.andWhere(
        '(session.title LIKE :search OR session.description LIKE :search)',
        { search: `%${search}%` }
      );
    }

    // 排序
    queryBuilder.orderBy(`session.${sortBy}`, sortOrder);

    // 分页
    const offset = (page - 1) * limit;
    queryBuilder.skip(offset).take(limit);

    // 获取总数和数据
    const [sessions, total] = await queryBuilder.getManyAndCount();

    return {
      data: sessions,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  /**
   * 获取特定会话详情
   */
  async getSessionById(userId: number, sessionId: string): Promise<ChatSession> {
    const session = await this.sessionRepository.findOne({
      where: { id: sessionId, userId },
      relations: ['messages'],
    });

    if (!session) {
      throw new NotFoundException('会话不存在');
    }

    if (session.status === 'deleted') {
      throw new NotFoundException('会话已被删除');
    }

    return session;
  }

  /**
   * 更新会话信息
   */
  async updateSession(
    userId: number, 
    sessionId: string, 
    updateData: Partial<CreateSessionDto>
  ): Promise<ChatSession> {
    const session = await this.getSessionById(userId, sessionId);
    
    Object.assign(session, updateData);
    return await this.sessionRepository.save(session);
  }

  /**
   * 删除会话（软删除）
   */
  async deleteSession(userId: number, sessionId: string): Promise<void> {
    const session = await this.getSessionById(userId, sessionId);
    
    session.status = 'deleted';
    await this.sessionRepository.save(session);
  }

  /**
   * 归档会话
   */
  async archiveSession(userId: number, sessionId: string): Promise<ChatSession> {
    const session = await this.getSessionById(userId, sessionId);
    
    session.status = 'archived';
    return await this.sessionRepository.save(session);
  }

  /**
   * 恢复会话
   */
  async restoreSession(userId: number, sessionId: string): Promise<ChatSession> {
    const session = await this.sessionRepository.findOne({
      where: { id: sessionId, userId },
    });

    if (!session) {
      throw new NotFoundException('会话不存在');
    }

    session.status = 'active';
    return await this.sessionRepository.save(session);
  }

  /**
   * 添加消息到会话
   */
  async addMessage(userId: number, createMessageDto: CreateMessageDto): Promise<ChatMessage> {
    const { sessionId } = createMessageDto;
    
    // 验证会话是否存在且属于当前用户
    const session = await this.getSessionById(userId, sessionId);

    // 获取消息序号
    const messageCount = await this.messageRepository.count({
      where: { sessionId },
    });

    // 创建消息
    const message = this.messageRepository.create({
      ...createMessageDto,
      userId,
      sequenceNumber: messageCount + 1,
    });

    const savedMessage = await this.messageRepository.save(message);

    // 更新会话的最后消息时间和消息数量
    session.lastMessageAt = savedMessage.createdAt;
    session.messageCount = messageCount + 1;
    
    // 如果是第一条消息且没有自定义标题，使用消息内容作为标题
    if (messageCount === 0 && session.title === '新的对话') {
      session.title = createMessageDto.content.substring(0, 50) + (createMessageDto.content.length > 50 ? '...' : '');
    }

    await this.sessionRepository.save(session);

    return savedMessage;
  }

  /**
   * 获取会话的消息列表
   */
  async getSessionMessages(
    userId: number, 
    sessionId: string, 
    page: number = 1, 
    limit: number = 50
  ) {
    // 验证会话权限
    await this.getSessionById(userId, sessionId);

    const offset = (page - 1) * limit;
    
    const [messages, total] = await this.messageRepository.findAndCount({
      where: { sessionId },
      order: { sequenceNumber: 'ASC' },
      skip: offset,
      take: limit,
    });

    return {
      data: messages,
      pagination: {
        page,
        limit,
        total,
        totalPages: Math.ceil(total / limit),
      },
    };
  }

  /**
   * 删除消息
   */
  async deleteMessage(userId: number, messageId: string): Promise<void> {
    const message = await this.messageRepository.findOne({
      where: { id: messageId },
      relations: ['session'],
    });

    if (!message) {
      throw new NotFoundException('消息不存在');
    }

    if (message.session.userId !== userId) {
      throw new ForbiddenException('无权限删除此消息');
    }

    await this.messageRepository.remove(message);

    // 更新会话的消息数量
    const session = message.session;
    session.messageCount = Math.max(0, session.messageCount - 1);
    await this.sessionRepository.save(session);
  }

  /**
   * 获取用户的聊天统计信息
   */
  async getUserChatStats(userId: number) {
    const totalSessions = await this.sessionRepository.count({
      where: { userId, status: 'active' },
    });

    const totalMessages = await this.messageRepository.count({
      where: { userId },
    });

    const archivedSessions = await this.sessionRepository.count({
      where: { userId, status: 'archived' },
    });

    return {
      totalSessions,
      totalMessages,
      archivedSessions,
    };
  }
} 