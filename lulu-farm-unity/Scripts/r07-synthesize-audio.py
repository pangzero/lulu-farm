#!/usr/bin/env python3
"""Original deterministic signal synthesis: no downloaded samples or model weights."""
import hashlib, json, math, pathlib, random, struct, wave
root=pathlib.Path(__file__).resolve().parents[1]
out=root/'Assets/Farm/Audio/R07';out.mkdir(parents=True,exist_ok=True)
rate=24000;seconds=24;n=rate*seconds
bird=[0.0]*n
for start,freq,duration in [(1.2,2200,.18),(1.53,2800,.14),(6.4,1950,.22),(6.76,2450,.18),(7.08,2900,.12),(14.5,2350,.2),(14.85,2800,.15),(20.0,2050,.18),(20.3,2600,.14)]:
    count=int(duration*rate);phase=0
    for k in range(count):
        u=k/count;phase+=2*math.pi*(freq+800*math.sin(u*math.pi)*math.sin(u*2))/rate
        bird[int(start*rate)+k]+=.22*math.sin(math.pi*u)**2*(math.sin(phase)+.15*math.sin(phase*2))
rng=random.Random(240724);water=[];slow=fast=0
for i in range(n):
    noise=rng.uniform(-1,1);slow+=.025*(noise-slow);fast+=.19*(noise-fast)
    t=i/rate;envelope=(.68+.1*math.sin(2*math.pi*t/8)+.06*math.sin(2*math.pi*t/3))
    # Smooth endpoints prevent the loop seam clicking; no impact on source asset files.
    fade=min(1,t/.6,(seconds-t)/.6)
    water.append((fast-slow)*.32*envelope*max(0,fade))
records=[]
for name,data in [('bird-chirps.wav',bird),('soft-water.wav',water)]:
    path=out/name
    with wave.open(str(path),'wb') as w:
        w.setnchannels(1);w.setsampwidth(2);w.setframerate(rate)
        w.writeframes(b''.join(struct.pack('<h',round(max(-1,min(1,v))*32767)) for v in data))
    records.append({'file':str(path.relative_to(root)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'seconds':seconds,'sampleRate':rate,'channels':1,'peak':max(abs(v) for v in data)})
record={'source':'Original mathematical signal synthesis by this project script. No third-party recordings, copyrighted samples or downloaded audio.','permission':'Created for the user’s Lulu Farm project; no external attribution or third-party license terms apply. Commercial use is not conditioned on a third-party audio license.','review':'Playback and audible quality remain pending actual runtime review.','generator':str(pathlib.Path(__file__).relative_to(root)),'files':records}
(out/'audio-source.json').write_text(json.dumps(record,ensure_ascii=False,indent=2))
print(json.dumps(records,indent=2))
