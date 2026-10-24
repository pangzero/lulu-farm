using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;
using UnityEngine.Profiling;

namespace LuluFarm
{
    // Opt-in raw CPU capture, independent of the historical aggregate recorder.
    // Rotation keeps individual binary files small enough to inspect on a 24 GB machine.
    public sealed class FarmProfilerCaptureR07 : MonoBehaviour
    {
        string folder; float started, chunkStart; int index; bool active;
        readonly List<Chunk> chunks = new List<Chunk>();
        [Serializable] sealed class Chunk { public string file; public float fromSeconds,toSeconds; }
        [Serializable] sealed class CaptureRecord {
            public string utc,method="Unity binary CPU Profiler; 10-second chunks; deep profiling off; rendering/memory counters remain in the separate runtime recorder";
            public string limitation="Chunk rotation flush overhead is included in runtime measurements. Exported timeline is a filtered index; binary data is authoritative. No performance acceptance conclusion.";
            public Chunk[] chunks; public bool developmentBuild; public float elapsedSeconds;
        }
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void AttachRequestedCapture()
        {
            string[] a=Environment.GetCommandLineArgs();int i=Array.IndexOf(a,"--r07-profiler-directory");
            if(i<0)return;
            if(i+1>=a.Length)throw new ArgumentException("Missing --r07-profiler-directory value");
            new GameObject("R07_ProfilerCapture").AddComponent<FarmProfilerCaptureR07>().folder=a[i+1];
        }
        IEnumerator Start()
        {
            if(!Debug.isDebugBuild){Debug.LogError("Raw profiling requires a development player.");yield break;}
            Directory.CreateDirectory(folder);
            // Align to the route recorder's five-second warmup, without taking screenshots.
            yield return new WaitForSecondsRealtime(5);
            started=Time.realtimeSinceStartup; active=true;
            Profiler.enabled=false;Profiler.maxUsedMemory=128*1024*1024;
            foreach(ProfilerArea area in Enum.GetValues(typeof(ProfilerArea)))
                Profiler.SetAreaEnabled(area,area==ProfilerArea.CPU);
            NextChunk();
        }
        void Update(){if(active&&Time.realtimeSinceStartup-chunkStart>=10)NextChunk();}
        void NextChunk()
        {
            CloseChunk();chunkStart=Time.realtimeSinceStartup;
            string file="cpu-"+(index++).ToString("D4")+".data";
            chunks.Add(new Chunk{file=file,fromSeconds=chunkStart-started});
            Profiler.logFile=Path.GetFullPath(Path.Combine(folder,file));
            Profiler.enableBinaryLog=true;Profiler.enabled=true;
        }
        void CloseChunk()
        {
            Profiler.enabled=false;Profiler.enableBinaryLog=false;Profiler.logFile="";
            if(chunks.Count>0)chunks[chunks.Count-1].toSeconds=Time.realtimeSinceStartup-started;
        }
        void OnApplicationQuit(){Finish();}
        void OnDestroy(){Finish();}
        void Finish()
        {
            if(!active)return;active=false;CloseChunk();
            File.WriteAllText(Path.Combine(folder,"capture.json"),JsonUtility.ToJson(new CaptureRecord {
                utc=DateTime.UtcNow.ToString("o"),developmentBuild=Debug.isDebugBuild,elapsedSeconds=Time.realtimeSinceStartup-started,chunks=chunks.ToArray()},true));
        }
    }
}
