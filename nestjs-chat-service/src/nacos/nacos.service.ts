import { Injectable, Logger, OnModuleInit, OnModuleDestroy } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { NacosNamingClient } from 'nacos';
import * as os from 'os';

/**
 * Nacos服务注册与发现
 * 负责将服务注册到Nacos注册中心
 */
@Injectable()
export class NacosService implements OnModuleInit, OnModuleDestroy {
  private readonly logger = new Logger(NacosService.name);
  private namingClient: NacosNamingClient;
  private serviceName: string;
  private serviceIp: string;
  private servicePort: number;

  constructor(private readonly configService: ConfigService) {
    this.serviceName = this.configService.get<string>('NACOS_SERVICE_NAME', 'xzxz-chat-service');
    this.serviceIp = this.getLocalIP();
    this.servicePort = this.configService.get<number>('PORT', 8001);
  }

  /**
   * 自动获取本机IP地址
   */
  private getLocalIP(): string {
    // 优先使用环境变量配置的IP
    const configuredIP = this.configService.get<string>('SERVICE_IP');
    if (configuredIP && configuredIP !== '0.0.0.0' && configuredIP !== '127.0.0.1') {
      this.logger.log(`使用配置的服务IP: ${configuredIP}`);
      return configuredIP;
    }

    // 自动检测本机IP地址
    const interfaces = os.networkInterfaces();
    
    // 优先级：以太网 > WiFi > 其他
    const priorityOrder = ['en0', 'eth0', 'en1', 'wlan0', 'wlp0s20f3'];
    
    for (const interfaceName of priorityOrder) {
      const networkInterface = interfaces[interfaceName];
      if (networkInterface) {
        for (const alias of networkInterface) {
          if (alias.family === 'IPv4' && !alias.internal) {
            this.logger.log(`自动检测到服务IP [${interfaceName}]: ${alias.address}`);
            return alias.address;
          }
        }
      }
    }

    // 如果优先接口都没找到，遍历所有接口
    for (const interfaceName of Object.keys(interfaces)) {
      const networkInterface = interfaces[interfaceName];
      if (networkInterface) {
        for (const alias of networkInterface) {
          if (alias.family === 'IPv4' && !alias.internal && !alias.address.startsWith('169.254')) {
            this.logger.log(`检测到服务IP [${interfaceName}]: ${alias.address}`);
            return alias.address;
          }
        }
      }
    }

    // 如果都没找到，使用localhost作为fallback
    this.logger.warn('无法自动检测到有效的网络IP，使用localhost');
    return '127.0.0.1';
  }

  async onModuleInit() {
    try {
      // 检查是否启用Nacos
      const nacosEnabled = this.configService.get<boolean>('NACOS_ENABLED', true);
      if (!nacosEnabled) {
        this.logger.log('Nacos服务注册已禁用');
        return;
      }

      // 初始化Nacos客户端
      const serverList = this.configService.get<string>('NACOS_SERVER_ADDRESSES', 'localhost:8848');
      const namespace = this.configService.get<string>('NACOS_NAMESPACE', '');
      
      this.namingClient = new NacosNamingClient({
        logger: console,
        serverList,
        namespace,
      });

      await this.namingClient.ready();
      this.logger.log('Nacos客户端初始化成功');

      // 注册服务实例
      await this.registerService();
      
      // 设置心跳检查
      this.setupHeartbeat();

    } catch (error) {
      this.logger.error('Nacos服务初始化失败:', error);
    }
  }

  async onModuleDestroy() {
    try {
      if (this.namingClient) {
        // 注销服务实例
        await this.deregisterService();
        this.logger.log('服务实例已注销');
      }
    } catch (error) {
      this.logger.error('注销服务实例失败:', error);
    }
  }

  /**
   * 注册服务实例到Nacos
   */
  private async registerService() {
    try {
      const groupName = this.configService.get<string>('NACOS_GROUP', 'DEFAULT_GROUP');
      const clusterName = this.configService.get<string>('NACOS_CLUSTER_NAME', 'DEFAULT');
      const weight = this.configService.get<number>('NACOS_WEIGHT', 1.0);

      const instance = {
        ip: this.serviceIp,
        port: this.servicePort,
        weight,
        metadata: {
          version: '1.0.0',
          service_type: 'chat_history',
          framework: 'nestjs',
          features: 'chat,history,session,message',
          health_check_url: '/chat/health',
          ...this.configService.get<object>('NACOS_METADATA', {}),
        },
      };

      await this.namingClient.registerInstance(this.serviceName, instance as any, groupName);
      
      this.logger.log(`服务实例注册成功: ${this.serviceName}@${this.serviceIp}:${this.servicePort}`);
    } catch (error) {
      this.logger.error('注册服务实例失败:', error);
      throw error;
    }
  }

  /**
   * 注销服务实例
   */
  private async deregisterService() {
    try {
      const groupName = this.configService.get<string>('NACOS_GROUP', 'DEFAULT_GROUP');
      
      await this.namingClient.deregisterInstance(this.serviceName, {
        ip: this.serviceIp,
        port: this.servicePort,
      } as any, groupName);
      
      this.logger.log('服务实例注销成功');
    } catch (error) {
      this.logger.error('注销服务实例失败:', error);
    }
  }

  /**
   * 设置心跳检查
   */
  private setupHeartbeat() {
    // Nacos客户端会自动处理心跳，这里可以添加额外的健康检查逻辑
    setInterval(() => {
      this.logger.debug(`服务心跳: ${this.serviceName}@${this.serviceIp}:${this.servicePort}`);
    }, 30000); // 30秒心跳日志
  }

  /**
   * 获取服务实例列表
   */
  async getServiceInstances(serviceName: string, groupName: string = 'DEFAULT_GROUP') {
    try {
      if (!this.namingClient) {
        throw new Error('Nacos客户端未初始化');
      }

      const instances = await this.namingClient.getAllInstances(serviceName, groupName);
      return instances;
    } catch (error) {
      this.logger.error(`获取服务实例失败: ${serviceName}`, error);
      throw error;
    }
  }

  /**
   * 选择一个健康的服务实例
   */
  async selectHealthyInstance(serviceName: string, groupName: string = 'DEFAULT_GROUP') {
    try {
      const instances = await this.getServiceInstances(serviceName, groupName);
      const healthyInstances = instances.filter(instance => instance.healthy && instance.enabled);
      
      if (healthyInstances.length === 0) {
        throw new Error(`没有可用的健康服务实例: ${serviceName}`);
      }

      // 简单的轮询选择策略
      const randomIndex = Math.floor(Math.random() * healthyInstances.length);
      return healthyInstances[randomIndex];
    } catch (error) {
      this.logger.error(`选择健康服务实例失败: ${serviceName}`, error);
      throw error;
    }
  }
} 