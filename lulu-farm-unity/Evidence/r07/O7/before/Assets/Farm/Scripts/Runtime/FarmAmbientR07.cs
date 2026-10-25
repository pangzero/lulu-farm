using System;
using System.Collections;
using UnityEngine;
using UnityEngine.UI;

namespace LuluFarm
{
    public sealed class FarmAmbientR07:MonoBehaviour
    {
        public FarmRuntimeBootstrap runtime;
        public Transform[] butterflies=Array.Empty<Transform>();
        public Renderer[] ripples=Array.Empty<Renderer>();
        public AudioSource birds,water;
        public bool windRequested=true,soundEnabled=true;
        Vector3[] anchors;MaterialPropertyBlock block;Text windLabel,soundLabel;float time;string quality;
        IEnumerator Start()
        {
            anchors=new Vector3[butterflies.Length];for(int i=0;i<anchors.Length;i++)anchors[i]=butterflies[i].localPosition;
            block=new MaterialPropertyBlock();
            // O6 performance A/B: start with wind motion off (the in-game toggle still works).
            if(Array.IndexOf(Environment.GetCommandLineArgs(),"--r07-wind-off")>=0)windRequested=false;
            while(runtime==null||runtime.HUD==null)yield return null;
            var presentation=runtime.GetComponent<FarmPresentationModeR07>();while(!presentation.Ready)yield return null;
            var panel=runtime.transform.Find("FarmHUD/SafeArea/Inspection") as RectTransform;
            foreach(RectTransform child in panel)child.anchoredPosition+=new Vector2(0,55);
            panel.sizeDelta+=new Vector2(0,110);panel.anchoredPosition-=new Vector2(0,55);
            windLabel=presentation.AddButton("WindSetting",panel,"风动：开",new Vector2(-140,-144),()=>{windRequested=!windRequested;ApplyOptions();},250).GetComponentInChildren<Text>();
            soundLabel=presentation.AddButton("SoundSetting",panel,"环境声：开",new Vector2(-140,-199),()=>{soundEnabled=!soundEnabled;ApplyOptions();},250).GetComponentInChildren<Text>();
            Shader.SetGlobalFloat("_FarmR07MotionEnabled",1);birds?.Play();water?.Play();ApplyOptions();
        }
        public void ApplyOptions()
        {
            if(runtime==null)return;quality=runtime.QualityLabel;bool wind=windRequested&&quality!="手机";
            Shader.SetGlobalFloat("_FarmR07WindEnabled",wind?1:0);
            if(windLabel!=null)windLabel.text=quality=="手机"?"风动：手机档关闭":"风动："+(wind?"开":"关");
            if(soundLabel!=null)soundLabel.text="环境声："+(soundEnabled?"开":"关");
            if(birds!=null)birds.mute=!soundEnabled;if(water!=null)water.mute=!soundEnabled;
            runtime.Diagnostics?.RecordEvent("r07_ambient_wind_"+wind+"_sound_"+soundEnabled);
        }
        void Update()
        {
            if(anchors==null)return;
            if(runtime!=null&&runtime.QualityLabel!=quality)ApplyOptions();
            if(runtime!=null&&runtime.Input!=null&&runtime.Input.Paused){if(birds!=null)birds.Pause();if(water!=null)water.Pause();return;}
            if(birds!=null&&!birds.isPlaying)birds.UnPause();if(water!=null&&!water.isPlaying)water.UnPause();
            time+=Time.deltaTime;Shader.SetGlobalFloat("_FarmR07Time",time);
            for(int i=0;i<butterflies.Length;i++){
                var b=butterflies[i];float t=time+i*1.79f;
                b.localPosition=anchors[i]+new Vector3(Mathf.Sin(t*.73f)*.28f,.08f*Mathf.Sin(t*1.37f),Mathf.Cos(t*.9f)*.22f);
                b.localRotation=Quaternion.Euler(0,Mathf.Sin(t*.7f)*55,8*Mathf.Sin(t));
                b.GetChild(0).localRotation=Quaternion.Euler(0,0,35+45*Mathf.Sin(t*19));
                b.GetChild(1).localRotation=Quaternion.Euler(0,0,-35-45*Mathf.Sin(t*19));
            }
            for(int i=0;i<ripples.Length;i++){
                float cycle=(time+i*3.71f)%11,progress=cycle/3.8f;bool visible=progress<1;var r=ripples[i];r.enabled=visible;
                if(!visible)continue;r.transform.localScale=Vector3.one*Mathf.Lerp(.16f,.65f,progress);
                block.Clear();block.SetColor("_BaseColor",new Color(.76f,.95f,1,.18f*Mathf.Sin(progress*Mathf.PI)));r.SetPropertyBlock(block);
            }
        }
        void OnDisable(){Shader.SetGlobalFloat("_FarmR07WindEnabled",0);Shader.SetGlobalFloat("_FarmR07MotionEnabled",0);Shader.SetGlobalFloat("_FarmR07Time",0);}
    }
}
