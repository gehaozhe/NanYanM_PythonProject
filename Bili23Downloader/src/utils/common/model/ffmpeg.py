from utils.config import Config

class FFmpegCommand:
    def __init__(self, input_files: list[str], output: str):
        self.input_files = input_files
        self.output = output

    def merge(self):
        params = ["-acodec", "copy", "-vcodec", "copy", "-strict", "experimental"]

        return self.construct(params)
    
    def convert_audio(self, acodec: str):
        params = ["-c:a", acodec, "-q:a", "0"]

        return self.construct(params)
    
    def merge_flv_list(self):
        params = ["-f", "concat", "-safe", "0", "-c", "copy"]

        return self.construct(params)

    def construct(self, params: list[str]):
        command = [f'"{Config.Merge.ffmpeg_path}"', "-y"]

        for input_file in self.input_files:
            command.extend(["-i", input_file])

        command.extend(params)
        command.append(self.output)

        return " ".join(command)

    def add_cover(self):
        # 确保输入文件列表至少有两个文件：视频文件和封面文件
        if len(self.input_files) < 2:
            return ""
        
        # 第一个输入是视频文件，第二个输入是封面文件
        # 使用-map选项来指定流映射
        params = [
            "-map", "0:v", "-map", "0:a?", "-map", "1:v",
            "-c:v", "copy", "-c:a", "copy",
            "-disposition:v:1", "attached_pic"
        ]

        return self.construct(params)