import os
from PIL import Image
import concurrent.futures
from pathlib import Path

def compress_image(input_path, output_dir, quality=85, max_size=(1920, 1080)):
    """
    压缩单张图片
    
    参数:
    input_path: 输入图片路径
    output_dir: 输出目录
    quality: 压缩质量 (1-100)
    max_size: 最大尺寸 (宽, 高)
    """
    try:
        # 打开图片
        with Image.open(input_path) as img:
            # 保持原始格式
            img_format = img.format if img.format else 'JPEG'
            
            # 计算新的尺寸，保持宽高比
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 确定输出文件名和路径
            filename = Path(input_path).stem
            output_filename = f"{filename}_compressed.{img.format.lower()}"
            output_path = os.path.join(output_dir, output_filename)
            
            # 保存压缩后的图片
            if img_format in ['JPEG', 'JPG']:
                img.save(output_path, quality=quality, optimize=True)
            elif img_format == 'PNG':
                img.save(output_path, optimize=True)
            else:
                img.save(output_path, quality=quality)
            
            print(f"✓ 已压缩: {os.path.basename(input_path)} -> {output_filename}")
            
            # 计算压缩率
            original_size = os.path.getsize(input_path)
            compressed_size = os.path.getsize(output_path)
            ratio = (1 - compressed_size / original_size) * 100
            
            return {
                'original': os.path.basename(input_path),
                'compressed': output_filename,
                'original_size': original_size,
                'compressed_size': compressed_size,
                'compression_ratio': ratio
            }
    
    except Exception as e:
        print(f"✗ 压缩失败 {os.path.basename(input_path)}: {str(e)}")
        return None

def compress_all_images(input_dir='.', output_dir='yasuo', quality=85, max_width=1920):
    """
    压缩目录下所有图片
    
    参数:
    input_dir: 输入目录，默认为当前目录
    output_dir: 输出目录名
    quality: 压缩质量 (1-100)
    max_width: 最大宽度
    """
    # 支持的图片格式
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp']
    
    # 创建输出目录
    output_path = os.path.join(input_dir, output_dir)
    os.makedirs(output_path, exist_ok=True)
    
    # 获取所有图片文件
    image_files = []
    for root, dirs, files in os.walk(input_dir):
        # 跳过输出目录
        if output_dir in root:
            continue
            
        for file in files:
            if any(file.lower().endswith(ext) for ext in image_extensions):
                full_path = os.path.join(root, file)
                image_files.append(full_path)
    
    if not image_files:
        print("未找到图片文件！")
        return []
    
    print(f"找到 {len(image_files)} 张图片需要压缩")
    print(f"输出目录: {output_path}")
    print("-" * 50)
    
    # 使用多线程加速处理
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for img_file in image_files:
            # 为每张图片设置最大尺寸，保持宽高比
            img = Image.open(img_file)
            max_height = int(max_width * img.height / img.width)
            img.close()
            
            future = executor.submit(
                compress_image,
                img_file,
                output_path,
                quality,
                (max_width, max_height)
            )
            futures.append(future)
        
        # 收集结果
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            if result:
                results.append(result)
    
    # 显示统计信息
    print("\n" + "=" * 50)
    print("压缩完成！")
    print("=" * 50)
    
    if results:
        total_original = sum(r['original_size'] for r in results)
        total_compressed = sum(r['compressed_size'] for r in results)
        total_saved = total_original - total_compressed
        total_ratio = (1 - total_compressed / total_original) * 100
        
        print(f"处理图片数量: {len(results)}")
        print(f"原始总大小: {total_original / 1024 / 1024:.2f} MB")
        print(f"压缩后总大小: {total_compressed / 1024 / 1024:.2f} MB")
        print(f"节省空间: {total_saved / 1024 / 1024:.2f} MB")
        print(f"总体压缩率: {total_ratio:.1f}%")
        
        # 显示压缩效果最好的5张图片
        if len(results) > 5:
            print("\n压缩效果最好的5张图片:")
            sorted_results = sorted(results, key=lambda x: x['compression_ratio'], reverse=True)
            for i, r in enumerate(sorted_results[:5], 1):
                print(f"{i}. {r['original']}: {r['compression_ratio']:.1f}%")
    
    return results

def main():
    """主函数"""
    print("图片批量压缩工具")
    print("=" * 50)
    
    # 获取用户输入
    try:
        quality = int(input("请输入压缩质量 (1-100，推荐85): ") or "85")
        quality = max(1, min(100, quality))  # 确保在有效范围内
        
        max_width = int(input("请输入最大宽度 (像素，推荐1920): ") or "1920")
        max_width = max(100, min(10000, max_width))  # 限制范围
        
        use_current_dir = input("使用当前目录？(y/n, 默认y): ").lower() or 'y'
        
        if use_current_dir == 'y':
            input_dir = '.'
        else:
            input_dir = input("请输入图片所在目录: ")
            if not os.path.exists(input_dir):
                print("目录不存在！")
                return
        
        print("\n开始压缩图片...")
        results = compress_all_images(
            input_dir=input_dir,
            output_dir='yasuo',
            quality=quality,
            max_width=max_width
        )
        
    except ValueError:
        print("输入无效！请确保输入的是数字。")
    except KeyboardInterrupt:
        print("\n\n程序被用户中断。")
    except Exception as e:
        print(f"发生错误: {str(e)}")

if __name__ == "__main__":
    # 安装所需库（如果未安装）
    try:
        from PIL import Image
    except ImportError:
        print("正在安装所需库...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'Pillow'])
        print("安装完成，请重新运行程序。")
        exit()
    
    main()