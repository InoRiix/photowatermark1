import os
import sys
import argparse
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import piexif

# 支持的图片格式
IMG_EXTS = {'.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG'}
# 位置映射
POSITION_MAP = {
    'lt': 'left-top',
    'rt': 'right-top',
    'lb': 'left-bottom',
    'rb': 'right-bottom',
    'c': 'center',
}


def parse_args():
    parser = argparse.ArgumentParser(description='批量为图片添加拍摄日期水印')
    parser.add_argument('-i', '--input', required=True, help='图片文件或目录路径')
    parser.add_argument('-s', '--font-size', type=int, default=24, help='水印字体大小，默认24，最大48')
    parser.add_argument('-c', '--font-color', default='black', help='水印字体颜色，支持英文名、#RRGGBB、RGB三元组')
    parser.add_argument('-p', '--position', default='rb', choices=POSITION_MAP.keys(), help='水印位置，lt/rt/lb/rb/c')
    return parser.parse_args()


def is_image_file(path):
    return Path(path).suffix.lower() in IMG_EXTS


def get_all_images(input_path):
    p = Path(input_path)
    if p.is_file() and is_image_file(p):
        return [p]
    elif p.is_dir():
        return [f for f in p.rglob('*') if is_image_file(f)]
    else:
        return []


def get_exif_date(img_path):
    try:
        exif_dict = piexif.load(str(img_path))
        dt = exif_dict['Exif'].get(piexif.ExifIFD.DateTimeOriginal)
        if dt:
            dt_str = dt.decode() if isinstance(dt, bytes) else dt
            return dt_str.split(' ')[0].replace(':', '-')
    except Exception:
        pass
    return '无拍摄时间'


def calc_position(pos, img_size, text_size, margin=10):
    W, H = img_size
    w, h = text_size
    if pos == 'lt':
        return (margin, margin)
    elif pos == 'rt':
        return (W - w - margin, margin)
    elif pos == 'lb':
        return (margin, H - h - margin)
    elif pos == 'rb':
        return (W - w - margin, H - h - margin)
    elif pos == 'c':
        return ((W - w) // 2, (H - h) // 2)
    else:
        return (margin, margin)


def add_watermark(img_path, out_path, font_size, font_color, position):
    try:
        img = Image.open(img_path).convert('RGB')
        date_str = get_exif_date(img_path)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("simhei.ttf", font_size)
            print("字体加载成功")
        except Exception:
            font = ImageFont.load_default()
            print("moren")
        text = date_str
        # 兼容 Pillow 10+，用 textbbox 获取文本尺寸
        bbox = draw.textbbox((0, 0), text, font=font)
        text_size = (bbox[2] - bbox[0], bbox[3] - bbox[1])
        xy = calc_position(position, img.size, text_size)
        draw.text(xy, text, fill=font_color, font=font)
        img.save(out_path)
        print(f"[成功] {img_path} -> {out_path}")
    except Exception as e:
        print(f"[失败] {img_path}: {e}")


def main():
    args = parse_args()
    if args.font_size <= 0 or args.font_size > 48:
        print('字体大小需为1-48之间的正整数')
        sys.exit(1)
    input_path = Path(args.input)
    if not input_path.exists():
        print('输入路径不存在')
        sys.exit(1)
    images = get_all_images(input_path)
    if not images:
        print('未找到图片文件')
        sys.exit(1)
    # 输出目录
    if input_path.is_file():
        out_dir = input_path.parent / 'watermark'
    else:
        out_dir = input_path.parent / (input_path.name + '_watermark')
    out_dir.mkdir(exist_ok=True)
    for img_path in images:
        out_path = out_dir / img_path.name
        add_watermark(img_path, out_path, args.font_size, args.font_color, args.position)
    print(f'处理完成，结果保存在：{out_dir}')


if __name__ == '__main__':
    main()
