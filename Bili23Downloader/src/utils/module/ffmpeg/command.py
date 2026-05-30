import os

from utils.config import Config

from utils.common.model.data_type import Command
from utils.common.model.task_info import DownloadTaskInfo
from utils.common.model.ffmpeg import FFmpegCommand

from utils.module.ffmpeg.prop import FFProp

class FFCommand:
    @classmethod
    def get_merge_dash_command(cls, task_info: DownloadTaskInfo):
        def check_audio_conversion_need():
            match task_info.output_type:
                case "flac":
                    output_temp_file = prop.output_temp_file("flac")

                    command.add(cls.get_convert_audio_command(audio_temp_file, output_temp_file, "flac"))
                    command.add_remove([audio_temp_file], task_info.download_path)

                    return output_temp_file

                case "m4a":
                    if Config.Merge.m4a_to_mp3:
                        task_info.output_type = "mp3"
                        output_temp_file = prop.output_temp_file("mp3")

                        command.add(cls.get_convert_audio_command(audio_temp_file, output_temp_file, "libmp3lame"))
                        command.add_remove([audio_temp_file], task_info.download_path)

                        return output_temp_file
                    
                    else:
                        return prop.audio_temp_file()
                
                case _:
                    return output_temp_file

        command = Command()

        prop = FFProp(task_info)

        video_temp_file = prop.video_temp_file()
        audio_temp_file = prop.audio_temp_file()
        output_temp_file = prop.output_temp_file("mp4")

        match task_info.download_option.copy():
            case ["video", "audio"]:
                ffcommand = FFmpegCommand([video_temp_file, audio_temp_file], output_temp_file)

                command.add(ffcommand.merge())
                
                # 添加封面到视频文件
                if hasattr(task_info, 'cover_url') and task_info.cover_url:
                    cover_temp_file = os.path.join(task_info.download_path, f"{task_info.id}_cover.jpg")
                    final_output_file = os.path.join(task_info.download_path, prop.output_file_name("mp4"))
                    cover_output_file = os.path.join(task_info.download_path, f"{task_info.id}_with_cover.mp4")
                    
                    # 下载封面
                    from utils.module.pic.cover import Cover
                    cover_data = Cover.download_cover(task_info.cover_url)
                    with open(cover_temp_file, "wb") as f:
                        f.write(cover_data)
                    
                    # 添加封面
                    command.add(cls.get_add_cover_command(output_temp_file, cover_temp_file, cover_output_file))
                    command.add_rename(cover_output_file, prop.output_file_name("mp4"), task_info.download_path)
                    
                    # 清理临时文件
                    command.add_remove([cover_temp_file, output_temp_file], task_info.download_path)
                else:
                    command.add_rename(output_temp_file, prop.output_file_name("mp4"), task_info.download_path)

                if Config.Merge.keep_original_files:
                    command.add_rename(video_temp_file, f"{task_info.file_name}_video.{task_info.video_type}", task_info.download_path)
                    command.add_rename(audio_temp_file, f"{task_info.file_name}_audio.{task_info.audio_type}", task_info.download_path)
                else:
                    command.add_remove([video_temp_file, audio_temp_file], task_info.download_path)

            case ["video"]:
                # 添加封面到视频文件
                if hasattr(task_info, 'cover_url') and task_info.cover_url:
                    cover_temp_file = os.path.join(task_info.download_path, f"{task_info.id}_cover.jpg")
                    final_output_file = os.path.join(task_info.download_path, prop.output_file_name("mp4"))
                    cover_output_file = os.path.join(task_info.download_path, f"{task_info.id}_with_cover.mp4")
                    
                    # 下载封面
                    from utils.module.pic.cover import Cover
                    cover_data = Cover.download_cover(task_info.cover_url)
                    with open(cover_temp_file, "wb") as f:
                        f.write(cover_data)
                    
                    # 添加封面
                    command.add(cls.get_add_cover_command(video_temp_file, cover_temp_file, cover_output_file))
                    command.add_rename(cover_output_file, prop.output_file_name("mp4"), task_info.download_path)
                    
                    # 清理临时文件
                    command.add_remove([cover_temp_file], task_info.download_path)
                else:
                    command.add_rename(video_temp_file, prop.output_file_name("mp4"), task_info.download_path)

            case ["audio"]:
                audio_temp_file = check_audio_conversion_need()

                command.add_rename(audio_temp_file, prop.output_file_name(), task_info.download_path)

        return command
    
    @classmethod
    def get_merge_flv_command(cls, task_info: DownloadTaskInfo):
        def create_flv_list_file(task_info: DownloadTaskInfo, path: str):
            with open(path, "w", encoding = "utf-8") as f:
                f.write("\n".join([f"file flv_{task_info.id}_part{i + 1}.flv" for i in range(task_info.flv_video_count)]))

        command = Command()

        prop = FFProp(task_info)

        if task_info.flv_video_count > 1:
            create_flv_list_file(task_info, prop.flv_list_path())

            output_temp_file = prop.output_temp_file()

            command.add(cls.get_merge_flv_list_command(prop.flv_list_path(), output_temp_file))
            command.add_rename(output_temp_file, prop.output_file_name(), task_info.download_path)
        else:
            command.add_rename(prop.flv_temp_file(), prop.output_file_name(), task_info.download_path)

        return command

    @staticmethod
    def get_merge_mp4_command(task_info: DownloadTaskInfo):
        command = Command()

        prop = FFProp(task_info)

        video_temp_file = prop.video_temp_file()
        output_file_name = prop.output_file_name()

        command.add_rename(video_temp_file, output_file_name, task_info.download_path)

        return command

    @staticmethod
    def get_convert_audio_command(src: str, dst: str, acodec: str):
        ffcommand = FFmpegCommand([src], dst)

        return ffcommand.convert_audio(acodec)

    @staticmethod
    def get_merge_flv_list_command(src: str, dst: str):
        ffcommand = FFmpegCommand([src], dst)

        return ffcommand.merge_flv_list()

    @staticmethod
    def get_add_cover_command(video_file: str, cover_file: str, output_file: str):
        ffcommand = FFmpegCommand([video_file, cover_file], output_file)

        return ffcommand.add_cover()