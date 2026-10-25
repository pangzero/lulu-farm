using System;
using System.IO;
using UnityEngine;

namespace LuluFarm
{
    // Opt-in capture of the game AudioListener mix, never microphone/system audio.
    // Used only alongside the diagnostic movie, never during performance sampling.
    public sealed class FarmOutputAudioCaptureR07:MonoBehaviour
    {
        readonly object gate=new object();FileStream stream;BinaryWriter writer;string filename;
        int rate,channels;long samples;float peak;byte[] bytes;bool active;
        public void Begin(string path){
            lock(gate){filename=path;rate=AudioSettings.outputSampleRate;stream=new FileStream(path,FileMode.CreateNew,FileAccess.Write,FileShare.Read);writer=new BinaryWriter(stream);writer.Write(new byte[44]);active=true;}
        }
        void OnAudioFilterRead(float[] data,int count){
            lock(gate){if(!active||writer==null)return;channels=count;
                if(bytes==null||bytes.Length!=data.Length*4)bytes=new byte[data.Length*4];
                Buffer.BlockCopy(data,0,bytes,0,bytes.Length);writer.Write(bytes);samples+=data.Length;
                foreach(float value in data)peak=Math.Max(peak,Math.Abs(value));
            }
        }
        public void Finish(){
            lock(gate){if(!active)return;active=false;int ch=Math.Max(1,channels);int dataBytes=checked((int)(samples*4));
                stream.Position=0;writer.Write(System.Text.Encoding.ASCII.GetBytes("RIFF"));writer.Write(dataBytes+36);writer.Write(System.Text.Encoding.ASCII.GetBytes("WAVEfmt "));writer.Write(16);writer.Write((short)3);writer.Write((short)ch);writer.Write(rate);writer.Write(rate*ch*4);writer.Write((short)(ch*4));writer.Write((short)32);writer.Write(System.Text.Encoding.ASCII.GetBytes("data"));writer.Write(dataBytes);writer.Flush();writer.Dispose();writer=null;stream=null;
                File.WriteAllText(filename+".json",JsonUtility.ToJson(new Record{utc=DateTime.UtcNow.ToString("o"),sampleRate=rate,channels=ch,samples=samples,seconds=(double)samples/ch/rate,peak=peak,status=samples>0?"actual_listener_callback_samples_captured":"no_audio_callback_samples_not_verified"},true));
            }
        }
        void OnDestroy(){Finish();}
        [Serializable] sealed class Record {public string utc,status,source="Actual Unity AudioListener output, float32 WAV. No microphone. No synthetic replacement of captured samples.",review="Audible quality pending human/Opus review; video is separately captured and has no muxed audio track.";public int sampleRate,channels;public long samples;public double seconds;public float peak;}
    }
}
