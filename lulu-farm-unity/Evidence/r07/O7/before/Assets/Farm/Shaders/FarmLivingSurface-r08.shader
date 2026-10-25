Shader "LuluFarm/LivingSurface-r08"
{
 Properties {
  _BaseMap("Existing base texture",2D)="white"{} _BaseColor("Existing base factor",Color)=(1,1,1,1)
  _NormalMap("Existing RGB normal",2D)="bump"{} _NormalScale("Normal scale",Float)=0
  _Smoothness("Existing smoothness",Range(0,1))=.1 _SpecularFactor("Existing specular factor",Range(0,1))=.4
  _MotionMode("1 foliage, 2 animal",Float)=1 _WindStart("Rigid trunk height",Float)=1.15 _WindTop("Crown height",Float)=3.2 _Amplitude("World displacement",Float)=.025
  _HeadPivot("Local neck pivot",Vector)=(0,.05,.25,0) _HeadLimits("Z blend and Y blend",Vector)=(.05,.5,-.15,.15)
  _FloorY("Local feet",Float)=-.95 _Phase("Per animal phase",Float)=0 _Cull("Cull",Float)=0
  _BreathAmp("Animal breath amplitude",Float)=.003 _TurnAmp("Animal head turn radians",Float)=.035
 }
 SubShader {
  Tags {"RenderPipeline"="UniversalPipeline" "RenderType"="Opaque" "Queue"="Geometry"}
  HLSLINCLUDE
  #define _SPECULAR_SETUP 1
  #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
  #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"
  CBUFFER_START(UnityPerMaterial)
  float4 _BaseMap_ST,_BaseColor,_HeadPivot,_HeadLimits;
  float _NormalScale,_Smoothness,_SpecularFactor,_MotionMode,_WindStart,_WindTop,_Amplitude,_FloorY,_Phase,_Cull,_BreathAmp,_TurnAmp;
  CBUFFER_END
  float _FarmR07WindEnabled,_FarmR07MotionEnabled,_FarmR07Time;
  TEXTURE2D(_BaseMap);SAMPLER(sampler_BaseMap);TEXTURE2D(_NormalMap);SAMPLER(sampler_NormalMap);
  struct A {float4 positionOS:POSITION;float3 normalOS:NORMAL;float4 tangentOS:TANGENT;float2 uv:TEXCOORD0;};
  struct V {float4 positionCS:SV_POSITION;float3 positionWS:TEXCOORD0;half3 normalWS:TEXCOORD1;half4 tangentWS:TEXCOORD2;float2 uv:TEXCOORD3;};
  void Deform(inout float3 p,inout float3 n,inout float3 tangent) {
   if(_FarmR07MotionEnabled<.5)return;
   float t=_FarmR07Time;
   if(_MotionMode<1.5){
    float3 ws=TransformObjectToWorld(p);float w=smoothstep(_WindStart,_WindTop,ws.y)*_FarmR07WindEnabled;
    float wave=sin(t*1.35+ws.x*.39+ws.z*.27)+.35*sin(t*2.2+ws.z*.7);
    ws.xz+=float2(1,.36)*(_Amplitude*w*wave);p=TransformWorldToObject(ws);
   }else{
    float breath=sin(t*1.7+_Phase)*_BreathAmp;
    float upper=smoothstep(_FloorY+.12,_FloorY+.5,p.y);
    p.y+=(p.y-_FloorY)*breath*upper;p.x*=1+breath*.55*upper;
    // A small, smooth local neck bend; no skeleton, path finding or source-mesh edit.
    float cycle=frac((t+_Phase*2)/13);float envelope=smoothstep(.58,.70,cycle)*(1-smoothstep(.84,.96,cycle));
    float w=smoothstep(_HeadLimits.x,_HeadLimits.y,p.z)*smoothstep(_HeadLimits.z,_HeadLimits.w,p.y);
    float angle=_TurnAmp*sin((cycle-.58)*16)*envelope*w;float c=cos(angle),s=sin(angle);
    float3 q=p-_HeadPivot.xyz;q.xz=float2(c*q.x+s*q.z,-s*q.x+c*q.z);p=q+_HeadPivot.xyz;
    n.xz=float2(c*n.x+s*n.z,-s*n.x+c*n.z);tangent.xz=float2(c*tangent.x+s*tangent.z,-s*tangent.x+c*tangent.z);
   }
  }
  V Vertex(A a){V v;float3 p=a.positionOS.xyz,n=a.normalOS,t=a.tangentOS.xyz;Deform(p,n,t);
   v.positionWS=TransformObjectToWorld(p);v.positionCS=TransformWorldToHClip(v.positionWS);v.normalWS=TransformObjectToWorldNormal(n);
   v.tangentWS=half4(TransformObjectToWorldDir(t),a.tangentOS.w*GetOddNegativeScale());v.uv=TRANSFORM_TEX(a.uv,_BaseMap);return v;}
  ENDHLSL
  Pass {
   Name "ForwardLit" Tags {"LightMode"="UniversalForward"} Cull [_Cull] ZWrite On
   HLSLPROGRAM
   #pragma target 3.0
   #pragma vertex Vertex
   #pragma fragment Fragment
   #pragma multi_compile_fog
   #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
   #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
   #pragma multi_compile_fragment _ _SCREEN_SPACE_OCCLUSION
   half4 Fragment(V v, FRONT_FACE_TYPE facing:FRONT_FACE_SEMANTIC):SV_Target {
    half3 normal=normalize(v.normalWS);half3 map=SAMPLE_TEXTURE2D(_NormalMap,sampler_NormalMap,v.uv).xyz*2-1;
    map.xy*=_NormalScale;map.z=sqrt(1-saturate(dot(map.xy,map.xy)));
    half3 bitangent=cross(normal,v.tangentWS.xyz)*v.tangentWS.w;
    if(_NormalScale>0)normal=normalize(map.x*v.tangentWS.xyz+map.y*bitangent+map.z*normal);
    normal*=IS_FRONT_VFACE(facing,1,-1);
    InputData data=(InputData)0;data.positionWS=v.positionWS;data.normalWS=normal;data.viewDirectionWS=GetWorldSpaceNormalizeViewDir(v.positionWS);
    data.shadowCoord=TransformWorldToShadowCoord(v.positionWS);data.bakedGI=SampleSH(normal);data.normalizedScreenSpaceUV=GetNormalizedScreenSpaceUV(v.positionCS);data.shadowMask=half4(1,1,1,1);
    SurfaceData surface=(SurfaceData)0;surface.albedo=SAMPLE_TEXTURE2D(_BaseMap,sampler_BaseMap,v.uv).rgb*_BaseColor.rgb;surface.alpha=1;surface.occlusion=1;
    surface.smoothness=_Smoothness;surface.normalTS=half3(0,0,1);surface.specular=half3(.04,.04,.04)*_SpecularFactor;
    half4 result=UniversalFragmentPBR(data,surface);result.rgb=MixFog(result.rgb,ComputeFogFactor(TransformWorldToHClip(v.positionWS).z));return result;
   }
   ENDHLSL
  }
  Pass {Name "DepthOnly" Tags {"LightMode"="DepthOnly"} Cull [_Cull] ZWrite On ColorMask R
   HLSLPROGRAM
   #pragma vertex Vertex
   #pragma fragment DepthFragment
   half4 DepthFragment(V v):SV_Target{return v.positionCS.z;}
   ENDHLSL
  }
  Pass {Name "ShadowCaster" Tags {"LightMode"="ShadowCaster"} Cull [_Cull] ZWrite On ColorMask 0
   HLSLPROGRAM
   #pragma vertex ShadowVertex
   #pragma fragment ShadowFragment
   float3 _LightDirection;
   V ShadowVertex(A a){V v=Vertex(a);v.positionCS=TransformWorldToHClip(ApplyShadowBias(v.positionWS,v.normalWS,_LightDirection));return v;}
   half4 ShadowFragment(V v):SV_Target{return 0;}
   ENDHLSL
  }
  Pass {Name "DepthNormals" Tags {"LightMode"="DepthNormals"} Cull [_Cull] ZWrite On
   HLSLPROGRAM
   #pragma vertex Vertex
   #pragma fragment NormalFragment
   half4 NormalFragment(V v):SV_Target{return half4(normalize(v.normalWS),0);}
   ENDHLSL
  }
 }
}
