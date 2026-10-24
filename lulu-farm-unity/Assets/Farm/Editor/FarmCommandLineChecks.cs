using System;
using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
namespace LuluFarm.Editor
{
    [InitializeOnLoad] public static class FarmCommandLineChecks
    {
        const string Key="Farm.CLI.CameraRegression";
        static FarmCommandLineChecks(){EditorApplication.playModeStateChanged+=State;EditorApplication.update+=Tick;}
        public static void CameraRegression()
        {
            EditorSceneManager.OpenScene("Assets/Farm/Scenes/FarmCalibration.unity");
            SessionState.SetBool(Key,true);SessionState.SetBool(Key+"Started",false);
            SessionState.SetFloat(Key+"Time",(float)EditorApplication.timeSinceStartup);
            EditorApplication.isPlaying=true;
        }
        static void State(PlayModeStateChange state)
        {
            if(!SessionState.GetBool(Key,false))return;
            if(state==PlayModeStateChange.EnteredPlayMode)EditorApplication.delayCall+=()=>{
                CameraOcclusionRegression.Run();SessionState.SetBool(Key+"Started",true);
            };
            if(state==PlayModeStateChange.EnteredEditMode){SessionState.SetBool(Key,false);EditorApplication.Exit(0);}
        }
        static void Tick()
        {
            if(!SessionState.GetBool(Key,false))return;
            if(EditorApplication.timeSinceStartup-SessionState.GetFloat(Key+"Time",0)>90){SessionState.SetBool(Key,false);Debug.LogError("Camera regression timed out");EditorApplication.Exit(2);}
            if(EditorApplication.isPlaying&&SessionState.GetBool(Key+"Started",false)&&UnityEngine.Object.FindFirstObjectByType<CameraOcclusionRegressionRunner>()==null)EditorApplication.isPlaying=false;
        }
        public static void FullWorldAndMac()
        {
            FarmWorldReview.GenerateAndReview();
            FarmProjectBuilder.BuildMac();
        }
    }
}
