using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Globalization;
using System.IO.Compression;
using System.Collections.Generic;
using UnityEditor;
using UnityEditorInternal;
using UnityEngine;

namespace LuluFarm.Editor
{
    public static class FarmProfilerExportR07
    {
        public static void Export()
        {
            string folder="Evidence/r07/"+FarmProjectBuilder.R07Task+"/profiler";
            var args=Environment.GetCommandLineArgs();int option=Array.IndexOf(args,"--r07-profiler-directory");
            if(option>=0&&option+1<args.Length)folder=args[option+1];
            string[] files=Directory.GetFiles(folder,"*.data").OrderBy(p=>p).ToArray();
            if(files.Length==0)throw new InvalidOperationException("No real binary capture in "+folder);
            // SetMaxFrameHistoryLength is non-public in the locked editor; keep the change in this process only.
            typeof(ProfilerDriver).GetMethod("SetMaxFrameHistoryLength",BindingFlags.Static|BindingFlags.Public|BindingFlags.NonPublic).Invoke(null,new object[]{2000});
            var records=new List<ExportRecord>();
            foreach(string file in files)
            {
                string output=Path.ChangeExtension(file,"timeline.json.gz");
                if(File.Exists(output)&&File.Exists(output+".json")){records.Add(JsonUtility.FromJson<ExportRecord>(File.ReadAllText(output+".json")));continue;}
                ProfilerDriver.ClearAllFrames();
                if(!ProfilerDriver.LoadProfile(Path.GetFullPath(file),false)){
                    var failure=new ExportRecord{file=file,status="binary_load_rejected_by_Unity_retained_for_review"};
                    records.Add(failure);File.WriteAllText(file+".export-error.json",JsonUtility.ToJson(failure,true));continue;
                }
                var report=new ExportRecord {file=file,output=output,firstFrame=ProfilerDriver.firstFrameIndex,lastFrame=ProfilerDriver.lastFrameIndex};
                bool first=true;
                using(var stream=new FileStream(output,FileMode.CreateNew))
                using(var zip=new GZipStream(stream,System.IO.Compression.CompressionLevel.Fastest))
                using(var w=new StreamWriter(zip))
                {
                    w.Write("{\"displayTimeUnit\":\"ms\",\"traceEvents\":[");
                    for(int f=report.firstFrame;f<=report.lastFrame;f++)
                    {
                        bool gotFrame=false;
                        for(int thread=0;thread<128;thread++)
                        using(var view=ProfilerDriver.GetRawFrameDataView(f,thread))
                        {
                            if(!view.valid)break;
                            gotFrame=true;report.threads=Math.Max(report.threads,thread+1);
                            for(int s=0;s<view.sampleCount;s++)
                            {
                                float ms=view.GetSampleTimeMs(s);
                                // Retain all >=0.1 ms markers on every thread plus the frame root.
                                // Full sub-0.1 ms data stays in the .data for later Opus diagnosis.
                                if(s!=0&&ms<.1f)continue;
                                if(!first)w.Write(',');first=false;
                                w.Write("{\"ph\":\"X\",\"pid\":1,\"tid\":");w.Write(thread);
                                w.Write(",\"name\":");w.Write(Quote(view.GetSampleName(s)));
                                w.Write(",\"ts\":");w.Write((view.GetSampleStartTimeMs(s)*1000).ToString("R",CultureInfo.InvariantCulture));
                                w.Write(",\"dur\":");w.Write((ms*1000).ToString("R",CultureInfo.InvariantCulture));
                                w.Write(",\"args\":{\"frame\":");w.Write(f);w.Write(",\"thread\":");w.Write(Quote(view.threadName));w.Write("}}");report.events++;
                            }
                        }
                        if(gotFrame)report.frames++;
                    }
                    w.Write("]}");
                }
                File.WriteAllText(output+".json",JsonUtility.ToJson(report,true));records.Add(report);
            }
            File.WriteAllText(Path.Combine(folder,"export-index.json"),JsonUtility.ToJson(new ExportIndex{utc=DateTime.UtcNow.ToString("o"),chunks=records.ToArray()},true));
        }
        static string Quote(string s)=>"\""+(s??"").Replace("\\","\\\\").Replace("\"","\\\"").Replace("\n","\\n").Replace("\r","\\r").Replace("\t","\\t")+"\"";
        [Serializable] sealed class ExportRecord {public string file,output,status="exported_filtered_timeline_binary_retained";public int firstFrame,lastFrame,frames,threads;public long events;}
        [Serializable] sealed class ExportIndex {public string utc;public string method="raw .data read by locked Unity ProfilerDriver; Chrome Trace gzip; samples >=0.1 ms plus roots; binary captures preserve all markers";public ExportRecord[] chunks;}
        // Local locked-editor API inventory, used before implementing an exporter.
        public static void InspectAPI()
        {
            // D5–D6 keep writing the delivered D7 listing; the Opus O6 stage writes its own copy.
            string apiFolder=FarmProjectBuilder.R07Task=="O6"?"Evidence/r07/O6":"Evidence/r07/D7";
            Directory.CreateDirectory(apiFolder);
            using(var w=new StreamWriter(apiFolder+"/profiler-api.txt"))
            foreach(var type in new[]{typeof(ProfilerDriver),typeof(ProfilerDriver).GetMethod("GetRawFrameDataView")?.ReturnType,typeof(ProfilerDriver).Assembly.GetType("UnityEditorInternal.ProfilerUserSettings")}.Where(t=>t!=null))
            {
                w.WriteLine(type.FullName);
                foreach(var m in type.GetMembers(BindingFlags.Public|BindingFlags.NonPublic|BindingFlags.Static|BindingFlags.Instance).OrderBy(m=>m.Name)) w.WriteLine(m);
            }
        }
    }
}
