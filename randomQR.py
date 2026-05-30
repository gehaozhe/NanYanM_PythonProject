import qrcode
import random
import string
import os

def generate_random_string(length=10):
    """
    生成指定长度的随机字符串
    :param length: 字符串长度，默认10
    :return: 随机字符串
    """
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

def generate_qr_code(data, filename=None):
    """
    生成包含指定数据的二维码
    :param data: 要包含在二维码中的数据
    :param filename: 保存二维码的文件名，默认生成随机文件名
    :return: 生成的二维码文件路径
    """
    if not filename:
        # 生成随机文件名
        random_suffix = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(5))
        filename = f"qrcode_{random_suffix}.png"
    
    # 创建QRCode对象
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # 添加数据
    qr.add_data(data)
    qr.make(fit=True)
    
    # 创建图像
    img = qr.make_image(fill_color="black", back_color="white")
    
    # 保存图像
    img.save(filename)
    
    return os.path.abspath(filename)

def main():
    """
    主函数，生成包含随机字符串的二维码
    """
    print("随机二维码生成器")
    print("=" * 30)
    
    # 生成随机字符串
    random_str = generate_random_string()
    print(f"生成的随机字符串: {random_str}")
    
    # 生成二维码
    qr_path = generate_qr_code(random_str)
    print(f"二维码已生成并保存至: {qr_path}")
    
    # 提示用户
    print("\n您可以使用手机或其他设备扫描此二维码来查看随机字符串。")

if __name__ == "__main__":
    try:
        main()
    except ImportError:
        print("错误: 缺少必要的库。请运行以下命令安装:")
        print("pip install qrcode[pil]")
