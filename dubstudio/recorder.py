import queue, threading
import numpy as np
import sounddevice as sd
import soundfile as sf
from .core import RATE

class Recorder:
    def __init__(self,path,device,limit):
        self.path=path; self.frames=0; self.limit=round(limit*RATE)
        self.peak=0.; self.error=None; self.q=queue.Queue(); self.stream=None
        self.writer=threading.Thread(target=self.write,daemon=True)
        self.device=device
    def write(self):
        try:
            with sf.SoundFile(self.path,'w',samplerate=RATE,channels=1,subtype='PCM_24') as f:
                while True:
                    block=self.q.get()
                    if block is None: break
                    f.write(block)
        except Exception as e: self.error=str(e)
    def callback(self,data,frames,timing,status):
        if status: self.error='O microfone perdeu amostras. Tente gravar novamente.'
        count=min(len(data),max(0,self.limit-self.frames))
        if count:
            block=data[:count,0].copy(); self.q.put(block)
            self.frames+=count; self.peak=float(np.max(np.abs(block)))
    def start(self):
        self.stream=sd.InputStream(samplerate=RATE,channels=1,dtype='float32',device=self.device,callback=self.callback)
        self.writer.start()
        try: self.stream.start()
        except Exception:
            self.stream.close(); self.q.put(None); self.writer.join(); raise
    def stop(self):
        if self.stream: self.stream.stop(); self.stream.close()
        self.q.put(None); self.writer.join()
