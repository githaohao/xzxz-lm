/**
 * 文本处理工具函数
 * 用于清理AI回复中不适合语音输出的内容
 */

/**
 * 清理文本以适合语音输出
 * 移除think标签、表情符号等不适合语音的内容
 */
export function cleanTextForSpeech(text: string): string {
  if (!text) return text;
  
  let cleanedText = text;
  
  // 1. 移除 <think>...</think> 标签及其内容
  cleanedText = cleanedText.replace(/<think>[\s\S]*?<\/think>/gi, '');
  
  // 2. 移除其他XML/HTML标签
  cleanedText = cleanedText.replace(/<[^>]*>/g, '');
  
  // 3. 移除表情符号
  cleanedText = removeEmojis(cleanedText);
  
  // 4. 移除markdown格式符号
  cleanedText = cleanedText.replace(/\*\*(.*?)\*\*/g, '$1'); // 粗体
  cleanedText = cleanedText.replace(/\*(.*?)\*/g, '$1');     // 斜体
  cleanedText = cleanedText.replace(/`(.*?)`/g, '$1');       // 代码
  cleanedText = cleanedText.replace(/~~(.*?)~~/g, '$1');     // 删除线
  
  // 5. 移除其他特殊符号
  cleanedText = removeSpecialSymbols(cleanedText);
  
  // 6. 清理多余的空白字符
  cleanedText = cleanedText.replace(/\s+/g, ' '); // 多个空格变成单个空格
  cleanedText = cleanedText.replace(/^\s+|\s+$/g, ''); // 移除首尾空格
  
  // 7. 移除空行
  cleanedText = cleanedText.replace(/\n\s*\n/g, '\n');
  
  return cleanedText;
}

/**
 * 移除表情符号
 */
function removeEmojis(text: string): string {
  let cleanedText = text;
  
  // 移除常见的文本表情符号
  const textEmojis = [
    /[:;=]-?[)(\]DPp]/g,     // :) :( :D ;) ;( =) 等
    /[xX][dD]/g,             // xD XD
    /o\.o|O\.O/g,            // o.o O.O
    /\^_\^|\^-\^/g,          // ^_^ ^-^
    />_<|<_>/g,              // >_< <_>
    /:\/|:\||>:\(|<3/g,      // :/ :| >:( <3
    /\\\o\/|\o\//g,          // \o/ o/
    /\\m\//g,                // \m/
    /-_-|>:\)/g              // -_- >:)
  ];
  
  for (const pattern of textEmojis) {
    cleanedText = cleanedText.replace(pattern, '');
  }
  
  // 移除一些基本的Unicode符号
  cleanedText = cleanedText.replace(/[\u2600-\u26FF]/g, '');     // 杂项符号
  cleanedText = cleanedText.replace(/[\u2700-\u27BF]/g, '');     // 装饰符号
  cleanedText = cleanedText.replace(/[\u2B00-\u2BFF]/g, '');     // 杂项符号和箭头
  
  return cleanedText;
}

/**
 * 移除特殊符号
 */
function removeSpecialSymbols(text: string): string {
  let cleanedText = text;
  
  // 移除一些常见的特殊符号（使用ASCII码范围）
  cleanedText = cleanedText.replace(/[★☆]/g, '');
  cleanedText = cleanedText.replace(/[✓✔]/g, '');
  cleanedText = cleanedText.replace(/[❌❎]/g, '');
  
  return cleanedText;
}

/**
 * 检查文本是否包含think标签
 */
export function hasThinkTags(text: string): boolean {
  return /<think>[\s\S]*?<\/think>/i.test(text);
}

/**
 * 提取think标签中的内容（用于调试）
 */
export function extractThinkContent(text: string): string[] {
  const matches = text.match(/<think>([\s\S]*?)<\/think>/gi);
  if (!matches) return [];
  
  return matches.map(match => 
    match.replace(/<\/?think>/gi, '').trim()
  );
}

/**
 * 估算文本的语音播放时长（秒）
 * 基于平均语速：中文约150字/分钟，英文约180词/分钟
 */
export function estimateSpeechDuration(text: string): number {
  const cleanText = cleanTextForSpeech(text);
  
  // 简单估算：中文字符和英文单词数
  const chineseChars = (cleanText.match(/[\u4e00-\u9fff]/g) || []).length;
  const englishWords = (cleanText.match(/[a-zA-Z]+/g) || []).length;
  
  // 中文：150字/分钟 = 2.5字/秒
  // 英文：180词/分钟 = 3词/秒
  const chineseDuration = chineseChars / 2.5;
  const englishDuration = englishWords / 3;
  
  return Math.max(chineseDuration + englishDuration, 1); // 至少1秒
}

/**
 * 检测文本是否主要是空白或只包含被过滤的内容
 */
export function isEmptyAfterCleaning(text: string): boolean {
  const cleaned = cleanTextForSpeech(text);
  return !cleaned || cleaned.trim().length === 0;
}
