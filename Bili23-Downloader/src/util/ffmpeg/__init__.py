from util.common.enum import FFmpegSource
from util.common import config, Directory

from pathlib import Path
import logging
import shutil
import sys
import os

logger = logging.getLogger(__name__)

# 确定不同平台 FFmpeg 可执行文件名
if sys.platform == "win32":
    ffmpeg_executable = "ffmpeg.exe"

else:
    ffmpeg_executable = "ffmpeg"

def set_ffmpeg_environment(path: str):
    os.environ["PATH"] = os.environ["PATH"] + os.pathsep + str(Path(path).parent)

    logger.info(f"已将 FFmpeg 路径 {path} 添加到环境变量")

    config.no_ffmpeg_available = False

def try_system_ffmpeg():
    # 方法1：使用shutil.which在环境变量中查找
    ffmpeg_path = shutil.which(ffmpeg_executable)

    if ffmpeg_path:
        logger.info(f"环境变量中找到 FFmpeg 可执行文件：{ffmpeg_path}")
        set_ffmpeg_environment(ffmpeg_path)
        return True
    
    # 方法2：直接检查常见的FFmpeg安装位置
    common_paths = [
        Path("C:\\Users\\" + os.environ.get("USERNAME", "") + "\\ffmpeg.exe"),
        Path("C:\\Program Files\\ffmpeg\\bin\\ffmpeg.exe"),
        Path("C:\\Program Files (x86)\\ffmpeg\\bin\\ffmpeg.exe"),
        Path("D:\\ffmpeg\\bin\\ffmpeg.exe"),
        Path("E:\\ffmpeg\\bin\\ffmpeg.exe"),
    ]

    for path in common_paths:
        if path.exists():
            logger.info(f"在常见位置找到 FFmpeg 可执行文件：{path}")
            set_ffmpeg_environment(str(path))
            return True
    
    # 方法3：检查环境变量中是否直接包含ffmpeg.exe路径
    path_env = os.environ.get("PATH", "")
    for path in path_env.split(os.pathsep):
        if path.endswith("ffmpeg.exe") and Path(path).exists():
            logger.info(f"环境变量中找到 FFmpeg 可执行文件路径：{path}")
            set_ffmpeg_environment(path)
            return True
    
    logger.warning("环境变量中未找到 FFmpeg 可执行文件")
    return False

def try_bundled_ffmpeg():
    if config.bundle_ffmpeg_exist:
        logger.info(f"找到附带的 FFmpeg 可执行文件：{bundle_ffmpeg_path}")
        set_ffmpeg_environment(bundle_ffmpeg_path)
        return True
        
    logger.warning("没有找到附带的 FFmpeg 可执行文件")
    return False

def on_ffmpeg_not_found():
    logger.error("没有可用的 FFmpeg 可执行文件")
    config.no_ffmpeg_available = True
    return False

# 获取项目根目录
import os
# 获取当前文件的绝对路径
current_file = os.path.abspath(__file__)
logger.info(f"当前文件路径: {current_file}")

# 向上四级到项目根目录
parent1 = os.path.dirname(current_file)
logger.info(f"向上一级: {parent1}")
parent2 = os.path.dirname(parent1)
logger.info(f"向上二级: {parent2}")
parent3 = os.path.dirname(parent2)
logger.info(f"向上三级: {parent3}")
project_root = Path(os.path.dirname(parent3))
logger.info(f"向上四级 (项目根目录): {project_root}")

config.ffmpeg_executable = ffmpeg_executable
bundle_ffmpeg_path = project_root / "bundle" / ffmpeg_executable
logger.info(f"Bundle FFmpeg路径: {bundle_ffmpeg_path}")

# 检查文件是否存在
config.bundle_ffmpeg_exist = bundle_ffmpeg_path.exists()
logger.info(f"Bundle FFmpeg是否存在: {config.bundle_ffmpeg_exist}")

# 检查文件是否可执行
if config.bundle_ffmpeg_exist:
    logger.info(f"Bundle FFmpeg文件大小: {bundle_ffmpeg_path.stat().st_size} bytes")
    logger.info(f"Bundle FFmpeg是否可执行: {os.access(str(bundle_ffmpeg_path), os.X_OK)}")

match config.get(config.ffmpeg_source):
    case FFmpegSource.BUNDLED:
        if not try_bundled_ffmpeg():
            logger.warning("附带的 FFmpeg 不存在，将尝试使用环境变量中的 FFmpeg")
            
            if try_system_ffmpeg():
                config.set(config.ffmpeg_source, FFmpegSource.SYSTEM)
            else:
                on_ffmpeg_not_found()
                
    case FFmpegSource.SYSTEM:
        if not try_system_ffmpeg():
            logger.warning("环境变量中无 FFmpeg，将尝试使用附带的 FFmpeg")
            
            if try_bundled_ffmpeg():
                config.set(config.ffmpeg_source, FFmpegSource.BUNDLED)
            else:
                on_ffmpeg_not_found()
            
    case FFmpegSource.CUSTOM:
        custom_ffmpeg_path = Path(config.get(config.custom_ffmpeg_path), ffmpeg_executable)

        if custom_ffmpeg_path.exists():
            set_ffmpeg_environment(custom_ffmpeg_path)
        else:
            logger.warning(f"自定义 FFmpeg 路径无效：{custom_ffmpeg_path}，将尝试 fallback")

            if try_bundled_ffmpeg():
                config.set(config.ffmpeg_source, FFmpegSource.BUNDLED)

            elif try_system_ffmpeg():
                config.set(config.ffmpeg_source, FFmpegSource.SYSTEM)
                
            else:
                on_ffmpeg_not_found()

from util.ffmpeg.command import FFmpegCommand
from util.ffmpeg.runner import FFmpegRunner
