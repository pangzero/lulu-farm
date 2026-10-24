using System;
using System.Collections;
using System.IO;
using UnityEngine;
using UnityEngine.UI;

namespace LuluFarm
{
    // Opt-in real player capture. Diagnostic fixed cameras are not exposed as a gameplay mode.
    public sealed class FarmAmbientEvidenceR07:MonoBehaviour
    {
        FarmRuntimeBootstrap runtime;FarmAmbientR07 ambient;string folder;StreamWriter samples;
        readonly float[] audio=new float[512];float next;
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Attach(){if(Array.IndexOf(Environment.GetCommandLineArgs(),"--r07-ambient-evidence")>=0)new GameObject("R07_ActualAmbientEvidence").AddComponent<FarmAmbientEvidenceR07>();}
        IEnumerator Start()
        {
            while((runtime=FindFirstObjectByType<FarmRuntimeBootstrap>())==null||!runtime.Initialized)yield return null;
            ambient=FindFirstObjectByType<FarmAmbientR07>();if(ambient==null)throw new InvalidOperationException("D6 ambient scene required");
            var presentation=runtime.GetComponent<FarmPresentationModeR07>();
            while(!presentation.Ready)yield return null;yield return new WaitForSecondsRealtime(2);
            folder=Path.Combine(runtime.Diagnostics.OutputDirectory,"ambient-proof");Directory.CreateDirectory(folder);
            samples=new StreamWriter(Path.Combine(folder,"actual-runtime.jsonl"));
            presentation.SetDebug(true);var panel=runtime.transform.Find("FarmHUD/SafeArea/Inspection");panel.gameObject.SetActive(true);
            yield return Capture("01-options-on");
            panel.Find("WindSetting").GetComponent<Button>().onClick.Invoke();panel.Find("SoundSetting").GetComponent<Button>().onClick.Invoke();
            yield return new WaitForSecondsRealtime(.5f);yield return Capture("02-options-off");
            runtime.SetQuality(0);yield return new WaitForSecondsRealtime(.5f);yield return Capture("03-mobile-options");
            runtime.SetQuality(1);panel.Find("WindSetting").GetComponent<Button>().onClick.Invoke();panel.Find("SoundSetting").GetComponent<Button>().onClick.Invoke();
            yield return new WaitForSecondsRealtime(.5f);yield return Capture("04-desktop-options-restored");presentation.SetDebug(false);
            runtime.CameraRig.enabled=false;runtime.CameraRig.brain.enabled=false;
            runtime.Recorder.requestedFramesPerSecond=10;runtime.Recorder.maximumSeconds=65;
            runtime.Recorder.BeginRecording();
            Vector3[] positions={new Vector3(-4.1f,1.3f,-3),new Vector3(2.1f,1.1f,-5.6f),new Vector3(-1.1f,1.8f,2.3f),new Vector3(10.9f,1.6f,-.5f)};
            Vector3[] targets={new Vector3(-1.7f,.55f,-.3f),new Vector3(.7f,.45f,-4.3f),new Vector3(-2.8f,.75f,5),new Vector3(11.7f,-.098f,1.4f)};
            for(int i=0;i<positions.Length;i++){
                runtime.mainCamera.transform.position=positions[i];runtime.mainCamera.transform.LookAt(targets[i]);
                runtime.Diagnostics.RecordEvent("r07_diagnostic_fixed_camera_"+i);
                yield return new WaitForSecondsRealtime(1);yield return Capture("motion-"+i+"-start");
                yield return new WaitForSecondsRealtime(13);yield return Capture("motion-"+i+"-end");
            }
            runtime.Recorder.StopRecording("ambient_diagnostic_sequence_finished");samples?.Flush();
        }
        void Update(){
            if(samples==null||Time.realtimeSinceStartup<next)return;next=Time.realtimeSinceStartup+.5f;
            AudioListener.GetOutputData(audio,0);float sum=0;foreach(float x in audio)sum+=x*x;
            samples.WriteLine(JsonUtility.ToJson(new Sample{utc=DateTime.UtcNow.ToString("o"),elapsed=Time.realtimeSinceStartup,shaderTime=Shader.GetGlobalFloat("_FarmR07Time"),wind=Shader.GetGlobalFloat("_FarmR07WindEnabled"),sound=ambient.soundEnabled,birdsPlaying=ambient.birds.isPlaying,waterPlaying=ambient.water.isPlaying,birdsMuted=ambient.birds.mute,waterMuted=ambient.water.mute,audioRms=Mathf.Sqrt(sum/audio.Length),quality=runtime.QualityLabel,camera=runtime.mainCamera.transform.position}));samples.Flush();
        }
        IEnumerator Capture(string name){yield return new WaitForEndOfFrame();ScreenCapture.CaptureScreenshot(Path.Combine(folder,name+".png"));}
        void OnDestroy(){samples?.Dispose();}
        [Serializable] sealed class Sample {public string utc,quality;public float elapsed,shaderTime,wind,audioRms;public bool sound,birdsPlaying,waterPlaying,birdsMuted,waterMuted;public Vector3 camera;}
    }
}
