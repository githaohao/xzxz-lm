import {
  Controller,
  Get,
  Post,
  Put,
  Delete,
  Body,
  Param,
  Query,
  UseGuards,
  Request,
  HttpCode,
  HttpStatus,
  ParseIntPipe,
  ValidationPipe,
  UsePipes,
} from '@nestjs/common';
import { ChatService } from './chat.service';
import { AuthGuard, UserInfo, Public } from '../auth/auth.guard';
import { SecurityContextHolder } from '../auth/security-context';
import { CreateSessionDto } from './dto/create-session.dto';
import { CreateMessageDto } from './dto/create-message.dto';
import { QuerySessionsDto } from './dto/query-sessions.dto';
// import { UpdateSessionDto } from './dto/update-session.dto';

/**
 * 聊天控制器
 * 提供聊天历史相关的REST API
 */
@Controller('/chat')
@UseGuards(AuthGuard)
export class ChatController {
  constructor(private readonly chatService: ChatService) {}

  /**
   * 创建新的聊天会话
   */
  @Post('sessions')
  async createSession(
    @Request() req: { user: UserInfo },
    @Body() createSessionDto: CreateSessionDto,
  ) {
    const session = await this.chatService.createSession(
      req.user.userId,
      createSessionDto,
    );

    return {
      code: 200,
      msg: '会话创建成功',
      data: session,
    };
  }

  /**
   * 获取用户的聊天会话列表
   */
  @Get('sessions')
  async getUserSessions(
    @Request() req: { user: UserInfo },
    @Query() queryDto: QuerySessionsDto,
  ) {
    const result = await this.chatService.getUserSessions(
      req.user.userId,
      queryDto,
    );

    return {
      code: 200,
      msg: '获取会话列表成功',
      data: result.data,
      pagination: result.pagination,
    };
  }

  /**
   * 获取特定会话详情
   */
  @Get('sessions/:id')
  async getSessionById(
    @Request() req: { user: UserInfo },
    @Param('id') sessionId: string,
  ) {
    const session = await this.chatService.getSessionById(
      req.user.userId,
      sessionId,
    );

    return {
      code: 200,
      msg: '获取会话详情成功',
      data: session,
    };
  }

  /**
   * 更新会话信息
   */
  @Put('sessions/:id')
  async updateSession(
    @Request() req: { user: UserInfo },
    @Param('id') sessionId: string,
    @Body() updateData: Partial<CreateSessionDto>,
  ) {
    const session = await this.chatService.updateSession(
      req.user.userId,
      sessionId,
      updateData,
    );

    return {
      code: 200,
      msg: '会话更新成功',
      data: session,
    };
  }

  /**
   * 删除会话（软删除）
   */
  @Delete('sessions/:id')
  @HttpCode(HttpStatus.OK)
  async deleteSession(
    @Request() req: { user: UserInfo },
    @Param('id') sessionId: string,
  ) {
    await this.chatService.deleteSession(req.user.userId, sessionId);

    return {
      code: 200,
      msg: '会话删除成功',
    };
  }

  /**
   * 归档会话
   */
  @Put('sessions/:id/archive')
  async archiveSession(
    @Request() req: { user: UserInfo },
    @Param('id') sessionId: string,
  ) {
    const session = await this.chatService.archiveSession(
      req.user.userId,
      sessionId,
    );

    return {
      code: 200,
      msg: '会话归档成功',
      data: session,
    };
  }

  /**
   * 恢复会话
   */
  @Put('sessions/:id/restore')
  async restoreSession(
    @Request() req: { user: UserInfo },
    @Param('id') sessionId: string,
  ) {
    const session = await this.chatService.restoreSession(
      req.user.userId,
      sessionId,
    );

    return {
      code: 200,
      msg: '会话恢复成功',
      data: session,
    };
  }

  /**
   * 获取会话的消息列表
   */
  @Get('sessions/:id/messages')
  async getSessionMessages(
    @Request() req: { user: UserInfo },
    @Param('id') sessionId: string,
    @Query('page') page?: number,
    @Query('limit') limit?: number,
  ) {
    const result = await this.chatService.getSessionMessages(
      req.user.userId,
      sessionId,
      page,
      limit,
    );

    return {
      code: 200,
      msg: '获取消息列表成功',
      data: result.data,
      pagination: result.pagination,
    };
  }

  /**
   * 添加消息到会话
   */
  @Post('sessions/:id/messages')
  async addMessage(
    @Request() req: { user: UserInfo },
    @Param('id') sessionId: string,
    @Body() createMessageDto: Omit<CreateMessageDto, 'sessionId'>,
  ) {
    const messageDto = { ...createMessageDto, sessionId };
    const message = await this.chatService.addMessage(
      req.user.userId,
      messageDto,
    );

    return {
      code: 200,
      msg: '消息添加成功',
      data: message,
    };
  }

  /**
   * 批量添加消息（用于保存完整对话）
   */
  @Post('messages/batch')
  async addMessages(
    @Request() req: { user: UserInfo },
    @Body() messages: CreateMessageDto[],
  ) {
    const savedMessages = [];
    
    for (const messageDto of messages) {
      const message = await this.chatService.addMessage(
        req.user.userId,
        messageDto,
      );
      savedMessages.push(message);
    }

    return {
      code: 200,
      msg: '批量添加消息成功',
      data: savedMessages,
    };
  }

  /**
   * 删除消息
   */
  @Delete('messages/:id')
  @HttpCode(HttpStatus.OK)
  async deleteMessage(
    @Request() req: { user: UserInfo },
    @Param('id') messageId: string,
  ) {
    await this.chatService.deleteMessage(req.user.userId, messageId);

    return {
      code: 200,
      msg: '消息删除成功',
    };
  }

  /**
   * 获取用户的聊天统计信息
   */
  @Get('stats')
  async getUserChatStats(@Request() req: { user: UserInfo }) {
    const stats = await this.chatService.getUserChatStats(req.user.userId);

    return {
      code: 200,
      msg: '获取统计信息成功',
      data: stats,
    };
  }

  /**
   * 健康检查 - 公开端点，无需认证
   */
  @Public()
  @Get('health')
  getHealth() {
    return {
      code: 200,
      msg: '聊天历史服务运行正常',
      data: {
        service: 'xzxz-chat-service',
        status: 'UP',
        timestamp: new Date().toISOString(),
      },
    };
  }

  // 网关认证测试端点 - 用于验证从网关传递的用户信息
  @Get('test-auth')
  async testGatewayAuth(@Request() req: any) {
    // 从SecurityContextHolder获取用户信息
    const contextUser = SecurityContextHolder.getUserContext();
    
    return {
      message: '网关认证解析成功',
      requestUser: req.user, // 从请求对象获取的用户信息
      contextUser: contextUser, // 从SecurityContextHolder获取的用户信息
      headers: {
        'user-id': req.headers['user-id'],
        'username': req.headers['username'],
        'user-key': req.headers['user-key'],
        'roles': req.headers['roles'],
        'role-permission': req.headers['role-permission'],
        'dept-id': req.headers['dept-id'],
      },
      timestamp: new Date().toISOString(),
      note: '此端点用于测试网关传递的用户信息与NestJS服务的兼容性',
    };
  }
} 