"""切割精灵表/图标表/头像表，底图像素化到 480x270 原生网格。"""
from PIL import Image, ImageFilter
import numpy as np
from scipy import ndimage
import os, json
B='底图'; A='资产'
NAMES={
 'R_精灵表1':['founder_walk','founder_cheer','founder_bow','hoodie_shock','hoodie_thumb',
             'ceo_slump','emp_kneel','emp_coffee','investor_bag','singer',
             'guitar','fan_green','fan_pink','robot','cat'],
 'R_精灵表2':['emp_type','girl_type','emp_sleep','scientist','intern_papers',
             'gpu_hug','sign_hold','biz_sweat','emp_toast','girl_confetti'],
 'R_图标表':['gpu','moneybag','coin','trophy','bulb','glowstick','note','star','heart','rocket','mushroom','crown'],
}
def blobs(alpha, dil=18):
    m = alpha > 40
    lab, n = ndimage.label(ndimage.binary_dilation(m, iterations=dil))
    boxes=[]
    for sl in ndimage.find_objects(lab):
        ys, xs = sl
        sub = m[sl]
        if sub.sum() < 800: continue
        boxes.append((xs.start, ys.start, xs.stop, ys.stop))
    # 行优先排序：按中心 y 聚类成行
    boxes.sort(key=lambda b:(b[1]+b[3])/2)
    rows=[]; 
    for b in boxes:
        cy=(b[1]+b[3])/2
        if rows and abs(cy-rows[-1][0])<120: rows[-1][1].append(b)
        else: rows.append([cy,[b]])
    out=[]
    for _,r in rows: out += sorted(r,key=lambda b:b[0])
    return out
meta={}
for sheet,names in NAMES.items():
    im=Image.open(f'{B}/{sheet}.png').convert('RGBA')
    a=np.array(im)[:,:,3]
    bx=blobs(a, 10 if sheet=='R_精灵表1' else 18)
    print(sheet,len(bx),'blobs; expect',len(names))
    sub = '图标' if sheet=='R_图标表' else '精灵'
    for nm,b in zip(names,bx):
        crop=im.crop(b)
        arr=np.array(crop); arr[:,:,3]=np.where(arr[:,:,3]>110,255,0); 
        Image.fromarray(arr).save(f'{A}/{sub}/{nm}.png')
        meta[nm]={'box':b,'size':crop.size}
# 头像表：灰底 → 透明
im=Image.open(f'{B}/R_头像表.png').convert('RGB'); arr=np.array(im).astype(int)
bg=np.abs(arr-np.array([206,206,206])).sum(2)>30
lab,n=ndimage.label(ndimage.binary_dilation(bg,iterations=4))
bx=[]
for sl in ndimage.find_objects(lab):
    ys,xs=sl
    if bg[sl].sum()>5000: bx.append((xs.start,ys.start,xs.stop,ys.stop))
bx.sort(key=lambda b:(b[1]>400,b[0]))
print('portraits',len(bx))
for i,b in enumerate(bx[:6]):
    c=Image.open(f'{B}/R_头像表.png').convert('RGBA').crop(b)
    ca=np.array(c); m=np.abs(ca[:,:,:3].astype(int)-206).sum(2)<=30; ca[m,3]=0
    Image.fromarray(ca).save(f'{A}/头像/p{i+1}.png')
# 底图：box 降采样到 480x270 + 调色板量化（保持像素网格）
for f in sorted(os.listdir(B)):
    if not f.startswith('P') or not f.endswith('.png'): continue
    im=Image.open(f'{B}/{f}').convert('RGB')
    small=im.resize((480,270),Image.BOX)
    q=small.quantize(colors=64,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE).convert('RGB')
    q.save(f'{A}/底图480/{f}')
json.dump(meta,open(f'{A}/精灵元数据.json','w'),ensure_ascii=False,indent=1)
