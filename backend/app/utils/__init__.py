"""
Utils 工具包
统一导入所有工具类和函数
"""

# 通用工具
from .common_utils import generate_doc_id, get_random_color, get_timestamp, safe_get, safe_int, safe_float, safe_str_convert, truncate_string, calculate_similarity

# 文本处理
from .text_processing import TextProcessor

# 文档分析
from .document_analysis import DocumentAnalyzer

# LLM客户端
from .llm_client import LLMClient

# 语音处理
from .voice_utils import VoiceProcessor, clean_text_for_speech, split_text_for_tts, synthesize_speech_chunk

# 时间处理
from .time_utils import (
    TimeUtils, 
    now_china, 
    now_china_naive, 
    utc_to_china, 
    china_to_utc, 
    format_china_time, 
    get_china_timestamp_sql
)

# 图像处理
from .image_processing import (
    ImageProcessor,
    enhance_image,
    preprocess_for_ocr,
    adjust_brightness_contrast,
    resize_for_processing
)

# 缓存工具
from .cache_utils import (
    FileHashCache,
    ContentHashCache,
    OCRCache,
    FileExtractionCache,
    create_file_cache,
    create_content_cache,
    create_ocr_cache,
    create_file_extraction_cache
)

# 文件处理工具
from .file_utils import (
    FileTypeDetector,
    detect_file_type,
    get_supported_file_types,
    is_supported_file_type,
    get_file_category,
    get_file_info,
    validate_file_size
)

# 文本处理（新增）
from .text_processing import clean_extracted_text

# 音频处理
from .audio_utils import (
    AudioProcessor,
    preprocess_audio,
    save_audio_temp,
    validate_audio_data,
    cleanup_temp_file
)

# 设备管理
from .device_utils import (
    DeviceManager,
    get_optimal_device,
    setup_mps_optimization,
    setup_device_optimization,
    get_memory_usage,
    clear_device_cache,
    get_device_info
)

# 情感分析
from .emotion_utils import (
    EmotionAnalyzer,
    analyze_emotion,
    extract_emotion_info,
    extract_event_info,
    clean_text,
    fuzzy_match,
    generate_simple_response,
    # SenseVoice 专用函数
    extract_sensevoice_emotion_info,
    extract_sensevoice_event_info,
    clean_sensevoice_text,
    fuzzy_match_wake_word
)

# LLM工具
from .llm_utils import (
    MessageProcessor,
    prepare_messages,
    format_chat_history,
    create_conversation_context,
    extract_response_content,
    validate_message_format,
    truncate_messages,
    # 新增便捷函数
    prepare_lm_studio_messages,
    format_user_message,
    format_assistant_message,
    limit_conversation_history
)

__all__ = [
    # 通用工具
    'generate_doc_id',
    'get_random_color',
    'get_timestamp',
    'safe_get',
    'safe_int',
    'safe_float',
    'safe_str_convert',
    'truncate_string',
    'calculate_similarity',
    
    # 文本处理
    'TextProcessor',
    
    # 文档分析
    'DocumentAnalyzer',
    
    # LLM客户端
    'LLMClient',
    
    # 语音处理
    'VoiceProcessor',
    'clean_text_for_speech',
    'split_text_for_tts',
    'synthesize_speech_chunk',
    
    # 时间处理
    'TimeUtils',
    'now_china',
    'now_china_naive',
    'utc_to_china',
    'china_to_utc',
    'format_china_time',
    'get_china_timestamp_sql',
    
    # 图像处理
    'ImageProcessor',
    'enhance_image',
    'preprocess_for_ocr',
    'adjust_brightness_contrast',
    'resize_for_processing',
    
    # 缓存工具
    'FileHashCache',
    'ContentHashCache',
    'OCRCache',
    'FileExtractionCache',
    'create_file_cache',
    'create_content_cache',
    'create_ocr_cache',
    'create_file_extraction_cache',
    
    # 文件处理工具
    'FileTypeDetector',
    'detect_file_type',
    'get_supported_file_types',
    'is_supported_file_type',
    'get_file_category',
    'get_file_info',
    'validate_file_size',
    
    # 文本处理（新增）
    'clean_extracted_text',
    
    # 音频处理
    'AudioProcessor',
    'preprocess_audio',
    'save_audio_temp',
    'validate_audio_data',
    'cleanup_temp_file',
    
    # 设备管理
    'DeviceManager',
    'get_optimal_device',
    'setup_mps_optimization',
    'setup_device_optimization',
    'get_memory_usage',
    'clear_device_cache',
    'get_device_info',
    
    # 情感分析
    'EmotionAnalyzer',
    'analyze_emotion',
    'extract_emotion_info',
    'extract_event_info',
    'clean_text',
    'fuzzy_match',
    'generate_simple_response',
    # SenseVoice 专用函数
    'extract_sensevoice_emotion_info',
    'extract_sensevoice_event_info',
    'clean_sensevoice_text',
    'fuzzy_match_wake_word',
    
    # LLM工具
    'MessageProcessor',
    'prepare_messages',
    'format_chat_history',
    'create_conversation_context',
    'extract_response_content',
    'validate_message_format',
    'truncate_messages',
    # 新增便捷函数
    'prepare_lm_studio_messages',
    'format_user_message',
    'format_assistant_message',
    'limit_conversation_history',
] 