import librosa, numpy as np, json, sys
from faster_whisper import WhisperModel
p='../音频/FlyMeToTheMoon-小野丽莎.flac'
y,sr=librosa.load(p,sr=22050,mono=True)
tempo,beats=librosa.beat.beat_track(y=y,sr=sr,units='time')
print('tempo',tempo, 'nbeats',len(beats)); print('beats[:40]',np.round(beats[:40],2).tolist())
rms=librosa.feature.rms(y=y)[0]; t=librosa.times_like(rms,sr=sr)
for s in range(0,224,4): print(s, round(float(20*np.log10(rms[(t>=s)&(t<s+4)].mean()+1e-9)),1), end=' | ')
print()
m=WhisperModel('分析/fw-medium',device='cpu',compute_type='int8')
segs,_=m.transcribe(p,language='en',word_timestamps=True,vad_filter=False)
out=[]
for s in segs:
    print(f'{s.start:7.2f}-{s.end:7.2f} {s.text}')
    out.append({'start':s.start,'end':s.end,'text':s.text,'words':[{'w':w.word,'s':w.start,'e':w.end} for w in s.words]})
json.dump({'tempo':float(np.atleast_1d(tempo)[0]),'beats':beats.tolist(),'segments':out},open('分析/audio.json','w'),ensure_ascii=False,indent=1)
