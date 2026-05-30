import wmi

import shutil
import os
import time
import logging

# 获取程序所在目录
program_dir = os.path.dirname(os.path.abspath(__file__))
POLL_INTERVAL = 1  # 轮询间隔（秒）
LOG_FILE = "usb_copy.log"
COPIED_FILES_LOG = "copied_files.log"

# 初始化日志
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# 读取已复制文件的日志
def read_copied_files():
    copied_files = set()
    if os.path.exists(COPIED_FILES_LOG):
        with open(COPIED_FILES_LOG, 'r') as f:
            for line in f:
                copied_files.add(line.strip())
    return copied_files

# 记录已复制的文件
def record_copied_file(file_path):
    with open(COPIED_FILES_LOG, 'a') as f:
        f.write(file_path + '\n')

def copy_usb_content(usb_path, usb_name):
    """复制U盘内容到目标目录，保留目录结构并处理同名文件"""
    usb_root = os.path.abspath(usb_path)
    # 目标路径为程序目录下以 U 盘名字命名的文件夹
    TARGET_PATH = os.path.join(program_dir, usb_name)
    if not os.path.exists(TARGET_PATH):
        os.makedirs(TARGET_PATH)
    copied_files = read_copied_files()
    try:
        for root, _, files in os.walk(usb_path):
            # 创建目标子目录（相对于U盘根目录）
            relative_dir = os.path.relpath(root, usb_root)
            dest_dir = os.path.join(TARGET_PATH, relative_dir)
            os.makedirs(dest_dir, exist_ok=True)

            for filename in files:
                src_path = os.path.join(root, filename)
                if src_path in copied_files:
                    print(f"文件 {src_path} 已复制，跳过。")
                    continue
                dest_path = os.path.join(dest_dir, filename)

                # 处理同名文件：添加时间戳后缀
                if os.path.exists(dest_path):
                    timestamp = time.strftime("%Y%m%d_%H%M%S")
                    base, ext = os.path.splitext(filename)
                    new_filename = f"{base}_{timestamp}{ext}"
                    dest_path = os.path.join(dest_dir, new_filename)

                try:
                    print(f"正在复制文件：{src_path} → {dest_path}")
                    shutil.copy2(src_path, dest_path)
                    logging.info(f"复制文件：{src_path} → {dest_path}")
                    record_copied_file(src_path)
                except FileNotFoundError:
                    print(f"文件 {src_path} 未找到，可能 U 盘已拔出。")
                    logging.error(f"文件 {src_path} 未找到，可能 U 盘已拔出。")
                    return False
                except PermissionError:
                    print(f"没有权限复制文件 {src_path}。")
                    logging.error(f"没有权限复制文件 {src_path}。")
                except Exception as e:
                    print(f"复制文件 {src_path} 时发生未知错误：{str(e)}")
                    logging.error(f"复制文件 {src_path} 时发生未知错误：{str(e)}")

        print(f"移动存储设备 {usb_name} 内容复制完成！")
        return True
    except FileNotFoundError:
        print(f"U 盘路径 {usb_path} 未找到，可能 U 盘已拔出。")
        logging.error(f"U 盘路径 {usb_path} 未找到，可能 U 盘已拔出。")
        return False
    except Exception as e:
        logging.error(f"复制失败：{str(e)}")
        print(f"错误：{str(e)}")
        return False


def is_removable_disk(disk_path):
    """判断磁盘是否为可移动磁盘"""
    wmi_obj = wmi.WMI()
    for logical_disk in wmi_obj.Win32_LogicalDisk(Caption=disk_path):
        for partition in logical_disk.associators("Win32_LogicalDiskToPartition"):
            for disk_drive in partition.associators("Win32_DiskDriveToDiskPartition"):
                if disk_drive.InterfaceType.lower() == "usb":
                    return True
    return False


def monitor_usb_devices():
    """监控可移动磁盘，仅处理新插入的设备"""
    processed_disks = set()  # 记录已处理的磁盘盘符（如 "F:\\"）
    wmi_obj = wmi.WMI()

    while True:
        for disk in wmi_obj.Win32_LogicalDisk():
            disk_path = disk.Caption  # 盘符（带末尾反斜杠，如 "F:\\"）
            if is_removable_disk(disk_path):
                if disk_path not in processed_disks:
                    processed_disks.add(disk_path)
                    usb_name = disk.VolumeName if disk.VolumeName else disk_path.strip(":\\")
                    print(f"检测到新移动存储设备：{disk_path}，卷标：{usb_name}")
                    result = copy_usb_content(disk_path, usb_name)
                    if not result:
                        # 若复制失败，从已处理集合中移除该磁盘路径
                        processed_disks.remove(disk_path)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    print(f"开始监控移动存储设备，日志已记录到：{LOG_FILE}")
    try:
        monitor_usb_devices()
    except KeyboardInterrupt:
        print("\n程序已终止（用户中断）")