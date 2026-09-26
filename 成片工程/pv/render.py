"""并行渲染：按帧段分给多个进程，各自管道进 ffmpeg，最后拼接并混入音轨。
用法：
  uv run python pv/render.py                # 全片
  uv run python pv/render.py --still 8.7 47 # 导出指定时刻单帧到 输出/still_*.png
"""
import os, sys, subprocess, argparse
from multiprocessing import Pool
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import FPS, OW, OH, ROOT
import scenes

OUT = os.path.join(ROOT, '输出')
FINAL_DIR = os.path.join(os.path.dirname(ROOT), '成片')

def work(args):
    k, f0, f1 = args
    path = os.path.join(OUT, f'part_{k:03d}.mp4')
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{OW}x{OH}',
           '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '14',
           '-pix_fmt', 'yuv420p', '-tune', 'animation', path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for f in range(f0, f1):
        p.stdin.write(scenes.render_frame(f / FPS).tobytes())
    p.stdin.close()
    p.wait()
    return path

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--still', nargs='*', type=float)
    ap.add_argument('--jobs', type=int, default=28)
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.still:
        for t in a.still:
            scenes.render_frame(t).save(os.path.join(OUT, f'still_{t:06.2f}.png'))
        return
    total = int(scenes.DURATION * FPS)
    n = a.jobs
    step = (total + n - 1) // n
    chunks = [(k, k * step, min(total, (k + 1) * step)) for k in range(n) if k * step < total]
    with Pool(len(chunks)) as pool:
        parts = pool.map(work, chunks)
    lst = os.path.join(OUT, 'parts.txt')
    with open(lst, 'w') as f:
        for pth in parts:
            f.write(f"file '{pth}'\n")
    video = os.path.join(OUT, 'video.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy', video], check=True)
    audio = os.path.join(OUT, 'mix.wav')
    os.makedirs(FINAL_DIR, exist_ok=True)
    final = os.path.join(FINAL_DIR, 'AI公司PV_中文版.mp4')
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', video, '-i', audio, '-map', '0:v', '-map', '1:a',
                    '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k', '-shortest', '-movflags', '+faststart', final], check=True)
    print(final)

if __name__ == '__main__':
    main()
