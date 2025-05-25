// 测试语音引擎API修复
const axios = require('axios');

async function testVoiceEngineAPI() {
    console.log('🧪 测试语音引擎API修复...\n');
    
    try {
        // 直接测试后端API
        console.log('1. 测试后端API (http://localhost:8000/api/voice/engine)');
        const backendResponse = await axios.get('http://localhost:8000/api/voice/engine');
        console.log('✅ 后端API响应成功');
        console.log('📊 后端数据结构:', JSON.stringify(backendResponse.data, null, 2));
        
        // 模拟前端修复前的逻辑
        const oldLogic = backendResponse.data.available || false;
        console.log(`❌ 旧逻辑结果: ${oldLogic}`);
        
        // 模拟前端修复后的逻辑
        let newLogic = false;
        if (backendResponse.data.success && backendResponse.data.engine && backendResponse.data.engine.status) {
            newLogic = backendResponse.data.engine.status.available || false;
        } else {
            newLogic = backendResponse.data.available || false;
        }
        console.log(`✅ 新逻辑结果: ${newLogic}`);
        
        console.log('\n2. 测试前端代理API (http://localhost:3001/api/voice/engine)');
        try {
            const frontendResponse = await axios.get('http://localhost:3001/api/voice/engine');
            console.log('✅ 前端代理API响应成功');
            
            // 应用修复后的逻辑
            let proxyResult = false;
            if (frontendResponse.data.success && frontendResponse.data.engine && frontendResponse.data.engine.status) {
                proxyResult = frontendResponse.data.engine.status.available || false;
            } else {
                proxyResult = frontendResponse.data.available || false;
            }
            console.log(`✅ 前端代理结果: ${proxyResult}`);
            
        } catch (proxyError) {
            console.log('❌ 前端代理API测试失败:', proxyError.message);
            console.log('💡 请确保前端开发服务器在端口3001运行');
        }
        
        console.log('\n🎉 测试完成！');
        console.log('📝 总结:');
        console.log(`   - 后端API正常: ✅`);
        console.log(`   - 旧逻辑 (response.data.available): ${oldLogic ? '✅' : '❌'}`);
        console.log(`   - 新逻辑 (response.data.engine.status.available): ${newLogic ? '✅' : '❌'}`);
        console.log(`   - 修复状态: ${newLogic ? '成功' : '失败'}`);
        
    } catch (error) {
        console.error('❌ 测试失败:', error.message);
        console.log('💡 请确保后端服务器在端口8000运行');
    }
}

// 运行测试
testVoiceEngineAPI(); 