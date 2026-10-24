using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace LuluFarm.Editor
{
    public static partial class FarmProjectBuilder
    {
        public static string R07Task {
            get { var a=Environment.GetCommandLineArgs(); int i=Array.IndexOf(a,"--r07-task");
                string task=i>=0&&i+1<a.Length?a[i+1]:"D6";
                if(!new[]{"D5","D2","D3","D4","D6","O6"}.Contains(task))throw new InvalidOperationException("Unexpected r07 task: "+task);
                return task; }
        }
        // O6 is the Opus integration stage: everything D6 enables plus the O3/O5 revisions.
        // D5–D6 remain reproducible exactly as delivered; nothing below changes when --r07-task is D*.
        public static bool R07Living=>R07Task=="D6"||R07Task=="O6";
        public static bool R07Opus=>R07Task=="O6";
        public static void R07GenerateReview()
        {
            string folder="Evidence/r07/"+R07Task;Directory.CreateDirectory(folder);
            FarmWorldReview.GenerateAndReview();
            string source=File.ReadAllText("Evidence/latest-world-review.txt").Trim();
            CopyR07Folder(source,folder+"/fixed");
            FarmReviewShotsR07.CaptureCurrent();
            foreach(string f in new[]{"scene-contact-audit.json","scene-generation-status.json","scene-build-issues.txt"})
                File.Copy("Evidence/"+f,folder+"/"+f,true);
            var report=Directory.GetFiles("Evidence/acceptance","static-validation.json",SearchOption.AllDirectories).OrderByDescending(File.GetLastWriteTimeUtc).First();
            File.Copy(report,folder+"/static-validation.json",true);
        }
        public static void R07BuildDevelopment()=>R07Build(false);
        public static void R07BuildRelease()=>R07Build(true);
        static void R07Build(bool release)
        {
            RequireCurrentStamp("Evidence/scene-generation-status.json","generated_pending_actual_play_and_visual_checks");
            PreparePlayerRendering();
            string flavor=release?"release":"development", folder="Builds/r07/"+R07Task+"/"+flavor;
            Directory.CreateDirectory(folder);
            var report=BuildPipeline.BuildPlayer(new BuildPlayerOptions { scenes=new[]{Base+"Scenes/FarmWorld.unity"},
                locationPathName=folder+"/LuluFarm.app",target=BuildTarget.StandaloneOSX,
                options=release?BuildOptions.None:BuildOptions.Development });
            SaveBuildReport(report,"r07-"+R07Task+"-"+flavor);
            File.Copy("Evidence/build-r07-"+R07Task+"-"+flavor+".json","Evidence/r07/"+R07Task+"/build-"+flavor+".json",true);
        }
        static void CopyR07Folder(string source,string target)
        {
            Directory.CreateDirectory(target);
            foreach(var path in Directory.GetFiles(source))File.Copy(path,Path.Combine(target,Path.GetFileName(path)),true);
        }
    }
}
